use std::collections::{BTreeMap, HashMap, HashSet};
use std::fs;
use std::io::{BufRead, BufReader};
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use anyhow::{Context, Result};
use regex::Regex;
use serde::Deserialize;
use serde_json::Value;

use crate::git::inspect_repo;
use crate::model::{
    AgentView, ComplianceCheck, DashboardSnapshot, ReviewFinding, ReviewSummary, SessionMetrics,
    SessionView, TimelineItem, TokenUsage,
};

const DASHBOARD_VERSION: &str = "0.1.0";
const MANIFEST_NAME: &str = "manifest.json";
const TRACE_NAME: &str = "trace.jsonl";
const STATE_NAME: &str = "state.json";

#[derive(Debug, Clone)]
pub struct SnapshotOptions {
    pub trace_root: PathBuf,
    pub repo: Option<PathBuf>,
    pub max_sessions: usize,
}

#[derive(Debug, Default)]
pub struct SnapshotCache {
    bundles: HashMap<PathBuf, CachedBundle>,
}

#[derive(Debug, Clone)]
struct CachedBundle {
    stamp: BundleStamp,
    session: SessionView,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct BundleStamp {
    manifest_len: u64,
    manifest_modified_ms: u128,
    trace_len: u64,
    trace_modified_ms: u128,
}

#[derive(Debug, Deserialize)]
struct Manifest {
    #[serde(default)]
    trace_id: String,
    #[serde(default)]
    rollout_id: String,
    #[serde(default)]
    root_thread_id: String,
    #[serde(default)]
    started_at_unix_ms: i64,
    #[serde(default)]
    raw_event_log: String,
    #[serde(default)]
    payloads_dir: String,
}

#[derive(Debug, Clone, Default)]
struct AgentAccumulator {
    thread_id: String,
    agent_path: String,
    nickname: Option<String>,
    parent_thread_id: Option<String>,
    task_name: Option<String>,
    agent_role: Option<String>,
    kind: String,
    status: String,
    model: Option<String>,
    reasoning_effort: Option<String>,
    fork_turns: Option<String>,
    started_at_unix_ms: i64,
    ended_at_unix_ms: Option<i64>,
    turns: u64,
    inference_calls: u64,
    review_rounds: u64,
    compactions: u64,
    tokens: TokenUsage,
    result_preview: Option<String>,
    delegated_message: Option<String>,
    response_texts: Vec<String>,
    write_activity_detected: bool,
}

#[derive(Debug, Clone, Default)]
struct SpawnMeta {
    parent_thread_id: Option<String>,
    target_agent_path: Option<String>,
    task_name: Option<String>,
    agent_role: Option<String>,
    model: Option<String>,
    reasoning_effort: Option<String>,
    fork_turns: Option<String>,
    message: Option<String>,
}

#[derive(Debug, Clone, Default)]
struct InferenceAccumulator {
    thread_id: String,
}

#[derive(Debug, Clone, Default)]
struct SessionAccumulator {
    status: String,
    started_at_unix_ms: i64,
    ended_at_unix_ms: Option<i64>,
    agents: BTreeMap<String, AgentAccumulator>,
    pending_spawns: HashMap<String, SpawnMeta>,
    spawns: Vec<SpawnMeta>,
    inferences: HashMap<String, InferenceAccumulator>,
    tool_calls: u64,
    warnings: Vec<String>,
}

pub fn build_snapshot(options: &SnapshotOptions) -> DashboardSnapshot {
    let mut cache = SnapshotCache::default();
    build_snapshot_cached(options, &mut cache)
}

pub fn build_snapshot_cached(
    options: &SnapshotOptions,
    cache: &mut SnapshotCache,
) -> DashboardSnapshot {
    let now = now_ms();
    let git = inspect_repo(options.repo.as_deref());
    let mut warnings = Vec::new();
    let mut sessions = Vec::new();
    let mut seen = HashSet::new();

    if !options.trace_root.exists() {
        warnings.push(format!(
            "Trace root does not exist yet: {}. Start Codex with CODEX_ROLLOUT_TRACE_ROOT set to this path.",
            options.trace_root.display()
        ));
    } else {
        let mut bundles = discover_bundles(&options.trace_root, 7);
        bundles.sort_by_key(|path| bundle_started_at(path).unwrap_or(0));
        bundles.reverse();
        bundles.truncate(options.max_sessions.max(1));

        for bundle in bundles {
            seen.insert(bundle.clone());
            let stamp = bundle_stamp(&bundle);
            let cached = stamp.and_then(|stamp| {
                cache
                    .bundles
                    .get(&bundle)
                    .filter(|entry| entry.stamp == stamp)
                    .map(|entry| entry.session.clone())
            });
            let result = if let Some(mut session) = cached {
                refresh_session_clock(&mut session, now);
                Ok(session)
            } else {
                parse_bundle(&bundle, now).map(|session| {
                    if let Some(stamp) = stamp {
                        cache.bundles.insert(
                            bundle.clone(),
                            CachedBundle {
                                stamp,
                                session: session.clone(),
                            },
                        );
                    }
                    session
                })
            };
            match result {
                Ok(session) => sessions.push(session),
                Err(error) => warnings.push(format!("{}: {error:#}", bundle.display())),
            }
        }

        cache.bundles.retain(|path, _| seen.contains(path));

        if sessions.is_empty() {
            warnings.push(format!(
                "No rollout trace bundles were found under {}.",
                options.trace_root.display()
            ));
        }
    }

    DashboardSnapshot {
        dashboard_version: DASHBOARD_VERSION,
        generated_at_unix_ms: now,
        trace_root: options.trace_root.display().to_string(),
        repo: git.root.clone().or_else(|| {
            options
                .repo
                .as_ref()
                .map(|path| path.display().to_string())
        }),
        live: true,
        git,
        warnings,
        sessions,
    }
}

fn bundle_stamp(bundle: &Path) -> Option<BundleStamp> {
    fn meta(path: &Path) -> Option<(u64, u128)> {
        let metadata = fs::metadata(path).ok()?;
        let modified = metadata
            .modified()
            .ok()?
            .duration_since(UNIX_EPOCH)
            .ok()?
            .as_millis();
        Some((metadata.len(), modified))
    }
    let trace = bundle_trace_path(bundle)?;
    let (manifest_len, manifest_modified_ms) = meta(&bundle.join(MANIFEST_NAME))?;
    let (trace_len, trace_modified_ms) = meta(&trace)?;
    Some(BundleStamp {
        manifest_len,
        manifest_modified_ms,
        trace_len,
        trace_modified_ms,
    })
}

fn refresh_session_clock(session: &mut SessionView, now: i64) {
    if session.ended_at_unix_ms.is_none() {
        session.duration_ms = now.saturating_sub(session.started_at_unix_ms).max(0);
    }
    for agent in &mut session.agents {
        if agent.ended_at_unix_ms.is_none() {
            agent.duration_ms = now.saturating_sub(agent.started_at_unix_ms).max(0);
        }
    }
}

fn discover_bundles(root: &Path, max_depth: usize) -> Vec<PathBuf> {
    fn walk(path: &Path, depth: usize, max_depth: usize, output: &mut Vec<PathBuf>) {
        if depth > max_depth {
            return;
        }
        if path.join(MANIFEST_NAME).is_file() && bundle_trace_path(path).is_some_and(|p| p.is_file()) {
            output.push(path.to_path_buf());
            return;
        }
        let entries = match fs::read_dir(path) {
            Ok(entries) => entries,
            Err(_) => return,
        };
        for entry in entries.flatten() {
            let child = entry.path();
            if !child.is_dir() {
                continue;
            }
            if child.file_name().and_then(|name| name.to_str()) == Some("payloads") {
                continue;
            }
            walk(&child, depth + 1, max_depth, output);
        }
    }

    let mut output = Vec::new();
    walk(root, 0, max_depth, &mut output);
    output
}


fn bundle_trace_path(bundle: &Path) -> Option<PathBuf> {
    let manifest_path = bundle.join(MANIFEST_NAME);
    let manifest_text = fs::read_to_string(manifest_path).ok()?;
    let manifest: Manifest = serde_json::from_str(&manifest_text).ok()?;
    let relative = if manifest.raw_event_log.trim().is_empty() {
        PathBuf::from(TRACE_NAME)
    } else {
        PathBuf::from(manifest.raw_event_log)
    };
    if relative.is_absolute()
        || relative
            .components()
            .any(|part| matches!(part, std::path::Component::ParentDir))
    {
        return None;
    }
    Some(bundle.join(relative))
}

fn bundle_started_at(bundle: &Path) -> Option<i64> {
    let text = fs::read_to_string(bundle.join(MANIFEST_NAME)).ok()?;
    let manifest: Manifest = serde_json::from_str(&text).ok()?;
    Some(manifest.started_at_unix_ms)
}

fn parse_bundle(bundle: &Path, now: i64) -> Result<SessionView> {
    let manifest_text = fs::read_to_string(bundle.join(MANIFEST_NAME))
        .with_context(|| format!("failed to read {MANIFEST_NAME}"))?;
    let manifest: Manifest = serde_json::from_str(&manifest_text)
        .with_context(|| format!("failed to parse {MANIFEST_NAME}"))?;
    if !manifest.payloads_dir.trim().is_empty() {
        let payloads_dir = PathBuf::from(&manifest.payloads_dir);
        if payloads_dir.is_absolute()
            || payloads_dir
                .components()
                .any(|part| matches!(part, std::path::Component::ParentDir))
        {
            anyhow::bail!("manifest payloads_dir is not bundle-relative");
        }
    }

    let trace_path = if manifest.raw_event_log.trim().is_empty() {
        bundle.join(TRACE_NAME)
    } else {
        let relative = PathBuf::from(&manifest.raw_event_log);
        if relative.is_absolute()
            || relative
                .components()
                .any(|part| matches!(part, std::path::Component::ParentDir))
        {
            anyhow::bail!("manifest raw_event_log is not bundle-relative");
        }
        bundle.join(relative)
    };
    let file = fs::File::open(&trace_path)
        .with_context(|| format!("failed to open {}", trace_path.display()))?;
    let reader = BufReader::new(file);
    let mut state = SessionAccumulator {
        status: "running".to_owned(),
        started_at_unix_ms: manifest.started_at_unix_ms,
        ..SessionAccumulator::default()
    };

    state.agents.insert(
        manifest.root_thread_id.clone(),
        AgentAccumulator {
            thread_id: manifest.root_thread_id.clone(),
            agent_path: "/root".to_owned(),
            kind: "main".to_owned(),
            status: "running".to_owned(),
            started_at_unix_ms: manifest.started_at_unix_ms,
            ..AgentAccumulator::default()
        },
    );

    for (line_number, line) in reader.lines().enumerate() {
        let line = match line {
            Ok(line) if !line.trim().is_empty() => line,
            Ok(_) => continue,
            Err(error) => {
                state.warnings.push(format!(
                    "trace line {} could not be read: {error}",
                    line_number + 1
                ));
                continue;
            }
        };
        let event: Value = match serde_json::from_str(&line) {
            Ok(event) => event,
            Err(error) => {
                state.warnings.push(format!(
                    "trace line {} is incomplete or invalid JSON: {error}",
                    line_number + 1
                ));
                continue;
            }
        };
        process_event(bundle, &manifest, &mut state, &event);
    }

    if !state.pending_spawns.is_empty() {
        state.spawns.extend(state.pending_spawns.drain().map(|(_, meta)| meta));
    }

    if bundle.join(STATE_NAME).is_file() {
        if let Err(error) = enrich_from_reduced_state(bundle, &mut state) {
            state
                .warnings
                .push(format!("state.json enrichment was skipped: {error:#}"));
        }
    }

    apply_spawn_metadata(&mut state);
    classify_agents(&mut state, &manifest.root_thread_id);

    let mut agents: Vec<AgentView> = state
        .agents
        .values()
        .cloned()
        .map(|agent| finalize_agent(agent, now))
        .collect();
    agents.sort_by_key(|agent| {
        (
            match agent.kind.as_str() {
                "main" => 0,
                "worker" => 1,
                "reviewer" => 2,
                _ => 3,
            },
            agent.started_at_unix_ms,
        )
    });

    let review = build_review_summary(&agents, &state.agents);
    let metrics = build_metrics(&agents, state.tool_calls, now);
    let compliance = build_compliance(&agents, &metrics, &review);
    let timeline = agents
        .iter()
        .map(|agent| TimelineItem {
            thread_id: agent.thread_id.clone(),
            label: agent
                .task_name
                .clone()
                .or_else(|| agent.nickname.clone())
                .unwrap_or_else(|| match agent.kind.as_str() {
                    "main" => "Main Sol".to_owned(),
                    "reviewer" => "Sol review".to_owned(),
                    _ => agent.agent_path.clone(),
                }),
            kind: agent.kind.clone(),
            status: agent.status.clone(),
            started_at_unix_ms: agent.started_at_unix_ms,
            ended_at_unix_ms: agent.ended_at_unix_ms,
        })
        .collect();

    let ended = state.ended_at_unix_ms;
    let duration_end = ended.unwrap_or(now);
    let trace_id = if manifest.trace_id.is_empty() {
        bundle
            .file_name()
            .and_then(|value| value.to_str())
            .unwrap_or("trace")
            .to_owned()
    } else {
        manifest.trace_id.clone()
    };
    let rollout_id = if manifest.rollout_id.is_empty() {
        trace_id.clone()
    } else {
        manifest.rollout_id.clone()
    };

    Ok(SessionView {
        id: trace_id.clone(),
        bundle_path: bundle.display().to_string(),
        trace_id,
        rollout_id,
        status: state.status,
        started_at_unix_ms: state.started_at_unix_ms,
        ended_at_unix_ms: ended,
        duration_ms: duration_end.saturating_sub(state.started_at_unix_ms),
        root_thread_id: manifest.root_thread_id,
        agents,
        timeline,
        metrics,
        review,
        compliance,
        warnings: state.warnings,
    })
}

fn process_event(bundle: &Path, manifest: &Manifest, state: &mut SessionAccumulator, event: &Value) {
    let wall_time = event
        .get("wall_time_unix_ms")
        .and_then(Value::as_i64)
        .unwrap_or(manifest.started_at_unix_ms);
    let envelope_thread = event
        .get("thread_id")
        .and_then(Value::as_str)
        .map(str::to_owned);
    let payload = match event.get("payload") {
        Some(payload) => payload,
        None => return,
    };
    let event_type = payload
        .get("type")
        .and_then(Value::as_str)
        .unwrap_or_default();

    match event_type {
        "rollout_started" => {
            state.status = "running".to_owned();
            if state.started_at_unix_ms == 0 {
                state.started_at_unix_ms = wall_time;
            }
        }
        "rollout_ended" => {
            state.status = string_field(payload, "status").unwrap_or_else(|| "completed".to_owned());
            state.ended_at_unix_ms = Some(wall_time);
        }
        "thread_started" => {
            let thread_id = string_field(payload, "thread_id")
                .or(envelope_thread)
                .unwrap_or_else(|| format!("unknown-{wall_time}"));
            let path = string_field(payload, "agent_path").unwrap_or_else(|| {
                if thread_id == manifest.root_thread_id {
                    "/root".to_owned()
                } else {
                    format!("/root/{}", short_id(&thread_id))
                }
            });
            let agent = state
                .agents
                .entry(thread_id.clone())
                .or_insert_with(|| AgentAccumulator {
                    thread_id: thread_id.clone(),
                    ..AgentAccumulator::default()
                });
            agent.agent_path = path;
            agent.status = "running".to_owned();
            if agent.started_at_unix_ms == 0 {
                agent.started_at_unix_ms = wall_time;
            }
            if let Some(metadata) = load_payload_ref(bundle, payload.get("metadata_payload")) {
                enrich_agent_from_value(agent, &metadata);
            }
        }
        "thread_ended" => {
            let thread_id = string_field(payload, "thread_id")
                .or(envelope_thread)
                .unwrap_or_default();
            if let Some(agent) = state.agents.get_mut(&thread_id) {
                agent.status = string_field(payload, "status").unwrap_or_else(|| "completed".to_owned());
                agent.ended_at_unix_ms = Some(wall_time);
            }
        }
        "codex_turn_started" => {
            let thread_id = string_field(payload, "thread_id")
                .or(envelope_thread)
                .unwrap_or_default();
            ensure_agent(state, &thread_id, wall_time).turns += 1;
        }
        "inference_started" => {
            let inference_id = string_field(payload, "inference_call_id").unwrap_or_default();
            let thread_id = string_field(payload, "thread_id")
                .or(envelope_thread)
                .unwrap_or_default();
            let model = string_field(payload, "model");
            let agent = ensure_agent(state, &thread_id, wall_time);
            if model.is_some() {
                agent.model = model;
            }
            agent.inference_calls += 1;
            state
                .inferences
                .insert(inference_id, InferenceAccumulator { thread_id });
        }
        "inference_completed" => {
            let inference_id = string_field(payload, "inference_call_id").unwrap_or_default();
            let thread_id = state
                .inferences
                .get(&inference_id)
                .map(|value| value.thread_id.clone())
                .or(envelope_thread)
                .unwrap_or_default();
            if let Some(response) = load_payload_ref(bundle, payload.get("response_payload")) {
                let usage = find_token_usage(&response).unwrap_or_default();
                let texts = extract_model_output_texts(&response);
                let agent = ensure_agent(state, &thread_id, wall_time);
                agent.tokens.add_assign(usage);
                for text in texts {
                    push_unique_text(&mut agent.response_texts, text);
                }
            }
        }
        "compaction_installed" => {
            if let Some(thread_id) = envelope_thread {
                ensure_agent(state, &thread_id, wall_time).compactions += 1;
            }
        }
        "tool_call_started" => {
            state.tool_calls += 1;
            let tool_call_id = string_field(payload, "tool_call_id").unwrap_or_default();
            let kind = payload
                .get("kind")
                .and_then(type_name)
                .unwrap_or_else(|| "other".to_owned());
            let summary = payload.get("summary");
            let invocation = load_payload_ref(bundle, payload.get("invocation_payload"));
            let thread_id = envelope_thread.clone();

            let target_path = summary
                .and_then(|value| string_field(value, "target_agent_path"))
                .or_else(|| {
                    invocation.as_ref().and_then(|value| {
                        recursive_string(
                            value,
                            &["target_agent_path", "agent_path", "recipient", "target"],
                        )
                    })
                });
            let task_name = summary
                .and_then(|value| string_field(value, "task_name"))
                .or_else(|| {
                    invocation
                        .as_ref()
                        .and_then(|value| recursive_string(value, &["task_name"]))
                });
            let message_preview = summary
                .and_then(|value| string_field(value, "message_preview"))
                .or_else(|| {
                    invocation.as_ref().and_then(|value| {
                        recursive_string(value, &["message", "task", "prompt", "input"])
                    })
                });

            if kind == "spawn_agent" {
                let mut meta = SpawnMeta {
                    parent_thread_id: thread_id.clone(),
                    target_agent_path: target_path.clone(),
                    task_name: task_name.clone(),
                    message: message_preview.clone(),
                    ..SpawnMeta::default()
                };
                if let Some(value) = invocation.as_ref() {
                    meta.model = recursive_string(value, &["model"]);
                    meta.reasoning_effort = recursive_string(
                        value,
                        &["reasoning_effort", "model_reasoning_effort"],
                    );
                    meta.fork_turns = recursive_string(value, &["fork_turns"]);
                    meta.agent_role = recursive_string(
                        value,
                        &["agent_role", "agent_type", "role"],
                    );
                    meta.message = recursive_string(value, &["message", "task", "prompt", "input"])
                        .or(meta.message);
                    meta.task_name = recursive_string(value, &["task_name"]).or(meta.task_name);
                }
                if tool_call_id.is_empty() {
                    state.spawns.push(meta);
                } else {
                    state.pending_spawns.insert(tool_call_id, meta);
                }
            }

            if matches!(
                kind.as_str(),
                "followup_task" | "assign_agent_task" | "send_message"
            ) {
                if let Some(path) = target_path.as_ref() {
                    if looks_like_review_assignment(
                        task_name.as_deref(),
                        message_preview.as_deref(),
                    ) {
                        if let Some(agent) = find_agent_by_path_mut(&mut state.agents, path) {
                            agent.review_rounds += 1;
                        }
                    }
                }
            }

            if let Some(thread_id) = thread_id.as_ref() {
                if kind == "apply_patch"
                    || invocation.as_ref().is_some_and(looks_like_write_command)
                {
                    ensure_agent(state, thread_id, wall_time).write_activity_detected = true;
                }
            }
        }
        "tool_call_ended" => {
            let tool_call_id = string_field(payload, "tool_call_id").unwrap_or_default();
            let Some(mut meta) = state.pending_spawns.remove(&tool_call_id) else {
                return;
            };
            if let Some(result) = load_payload_ref(bundle, payload.get("result_payload")) {
                meta.target_agent_path = recursive_string(
                    &result,
                    &["target_agent_path", "agent_path", "task_name"],
                )
                .filter(|value| value.starts_with('/'))
                .or(meta.target_agent_path);
                meta.task_name = recursive_string(&result, &["task_name"])
                    .filter(|value| !value.starts_with('/'))
                    .or(meta.task_name);
            }
            state.spawns.push(meta);
        }
        "agent_result_observed" => {
            let child_thread_id = string_field(payload, "child_thread_id").unwrap_or_default();
            let message = string_field(payload, "message").unwrap_or_default();
            let agent = ensure_agent(state, &child_thread_id, wall_time);
            if !message.is_empty() {
                agent.result_preview = Some(truncate(&message, 320));
                push_unique_text(&mut agent.response_texts, message);
            }
        }
        _ => {}
    }
}

fn enrich_from_reduced_state(bundle: &Path, state: &mut SessionAccumulator) -> Result<()> {
    let session_start = state.started_at_unix_ms;
    let text = fs::read_to_string(bundle.join(STATE_NAME))?;
    let root: Value = serde_json::from_str(&text)?;

    if let Some(status) = root.get("status").and_then(Value::as_str) {
        state.status = status.to_owned();
    }
    if let Some(ended) = root.get("ended_at_unix_ms").and_then(Value::as_i64) {
        state.ended_at_unix_ms = Some(ended);
    }

    if let Some(threads) = root.get("threads").and_then(Value::as_object) {
        for (thread_id, thread) in threads {
            let started = thread
                .pointer("/execution/started_at_unix_ms")
                .and_then(Value::as_i64)
                .unwrap_or(session_start);
            let agent = ensure_agent(state, thread_id, started);
            if let Some(path) = thread.get("agent_path").and_then(Value::as_str) {
                agent.agent_path = path.to_owned();
            }
            if let Some(nickname) = thread.get("nickname").and_then(Value::as_str) {
                agent.nickname = Some(nickname.to_owned());
            }
            if let Some(model) = thread.get("default_model").and_then(Value::as_str) {
                if agent.model.is_none() {
                    agent.model = Some(model.to_owned());
                }
            }
            if let Some(status) = thread.pointer("/execution/status").and_then(Value::as_str) {
                agent.status = status.to_owned();
            }
            if let Some(ended) = thread
                .pointer("/execution/ended_at_unix_ms")
                .and_then(Value::as_i64)
            {
                agent.ended_at_unix_ms = Some(ended);
            }
            if let Some(origin) = thread.get("origin") {
                let origin_type = origin.get("type").and_then(Value::as_str).unwrap_or_default();
                if origin_type == "spawned" {
                    agent.parent_thread_id = string_field(origin, "parent_thread_id");
                    agent.task_name = string_field(origin, "task_name").or(agent.task_name.clone());
                    agent.agent_role = string_field(origin, "agent_role").or(agent.agent_role.clone());
                }
            }
        }
    }

    if let Some(inferences) = root.get("inference_calls").and_then(Value::as_object) {
        for inference in inferences.values() {
            let Some(thread_id) = inference.get("thread_id").and_then(Value::as_str) else {
                continue;
            };
            if let Some(model) = inference.get("model").and_then(Value::as_str) {
                ensure_agent(state, thread_id, session_start).model = Some(model.to_owned());
            }
            if let Some(usage) = inference.get("usage") {
                if let Some(tokens) = token_usage_from_object(usage) {
                    // Raw response parsing is primary. Only use reduced usage when no raw usage was found.
                    let agent = ensure_agent(state, thread_id, session_start);
                    if agent.tokens.total_tokens == 0 {
                        agent.tokens.add_assign(tokens);
                    }
                }
            }
        }
    }

    if let Some(items) = root.get("conversation_items").and_then(Value::as_object) {
        for item in items.values() {
            if item.get("role").and_then(Value::as_str) != Some("assistant") {
                continue;
            }
            let Some(thread_id) = item.get("thread_id").and_then(Value::as_str) else {
                continue;
            };
            if let Some(parts) = item.pointer("/body/parts").and_then(Value::as_array) {
                for part in parts {
                    if let Some(text) = part.get("text").and_then(Value::as_str) {
                        push_unique_text(
                            &mut ensure_agent(state, thread_id, session_start).response_texts,
                            text.to_owned(),
                        );
                    }
                }
            }
        }
    }

    Ok(())
}

fn apply_spawn_metadata(state: &mut SessionAccumulator) {
    let mut unused: Vec<SpawnMeta> = state.spawns.clone();
    let agent_ids: Vec<String> = state.agents.keys().cloned().collect();

    for thread_id in agent_ids {
        let Some(agent) = state.agents.get(&thread_id) else {
            continue;
        };
        if agent.agent_path == "/root" {
            continue;
        }

        let index = unused
            .iter()
            .position(|meta| {
                meta.target_agent_path
                    .as_deref()
                    .is_some_and(|path| path == agent.agent_path)
            })
            .or_else(|| {
                unused.iter().position(|meta| {
                    meta.task_name.as_deref().is_some_and(|task| {
                        agent.task_name.as_deref() == Some(task)
                            || agent
                                .agent_path
                                .rsplit('/')
                                .next()
                                .is_some_and(|segment| segment == task)
                    })
                })
            })
            .or_else(|| {
                let candidates: Vec<usize> = unused
                    .iter()
                    .enumerate()
                    .filter_map(|(index, meta)| {
                        (meta.parent_thread_id == agent.parent_thread_id).then_some(index)
                    })
                    .collect();
                (candidates.len() == 1).then_some(candidates[0])
            });

        let Some(index) = index else {
            continue;
        };
        let meta = unused.remove(index);
        if let Some(agent) = state.agents.get_mut(&thread_id) {
            agent.parent_thread_id = meta.parent_thread_id.or(agent.parent_thread_id.clone());
            agent.task_name = meta.task_name.or(agent.task_name.clone());
            agent.agent_role = meta.agent_role.or(agent.agent_role.clone());
            agent.model = meta.model.or(agent.model.clone());
            agent.reasoning_effort = meta.reasoning_effort.or(agent.reasoning_effort.clone());
            agent.fork_turns = meta.fork_turns.or(agent.fork_turns.clone());
            agent.delegated_message = meta.message.clone().or(agent.delegated_message.clone());
            if agent.review_rounds == 0
                && looks_like_review_assignment(
                    agent.task_name.as_deref(),
                    agent.delegated_message.as_deref(),
                )
            {
                agent.review_rounds = 1;
            }
        }
    }
}

fn classify_agents(state: &mut SessionAccumulator, root_thread_id: &str) {
    for agent in state.agents.values_mut() {
        if agent.thread_id == root_thread_id {
            agent.kind = "main".to_owned();
            continue;
        }

        let explicit_role = agent
            .agent_role
            .as_deref()
            .is_some_and(|role| role.eq_ignore_ascii_case("reviewer"));
        let assignment_review = looks_like_review_assignment(
            agent.task_name.as_deref(),
            agent.delegated_message.as_deref(),
        );

        agent.kind = if explicit_role || assignment_review {
            if agent.review_rounds == 0 {
                agent.review_rounds = 1;
            }
            "reviewer".to_owned()
        } else {
            "worker".to_owned()
        };
    }
}

fn finalize_agent(agent: AgentAccumulator, now: i64) -> AgentView {
    let end = agent.ended_at_unix_ms.unwrap_or(now);
    AgentView {
        thread_id: agent.thread_id,
        agent_path: if agent.agent_path.is_empty() {
            "/root/unknown".to_owned()
        } else {
            agent.agent_path
        },
        nickname: agent.nickname,
        parent_thread_id: agent.parent_thread_id,
        task_name: agent.task_name,
        agent_role: agent.agent_role,
        kind: if agent.kind.is_empty() {
            "worker".to_owned()
        } else {
            agent.kind
        },
        status: if agent.status.is_empty() {
            "running".to_owned()
        } else {
            agent.status
        },
        model: agent.model,
        reasoning_effort: agent.reasoning_effort,
        fork_turns: agent.fork_turns,
        started_at_unix_ms: agent.started_at_unix_ms,
        ended_at_unix_ms: agent.ended_at_unix_ms,
        duration_ms: end.saturating_sub(agent.started_at_unix_ms),
        turns: agent.turns,
        inference_calls: agent.inference_calls,
        review_rounds: agent.review_rounds,
        compactions: agent.compactions,
        tokens: agent.tokens.normalized(),
        result_preview: agent.result_preview,
        write_activity_detected: agent.write_activity_detected,
    }
}

fn build_metrics(agents: &[AgentView], tool_calls: u64, now: i64) -> SessionMetrics {
    let mut metrics = SessionMetrics {
        agent_count: agents.len(),
        worker_count: agents.iter().filter(|agent| agent.kind == "worker").count(),
        reviewer_count: agents
            .iter()
            .filter(|agent| agent.kind == "reviewer")
            .count(),
        tool_calls,
        compactions: agents.iter().map(|agent| agent.compactions).sum(),
        ..SessionMetrics::default()
    };

    for agent in agents {
        metrics.total_tokens = metrics.total_tokens.saturating_add(agent.tokens.total_tokens);
        match agent.kind.as_str() {
            "main" => metrics.main_tokens = metrics.main_tokens.saturating_add(agent.tokens.total_tokens),
            "reviewer" => {
                metrics.reviewer_tokens = metrics
                    .reviewer_tokens
                    .saturating_add(agent.tokens.total_tokens)
            }
            _ => metrics.worker_tokens = metrics.worker_tokens.saturating_add(agent.tokens.total_tokens),
        }
    }
    if metrics.total_tokens > 0 {
        metrics.main_token_share = Some(metrics.main_tokens as f64 / metrics.total_tokens as f64);
    }

    let mut points = Vec::new();
    for agent in agents.iter().filter(|agent| agent.kind == "worker") {
        let start = agent.started_at_unix_ms;
        let end = agent.ended_at_unix_ms.unwrap_or(now).max(start);
        points.push((start, 1i32));
        points.push((end, -1i32));
    }
    points.sort_by_key(|(time, delta)| (*time, *delta));
    let mut active = 0i32;
    let mut peak = 0i32;
    let mut previous = None;
    let mut overlap = 0i64;
    for (time, delta) in points {
        if let Some(previous_time) = previous {
            if active >= 2 {
                overlap = overlap.saturating_add(time.saturating_sub(previous_time));
            }
        }
        active += delta;
        peak = peak.max(active);
        previous = Some(time);
    }
    metrics.peak_worker_concurrency = peak.max(0) as usize;
    metrics.parallel_overlap_ms = overlap;
    metrics
}

fn build_review_summary(
    agents: &[AgentView],
    raw_agents: &BTreeMap<String, AgentAccumulator>,
) -> ReviewSummary {
    let reviewer_ids: Vec<String> = agents
        .iter()
        .filter(|agent| agent.kind == "reviewer")
        .map(|agent| agent.thread_id.clone())
        .collect();
    let rounds = agents
        .iter()
        .filter(|agent| agent.kind == "reviewer")
        .map(|agent| agent.review_rounds.max(1))
        .sum();
    let mut all_text = Vec::new();
    for id in &reviewer_ids {
        if let Some(agent) = raw_agents.get(id) {
            all_text.extend(agent.response_texts.iter().cloned());
            if let Some(result) = agent.result_preview.clone() {
                all_text.push(result);
            }
        }
    }
    let verdict = detect_verdict(&all_text);
    let findings = parse_findings(&reviewer_ids, raw_agents);

    ReviewSummary {
        present: !reviewer_ids.is_empty(),
        reviewer_thread_ids: reviewer_ids,
        rounds,
        verdict,
        findings,
    }
}

fn parse_findings(
    reviewer_ids: &[String],
    agents: &BTreeMap<String, AgentAccumulator>,
) -> Vec<ReviewFinding> {
    let id_re = Regex::new(r"(?i)\b(AX-\d{2,})\b").expect("valid finding regex");
    let severity_re = Regex::new(r"(?i)\b(critical|high|major|medium|moderate|low|minor|nit)\b")
        .expect("valid severity regex");
    let status_re = Regex::new(r"(?i)\b(resolved|fixed|open|accepted|accept|rejected|reject|deferred|defer|escalated|escalate)\b")
        .expect("valid finding status regex");
    let mut findings: BTreeMap<String, ReviewFinding> = BTreeMap::new();

    for reviewer_id in reviewer_ids {
        let Some(agent) = agents.get(reviewer_id) else {
            continue;
        };
        for text in &agent.response_texts {
            for line in text.lines() {
                let Some(capture) = id_re.captures(line) else {
                    continue;
                };
                let id = capture
                    .get(1)
                    .map(|value| value.as_str().to_ascii_uppercase())
                    .unwrap_or_else(|| "AX-?".to_owned());
                let severity = severity_re
                    .captures(line)
                    .and_then(|value| value.get(1))
                    .map(|value| value.as_str().to_ascii_lowercase());
                let status = status_re
                    .captures(line)
                    .and_then(|value| value.get(1))
                    .map(|value| normalize_finding_status(value.as_str()))
                    .unwrap_or_else(|| "open".to_owned());
                findings.insert(
                    id.clone(),
                    ReviewFinding {
                        id,
                        severity,
                        status,
                        title: truncate(line.trim(), 220),
                        source_thread_id: reviewer_id.clone(),
                    },
                );
            }
        }
    }
    findings.into_values().collect()
}

fn detect_verdict(texts: &[String]) -> Option<String> {
    const VERDICTS: [(&str, &str); 7] = [
        ("FIX_FIRST", "FIX_FIRST"),
        ("FIX FIRST", "FIX_FIRST"),
        ("REQUEST CHANGES", "FIX_FIRST"),
        ("BLOCKED", "BLOCKED"),
        ("SHIP", "SHIP"),
        ("APPROVED", "SHIP"),
        ("APPROVE", "SHIP"),
    ];

    for text in texts.iter().rev() {
        let upper = text.to_ascii_uppercase();
        let mut latest: Option<(usize, &str)> = None;
        for (needle, normalized) in VERDICTS {
            if let Some(index) = upper.rfind(needle) {
                if latest.map_or(true, |(best, _)| index > best) {
                    latest = Some((index, normalized));
                }
            }
        }
        if let Some((_, normalized)) = latest {
            return Some(normalized.to_owned());
        }
    }
    None
}

fn build_compliance(
    agents: &[AgentView],
    metrics: &SessionMetrics,
    review: &ReviewSummary,
) -> Vec<ComplianceCheck> {
    let workers: Vec<&AgentView> = agents.iter().filter(|agent| agent.kind == "worker").collect();
    let reviewers: Vec<&AgentView> = agents
        .iter()
        .filter(|agent| agent.kind == "reviewer")
        .collect();
    let main = agents.iter().find(|agent| agent.kind == "main");
    let mut checks = Vec::new();

    if workers.is_empty() {
        checks.push(check(
            "worker-routing",
            "Worker routing",
            "not_applicable",
            "No bounded worker was observed in this session.",
        ));
    } else {
        let wrong_models = workers
            .iter()
            .filter(|agent| {
                agent
                    .model
                    .as_deref()
                    .is_some_and(|model| !model.to_ascii_lowercase().contains("luna"))
            })
            .count();
        let unknown_models = workers.iter().filter(|agent| agent.model.is_none()).count();
        let wrong_effort = workers
            .iter()
            .filter(|agent| {
                agent.reasoning_effort.as_deref().is_some_and(|effort| {
                    !effort.eq_ignore_ascii_case("max")
                })
            })
            .count();
        let status = if wrong_models > 0 || wrong_effort > 0 {
            "fail"
        } else if unknown_models > 0 || workers.iter().any(|agent| agent.reasoning_effort.is_none()) {
            "unknown"
        } else {
            "pass"
        };
        checks.push(check(
            "worker-routing",
            "Worker routing",
            status,
            format!(
                "{} worker(s); {} non-Luna model(s), {} unknown model(s).",
                workers.len(),
                wrong_models,
                unknown_models
            ),
        ));
    }

    if reviewers.is_empty() {
        checks.push(check(
            "review-independence",
            "Review independence",
            "not_applicable",
            "No delegated reviewer was observed.",
        ));
    } else {
        let non_sol = reviewers
            .iter()
            .filter(|agent| {
                agent
                    .model
                    .as_deref()
                    .is_some_and(|model| !model.to_ascii_lowercase().contains("sol"))
            })
            .count();
        let unknown_models = reviewers.iter().filter(|agent| agent.model.is_none()).count();
        let wrong_effort = reviewers
            .iter()
            .filter(|agent| {
                agent
                    .reasoning_effort
                    .as_deref()
                    .is_some_and(|effort| !effort.eq_ignore_ascii_case("xhigh"))
            })
            .count();
        let unknown_effort = reviewers
            .iter()
            .filter(|agent| agent.reasoning_effort.is_none())
            .count();
        checks.push(check(
            "review-independence",
            "Review independence",
            if non_sol > 0 || wrong_effort > 0 {
                "fail"
            } else if unknown_models > 0 || unknown_effort > 0 {
                "unknown"
            } else {
                "pass"
            },
            format!(
                "{} reviewer thread(s); {} non-Sol, {} non-XHIGH, {} model unknown, {} effort unknown.",
                reviewers.len(),
                non_sol,
                wrong_effort,
                unknown_models,
                unknown_effort
            ),
        ));
    }

    if reviewers.is_empty() || review.rounds <= 1 {
        checks.push(check(
            "review-continuity",
            "Review continuity",
            "not_applicable",
            "No re-review round was observed.",
        ));
    } else {
        checks.push(check(
            "review-continuity",
            "Review continuity",
            if reviewers.len() == 1 { "pass" } else { "fail" },
            if reviewers.len() == 1 {
                format!("{} round(s) used the same reviewer thread.", review.rounds)
            } else {
                format!(
                    "{} round(s) were spread across {} reviewer threads.",
                    review.rounds,
                    reviewers.len()
                )
            },
        ));
    }

    let child_agents: Vec<&AgentView> = agents.iter().filter(|agent| agent.kind != "main").collect();
    if child_agents.is_empty() {
        checks.push(check(
            "context-isolation",
            "Context isolation",
            "not_applicable",
            "No child agent was observed.",
        ));
    } else {
        let inherited = child_agents
            .iter()
            .filter(|agent| {
                agent
                    .fork_turns
                    .as_deref()
                    .is_some_and(|value| !value.eq_ignore_ascii_case("none"))
            })
            .count();
        let unknown = child_agents
            .iter()
            .filter(|agent| agent.fork_turns.is_none())
            .count();
        checks.push(check(
            "context-isolation",
            "Context isolation",
            if inherited > 0 {
                "warn"
            } else if unknown > 0 {
                "unknown"
            } else {
                "pass"
            },
            format!(
                "{} child agent(s); {} inherited turns, {} unknown.",
                child_agents.len(),
                inherited,
                unknown
            ),
        ));
    }

    checks.push(check(
        "parallelism",
        "Parallelism",
        if metrics.worker_count < 2 {
            "not_applicable"
        } else if metrics.peak_worker_concurrency >= 2 {
            "pass"
        } else {
            "warn"
        },
        if metrics.worker_count < 2 {
            "Fewer than two workers were observed.".to_owned()
        } else {
            format!(
                "Peak worker concurrency: {}; observed overlap: {} ms.",
                metrics.peak_worker_concurrency, metrics.parallel_overlap_ms
            )
        },
    ));

    let reviewer_writes = reviewers
        .iter()
        .filter(|agent| agent.write_activity_detected)
        .count();
    checks.push(check(
        "review-read-only",
        "Reviewer read-only behavior",
        if reviewers.is_empty() {
            "not_applicable"
        } else if reviewer_writes > 0 {
            "fail"
        } else {
            "pass"
        },
        if reviewers.is_empty() {
            "No delegated reviewer was observed.".to_owned()
        } else if reviewer_writes > 0 {
            format!("Write-like activity was detected in {reviewer_writes} reviewer thread(s).")
        } else {
            "No apply_patch or obvious write command was observed in reviewer threads.".to_owned()
        },
    ));

    let main_compactions = main.map(|agent| agent.compactions).unwrap_or(0);
    checks.push(check(
        "main-context",
        "Main context",
        if main_compactions == 0 { "pass" } else { "warn" },
        format!("Main compactions observed: {main_compactions}."),
    ));

    checks
}

fn check(key: &str, label: &str, status: &str, detail: impl Into<String>) -> ComplianceCheck {
    ComplianceCheck {
        key: key.to_owned(),
        label: label.to_owned(),
        status: status.to_owned(),
        detail: detail.into(),
    }
}

fn ensure_agent<'a>(
    state: &'a mut SessionAccumulator,
    thread_id: &str,
    started_at: i64,
) -> &'a mut AgentAccumulator {
    state
        .agents
        .entry(thread_id.to_owned())
        .or_insert_with(|| AgentAccumulator {
            thread_id: thread_id.to_owned(),
            agent_path: format!("/root/{}", short_id(thread_id)),
            status: "running".to_owned(),
            started_at_unix_ms: started_at,
            ..AgentAccumulator::default()
        })
}

