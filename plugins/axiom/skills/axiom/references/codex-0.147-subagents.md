# Codex v0.147 direct-spawn subagents

This reference is intentionally version-specific. Re-check it before adapting Axiom to another Codex release.

## One-time configuration

Merge this into `~/.codex/config.toml`, then fully restart Codex:

```toml
[features.multi_agent_v2]
enabled = true
expose_spawn_agent_model_overrides = true
wait_agent_enabled = true

# Axiom prefers long event-driven waits instead of repeated 30-second wakeups.
default_wait_timeout_ms = 3600000
max_wait_timeout_ms = 3600000

# Optional while validating routing:
hide_spawn_agent_metadata = false
```

Axiom must not edit the user's global config automatically.

In Codex v0.147, the built-in Multi-Agent V2 wait defaults are 30,000 ms and the hard maximum is 3,600,000 ms. Setting the default to 60 minutes prevents omitted `timeout_ms` calls from repeatedly waking Main every 30 seconds. A `wait_agent` call returns early when agent activity or new steering input arrives, so 60 minutes is an upper bound rather than a forced sleep duration.

## Luna MAX worker

Prefer direct spawn:

```text
spawn_agent(
  task_name = "bounded_worker_task",
  message = "<bounded handoff with enough context to act correctly>",
  model = "gpt-5.6-luna",
  reasoning_effort = "max",
  fork_turns = "none"
)
```

Intent:

- `model` selects Luna;
- `reasoning_effort` selects MAX;
- `fork_turns: "none"` preserves a clean context boundary when the handoff is sufficient;
- `message` contains the context the task actually needs.

Do not confuse `reasoning_effort: "max"` with `service_tier`. Omit `service_tier` unless the user explicitly requests one.

## Sol XHIGH reviewer: fresh initial spawn, same-session re-review

Prefer direct spawn:

```text
spawn_agent(
  task_name = "independent_sol_review",
  message = "<fresh review context with explicit no-edit contract>",
  model = "gpt-5.6-sol",
  reasoning_effort = "xhigh",
  fork_turns = "none"
)
```

Never use Luna as the reviewer. Retain the returned reviewer handle/agent identity. If fixes need re-review, continue with that same reviewer session using the follow-up mechanism exposed by the running Codex tool surface rather than starting a new reviewer from scratch.

If the reviewer session is lost, a new direct-spawn Sol XHIGH reviewer is the recovery path. Rehydrate it with the prior findings, Main adjudication, relevant fixes, current candidate, and verification evidence.

## `fork_turns`

Multi-Agent V2 accepts:

- `"none"` — no conversation fork; Axiom default for clean bounded handoffs;
- `"all"` — full history;
- a positive integer string such as `"3"` — most recent turns.

Choose the smallest context that reliably preserves the task. A recent-turn fork can be better than rewriting subtle dialogue into a packet; full history can be appropriate when the larger conversation materially informs the task. Use context isolation deliberately rather than mechanically.

Do not pass `fork_context` to Multi-Agent V2. Use `fork_turns`.

## Fail closed when model overrides are hidden

Before relying on delegated model routing, confirm that the available `spawn_agent` surface includes both:

- `model`
- `reasoning_effort`

If they are missing, do not silently spawn an unspecified worker that may inherit Main Sol. Continue in Main when practical or report the one-time v0.147 configuration requirement. Do not fall back to Terra merely because Luna routing is unavailable, and never fall back to Luna for independent review.

This preserves the intended cost and role separation.

## Waiting without polling churn

For Axiom's long-running workers, prefer an event-driven wait near the v0.147 maximum rather than repeated short waits:

```text
wait_agent(timeout_ms = 3600000)
```

With the recommended `default_wait_timeout_ms = 3600000`, omitting the argument has the same intended default.

The call can return before 60 minutes when agent activity arrives or the user steers the parent. If the running configuration exposes a lower maximum, use the longest permitted wait that fits the task rather than tight polling.

When several independent agents are running, spawn the useful set first and then wait; do not serialize them by waiting immediately after each spawn unless their work is actually dependent.

## Follow-up and continuity

Use follow-up when it continues the same bounded task and retained worker context is useful. Start a fresh worker when independence or a clean context boundary is more valuable.

For review, preserve the same Sol reviewer across re-review passes when available; do not reuse an implementation worker as the independent reviewer.

## Reviewer read-only contract

Direct spawn does not install a custom read-only profile. Put this contract at the top of the review message:

```text
READ-ONLY REVIEW.
Do not edit files, commit, format, auto-fix, generate code into the working tree,
or run commands likely to mutate it. Inspect and report evidence only.
```

Main should verify the working tree after review before accepting the candidate.

## Troubleshooting Luna spawn after an upgrade

If Codex reports v0.147 but rejects `gpt-5.6-luna` as an unknown child model:

1. fully terminate old Codex/app-server processes;
2. start a new session;
3. confirm model override fields are exposed;
4. retry a minimal Luna spawn;
5. for diagnosis, bypass an old TUI app-server with:

```bash
codex --disable tui_app_server -m gpt-5.6-sol
```

Do not claim routing succeeded based only on the child saying “I am Luna.” Use visible spawn metadata or runtime evidence when available.