fn find_agent_by_path_mut<'a>(
    agents: &'a mut BTreeMap<String, AgentAccumulator>,
    path: &str,
) -> Option<&'a mut AgentAccumulator> {
    let thread_id = agents
        .iter()
        .find(|(_, agent)| agent.agent_path == path)
        .map(|(thread_id, _)| thread_id.clone())?;
    agents.get_mut(&thread_id)
}

fn enrich_agent_from_value(agent: &mut AgentAccumulator, value: &Value) {
    agent.model = recursive_string(value, &["model", "default_model"]).or(agent.model.clone());
    agent.reasoning_effort = recursive_string(
        value,
        &["reasoning_effort", "model_reasoning_effort"],
    )
    .or(agent.reasoning_effort.clone());
    agent.fork_turns = recursive_string(value, &["fork_turns"]).or(agent.fork_turns.clone());
    agent.nickname = recursive_string(value, &["nickname", "agent_name"]).or(agent.nickname.clone());
    agent.parent_thread_id = recursive_string(value, &["parent_thread_id"])
        .or(agent.parent_thread_id.clone());
    agent.task_name = recursive_string(value, &["task_name"]).or(agent.task_name.clone());
    agent.agent_role = recursive_string(value, &["agent_role"])
        .or(agent.agent_role.clone());
}

fn load_payload_ref(bundle: &Path, reference: Option<&Value>) -> Option<Value> {
    let reference = reference?;
    if reference.is_null() {
        return None;
    }
    let path = reference.get("path")?.as_str()?;
    let safe = Path::new(path);
    if safe.is_absolute()
        || safe
            .components()
            .any(|part| matches!(part, std::path::Component::ParentDir))
    {
        return None;
    }
    let bundle_root = bundle.canonicalize().ok()?;
    let candidate = bundle.join(safe).canonicalize().ok()?;
    if !candidate.starts_with(&bundle_root) {
        return None;
    }
    let text = fs::read_to_string(candidate).ok()?;
    serde_json::from_str(&text).ok()
}

fn find_token_usage(value: &Value) -> Option<TokenUsage> {
    if let Some(usage) = token_usage_from_object(value) {
        return Some(usage);
    }
    match value {
        Value::Array(items) => items.iter().find_map(find_token_usage),
        Value::Object(map) => {
            for preferred in ["usage", "response", "result"] {
                if let Some(child) = map.get(preferred) {
                    if let Some(usage) = find_token_usage(child) {
                        return Some(usage);
                    }
                }
            }
            map.values().find_map(find_token_usage)
        }
        _ => None,
    }
}

fn token_usage_from_object(value: &Value) -> Option<TokenUsage> {
    let map = value.as_object()?;
    let has_known_key = map.contains_key("input_tokens")
        || map.contains_key("output_tokens")
        || map.contains_key("reasoning_output_tokens")
        || map.contains_key("total_tokens");
    if !has_known_key {
        return None;
    }
    let usage = TokenUsage {
        input_tokens: number_field(map.get("input_tokens")),
        cached_input_tokens: number_field(map.get("cached_input_tokens")),
        cache_write_input_tokens: number_field(map.get("cache_write_input_tokens")),
        output_tokens: number_field(map.get("output_tokens")),
        reasoning_output_tokens: number_field(map.get("reasoning_output_tokens")),
        total_tokens: number_field(map.get("total_tokens")),
    }
    .normalized();
    Some(usage)
}

fn number_field(value: Option<&Value>) -> u64 {
    value
        .and_then(|value| value.as_u64().or_else(|| value.as_i64().map(|v| v.max(0) as u64)))
        .unwrap_or(0)
}

fn extract_model_output_texts(value: &Value) -> Vec<String> {
    fn walk(value: &Value, key_hint: Option<&str>, output: &mut Vec<String>) {
        match value {
            Value::String(text) => {
                let key = key_hint.unwrap_or_default().to_ascii_lowercase();
                if matches!(key.as_str(), "text" | "content" | "message" | "output_text" | "summary")
                    && text.trim().len() >= 2
                {
                    push_unique_text(output, text.clone());
                }
            }
            Value::Array(items) => {
                for item in items {
                    walk(item, key_hint, output);
                }
            }
            Value::Object(map) => {
                let object_type = map
                    .get("type")
                    .and_then(Value::as_str)
                    .unwrap_or_default()
                    .to_ascii_lowercase();
                let role = map
                    .get("role")
                    .and_then(Value::as_str)
                    .unwrap_or_default()
                    .to_ascii_lowercase();
                let likely_output = role == "assistant"
                    || object_type.contains("output_text")
                    || object_type == "message"
                    || object_type.contains("agent_message");
                for (key, child) in map {
                    if likely_output || matches!(key.as_str(), "output" | "response" | "content" | "text" | "message") {
                        walk(child, Some(key), output);
                    }
                }
            }
            _ => {}
        }
    }

    let mut output = Vec::new();
    walk(value, None, &mut output);
    output
}

fn recursive_string(value: &Value, keys: &[&str]) -> Option<String> {
    fn walk(value: &Value, keys: &HashSet<String>) -> Option<String> {
        match value {
            Value::Object(map) => {
                for (key, child) in map {
                    if keys.contains(&key.to_ascii_lowercase()) {
                        if let Some(text) = value_to_string(child) {
                            return Some(text);
                        }
                    }
                }
                for child in map.values() {
                    if let Some(value) = walk(child, keys) {
                        return Some(value);
                    }
                }
                None
            }
            Value::Array(items) => items.iter().find_map(|item| walk(item, keys)),
            Value::String(text) => serde_json::from_str::<Value>(text)
                .ok()
                .and_then(|nested| walk(&nested, keys)),
            _ => None,
        }
    }
    let keys: HashSet<String> = keys.iter().map(|key| key.to_ascii_lowercase()).collect();
    walk(value, &keys)
}

fn value_to_string(value: &Value) -> Option<String> {
    match value {
        Value::String(text) => Some(text.clone()),
        Value::Bool(value) => Some(value.to_string()),
        Value::Number(value) => Some(value.to_string()),
        Value::Object(map) => map
            .get("type")
            .and_then(Value::as_str)
            .map(str::to_owned),
        _ => None,
    }
}

fn looks_like_review_assignment(task_name: Option<&str>, message: Option<&str>) -> bool {
    let task = task_name.unwrap_or_default().trim().to_ascii_lowercase();
    let task_match = matches!(task.as_str(), "review" | "reviewer" | "code-review" | "code_review")
        || task.starts_with("review-")
        || task.starts_with("review_")
        || task.ends_with("-review")
        || task.ends_with("_review");
    if task_match {
        return true;
    }

    let message = message.unwrap_or_default().trim().to_ascii_lowercase();
    [
        "review the ",
        "review this ",
        "review these ",
        "review changes",
        "review implementation",
        "perform a code review",
        "act as reviewer",
        "act as a reviewer",
        "audit the ",
        "audit this ",
    ]
    .iter()
    .any(|needle| message.starts_with(needle) || message.contains(needle))
}

fn looks_like_write_command(value: &Value) -> bool {
    let text = value.to_string().to_ascii_lowercase();
    [
        "apply_patch",
        "git commit",
        "git reset",
        "git checkout",
        "git restore",
        "git rebase",
        "cargo fmt",
        "npm run format",
        "prettier --write",
        "ruff format",
        "black ",
        "sed -i",
    ]
    .iter()
    .any(|needle| text.contains(needle))
}

fn normalize_finding_status(value: &str) -> String {
    match value.to_ascii_lowercase().as_str() {
        "fixed" | "resolved" => "resolved",
        "accepted" | "accept" => "accepted",
        "rejected" | "reject" => "rejected",
        "deferred" | "defer" => "deferred",
        "escalated" | "escalate" => "escalated",
        _ => "open",
    }
    .to_owned()
}

fn string_field(value: &Value, key: &str) -> Option<String> {
    value.get(key).and_then(value_to_string)
}

fn type_name(value: &Value) -> Option<String> {
    value
        .get("type")
        .and_then(Value::as_str)
        .map(str::to_owned)
        .or_else(|| value.as_str().map(str::to_owned))
}

fn push_unique_text(output: &mut Vec<String>, text: String) {
    let trimmed = text.trim();
    if trimmed.is_empty() || output.iter().any(|existing| existing == trimmed) {
        return;
    }
    output.push(trimmed.to_owned());
}

fn truncate(value: &str, max_chars: usize) -> String {
    let mut output = String::new();
    for (index, character) in value.chars().enumerate() {
        if index >= max_chars {
            output.push('…');
            break;
        }
        output.push(character);
    }
    output
}

fn short_id(value: &str) -> String {
    value.chars().take(8).collect()
}

pub fn now_ms() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_millis().min(i64::MAX as u128) as i64)
        .unwrap_or(0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn token_usage_is_detected_recursively() {
        let value = serde_json::json!({
            "response": {
                "usage": {
                    "input_tokens": 10,
                    "cached_input_tokens": 2,
                    "output_tokens": 4,
                    "reasoning_output_tokens": 3
                }
            }
        });
        let usage = find_token_usage(&value).expect("usage");
        assert_eq!(usage.total_tokens, 17);
    }

    #[test]
    fn review_finding_status_is_normalized() {
        assert_eq!(normalize_finding_status("fixed"), "resolved");
        assert_eq!(normalize_finding_status("DEFER"), "deferred");
    }

    #[test]
    fn path_traversal_payload_is_rejected() {
        let reference = serde_json::json!({"path": "../secret.json"});
        assert!(load_payload_ref(Path::new("."), Some(&reference)).is_none());
    }

    #[test]
    fn nested_json_string_fields_are_discovered() {
        let value = serde_json::json!({
            "payload": {
                "type": "function",
                "arguments": r#"{"task_name":"auth","model":"gpt-5.6-luna"}"#
            }
        });
        assert_eq!(recursive_string(&value, &["task_name"]).as_deref(), Some("auth"));
        assert_eq!(
            recursive_string(&value, &["model"]).as_deref(),
            Some("gpt-5.6-luna")
        );
    }

    #[test]
    fn raw_spawn_payload_enriches_child_agent() {
        let root = std::env::temp_dir().join(format!(
            "axiom-dashboard-trace-test-{}-{}",
            std::process::id(),
            now_ms()
        ));
        let payloads = root.join("payloads");
        fs::create_dir_all(&payloads).expect("create payload directory");

        fs::write(
            root.join(MANIFEST_NAME),
            serde_json::to_vec(&serde_json::json!({
                "schema_version": 1,
                "trace_id": "trace-test",
                "rollout_id": "rollout-test",
                "root_thread_id": "thread-root",
                "started_at_unix_ms": 1_000,
                "raw_event_log": TRACE_NAME,
                "payloads_dir": "payloads"
            }))
            .expect("manifest JSON"),
        )
        .expect("write manifest");

        fs::write(
            payloads.join("spawn-invocation.json"),
            serde_json::to_vec(&serde_json::json!({
                "tool_name": "spawn_agent",
                "tool_namespace": null,
                "payload": {
                    "type": "function",
                    "arguments": r#"{"task_name":"auth","message":"Implement auth flow","model":"gpt-5.6-luna","reasoning_effort":"max","fork_turns":"none"}"#
                }
            }))
            .expect("invocation JSON"),
        )
        .expect("write invocation");

        fs::write(
            payloads.join("spawn-result.json"),
            serde_json::to_vec(&serde_json::json!({
                "type": "direct_response",
                "response_item": {
                    "type": "function_call_output",
                    "output": r#"{"task_name":"/root/auth","status":"accepted"}"#
                }
            }))
            .expect("result JSON"),
        )
        .expect("write result");

        fs::write(
            payloads.join("response.json"),
            serde_json::to_vec(&serde_json::json!({
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 20,
                    "reasoning_output_tokens": 5
                },
                "output": [{
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Implemented auth flow."}]
                }]
            }))
            .expect("response JSON"),
        )
        .expect("write response");

        let events = vec![
            serde_json::json!({
                "schema_version": 1,
                "seq": 0,
                "wall_time_unix_ms": 1_000,
                "rollout_id": "rollout-test",
                "thread_id": null,
                "codex_turn_id": null,
                "payload": {"type": "rollout_started", "trace_id": "trace-test", "root_thread_id": "thread-root"}
            }),
            serde_json::json!({
                "schema_version": 1,
                "seq": 1,
                "wall_time_unix_ms": 1_001,
                "rollout_id": "rollout-test",
                "thread_id": "thread-root",
                "codex_turn_id": "turn-root",
                "payload": {
                    "type": "tool_call_started",
                    "tool_call_id": "call-spawn",
                    "kind": "spawn_agent",
                    "summary": {"type": "generic", "label": "spawn_agent", "input_preview": null, "output_preview": null},
                    "invocation_payload": {"path": "payloads/spawn-invocation.json"}
                }
            }),
            serde_json::json!({
                "schema_version": 1,
                "seq": 2,
                "wall_time_unix_ms": 1_002,
                "rollout_id": "rollout-test",
                "thread_id": "thread-root",
                "codex_turn_id": "turn-root",
                "payload": {
                    "type": "tool_call_ended",
                    "tool_call_id": "call-spawn",
                    "status": "completed",
                    "result_payload": {"path": "payloads/spawn-result.json"}
                }
            }),
            serde_json::json!({
                "schema_version": 1,
                "seq": 3,
                "wall_time_unix_ms": 1_003,
                "rollout_id": "rollout-test",
                "thread_id": "thread-auth",
                "codex_turn_id": null,
                "payload": {
                    "type": "thread_started",
                    "thread_id": "thread-auth",
                    "agent_path": "/root/auth",
                    "metadata_payload": null
                }
            }),
            serde_json::json!({
                "schema_version": 1,
                "seq": 4,
                "wall_time_unix_ms": 1_004,
                "rollout_id": "rollout-test",
                "thread_id": "thread-auth",
                "codex_turn_id": "turn-auth",
                "payload": {
                    "type": "inference_started",
                    "inference_call_id": "inference-auth",
                    "thread_id": "thread-auth",
                    "codex_turn_id": "turn-auth",
                    "model": "gpt-5.6-luna",
                    "provider_name": "openai",
                    "request_payload": {"path": "payloads/spawn-invocation.json"}
                }
            }),
            serde_json::json!({
                "schema_version": 1,
                "seq": 5,
                "wall_time_unix_ms": 1_005,
                "rollout_id": "rollout-test",
                "thread_id": "thread-auth",
                "codex_turn_id": "turn-auth",
                "payload": {
                    "type": "inference_completed",
                    "inference_call_id": "inference-auth",
                    "response_id": "response-auth",
                    "upstream_request_id": null,
                    "response_payload": {"path": "payloads/response.json"}
                }
            }),
            serde_json::json!({
                "schema_version": 1,
                "seq": 6,
                "wall_time_unix_ms": 1_006,
                "rollout_id": "rollout-test",
                "thread_id": "thread-auth",
                "codex_turn_id": null,
                "payload": {"type": "thread_ended", "thread_id": "thread-auth", "status": "completed"}
            }),
            serde_json::json!({
                "schema_version": 1,
                "seq": 7,
                "wall_time_unix_ms": 1_007,
                "rollout_id": "rollout-test",
                "thread_id": null,
                "codex_turn_id": null,
                "payload": {"type": "rollout_ended", "status": "completed"}
            }),
        ];
        let trace = events
            .iter()
            .map(|event| serde_json::to_string(event).expect("trace event JSON"))
            .collect::<Vec<_>>()
            .join("\n");
        fs::write(root.join(TRACE_NAME), format!("{trace}\n")).expect("write trace");

        let session = parse_bundle(&root, 1_010)
            .expect("parse raw trace bundle");
        let worker = session
            .agents
            .iter()
            .find(|agent| agent.thread_id == "thread-auth")
            .expect("worker agent");
        assert_eq!(worker.kind, "worker");
        assert_eq!(worker.task_name.as_deref(), Some("auth"));
        assert_eq!(worker.model.as_deref(), Some("gpt-5.6-luna"));
        assert_eq!(worker.reasoning_effort.as_deref(), Some("max"));
        assert_eq!(worker.fork_turns.as_deref(), Some("none"));
        assert_eq!(worker.tokens.total_tokens, 120);

        let _ = fs::remove_dir_all(root);
    }

    #[test]
    fn latest_review_verdict_wins() {
        let texts = vec![
            "AX-001 major: fix this. Verdict: FIX_FIRST".to_owned(),
            "AX-001 resolved. Verdict: SHIP".to_owned(),
        ];
        assert_eq!(detect_verdict(&texts).as_deref(), Some("SHIP"));
    }
}
