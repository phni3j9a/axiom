declare const React: any;
declare const ReactDOM: any;

const h = React.createElement;

type CheckStatus = "pass" | "warn" | "fail" | "unknown" | "not_applicable";

interface TokenUsage {
  input_tokens: number;
  cached_input_tokens: number;
  cache_write_input_tokens: number;
  output_tokens: number;
  reasoning_output_tokens: number;
  total_tokens: number;
}

interface AgentView {
  thread_id: string;
  agent_path: string;
  nickname: string | null;
  parent_thread_id: string | null;
  task_name: string | null;
  agent_role: string | null;
  kind: "main" | "worker" | "reviewer" | string;
  status: string;
  model: string | null;
  reasoning_effort: string | null;
  fork_turns: string | null;
  started_at_unix_ms: number;
  ended_at_unix_ms: number | null;
  duration_ms: number;
  turns: number;
  inference_calls: number;
  review_rounds: number;
  compactions: number;
  tokens: TokenUsage;
  result_preview: string | null;
  write_activity_detected: boolean;
}

interface TimelineItem {
  thread_id: string;
  label: string;
  kind: string;
  status: string;
  started_at_unix_ms: number;
  ended_at_unix_ms: number | null;
}

interface SessionMetrics {
  total_tokens: number;
  main_tokens: number;
  worker_tokens: number;
  reviewer_tokens: number;
  main_token_share: number | null;
  agent_count: number;
  worker_count: number;
  reviewer_count: number;
  tool_calls: number;
  compactions: number;
  peak_worker_concurrency: number;
  parallel_overlap_ms: number;
}

interface ReviewFinding {
  id: string;
  severity: string | null;
  status: string;
  title: string;
  source_thread_id: string;
}

interface ReviewSummary {
  present: boolean;
  reviewer_thread_ids: string[];
  rounds: number;
  verdict: string | null;
  findings: ReviewFinding[];
}

interface ComplianceCheck {
  key: string;
  label: string;
  status: CheckStatus;
  detail: string;
}

interface GitFile {
  path: string;
  index_status: string;
  worktree_status: string;
}

interface GitState {
  available: boolean;
  root: string | null;
  branch: string | null;
  changed_files: number;
  staged_files: number;
  unstaged_files: number;
  untracked_files: number;
  insertions: number;
  deletions: number;
  files: GitFile[];
  error: string | null;
}

interface SessionView {
  id: string;
  bundle_path: string;
  trace_id: string;
  rollout_id: string;
  status: string;
  started_at_unix_ms: number;
  ended_at_unix_ms: number | null;
  duration_ms: number;
  root_thread_id: string;
  agents: AgentView[];
  timeline: TimelineItem[];
  metrics: SessionMetrics;
  review: ReviewSummary;
  compliance: ComplianceCheck[];
  warnings: string[];
}

interface DashboardSnapshot {
  dashboard_version: string;
  generated_at_unix_ms: number;
  trace_root: string;
  repo: string | null;
  live: boolean;
  git: GitState;
  warnings: string[];
  sessions: SessionView[];
}

let latestSnapshot: DashboardSnapshot | null = null;
let selectedSessionId: string | null = null;
let connectionState: "connecting" | "live" | "offline" = "connecting";

function classNames(...names: Array<string | false | null | undefined>): string {
  return names.filter(Boolean).join(" ");
}

function formatDuration(ms: number): string {
  const seconds = Math.max(0, Math.floor(ms / 1000));
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remain = seconds % 60;
  if (minutes < 60) return `${minutes}m ${remain.toString().padStart(2, "0")}s`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ${(minutes % 60).toString().padStart(2, "0")}m`;
}

function formatNumber(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}m`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(value >= 100_000 ? 0 : 1)}k`;
  return value.toLocaleString();
}

function formatTime(unixMs: number): string {
  return new Date(unixMs).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function formatPercent(value: number | null): string {
  if (value === null || Number.isNaN(value)) return "—";
  return `${Math.round(value * 100)}%`;
}

function modelLabel(agent: AgentView): string {
  if (!agent.model) return "model unknown";
  const lower = agent.model.toLowerCase();
  if (lower.includes("luna")) return "LUNA";
  if (lower.includes("sol")) return "SOL";
  if (lower.includes("terra")) return "TERRA";
  return agent.model;
}

function effortLabel(agent: AgentView): string {
  return agent.reasoning_effort ? agent.reasoning_effort.toUpperCase() : "?";
}

function StatusDot(props: { status: string }): any {
  return h("span", {
    className: classNames("status-dot", `status-${props.status}`),
    title: props.status,
  });
}

function MetricCard(props: {
  label: string;
  value: string;
  detail?: string;
  accent?: string;
}): any {
  return h(
    "div",
    { className: classNames("metric-card", props.accent && `accent-${props.accent}`) },
    h("div", { className: "metric-label" }, props.label),
    h("div", { className: "metric-value" }, props.value),
    props.detail ? h("div", { className: "metric-detail" }, props.detail) : null,
  );
}

function Header(props: { snapshot: DashboardSnapshot; session: SessionView | null }): any {
  const repo = props.snapshot.git.root || props.snapshot.repo || "repository not detected";
  const branch = props.snapshot.git.branch || "—";
  return h(
    "header",
    { className: "app-header" },
    h(
      "div",
      { className: "brand" },
      h("div", { className: "brand-mark" }, "A"),
      h(
        "div",
        null,
        h("div", { className: "brand-name" }, "AXIOM"),
        h("div", { className: "brand-subtitle" }, "Agentic Engineering Observatory"),
      ),
    ),
    h(
      "div",
      { className: "header-context" },
      h(
        "div",
        { className: "connection" },
        h(StatusDot, { status: connectionState === "live" ? "running" : connectionState }),
        h("span", null, connectionState === "live" ? "LIVE" : connectionState.toUpperCase()),
      ),
      h("div", { className: "repo-label", title: repo }, repo.split(/[\\/]/).filter(Boolean).pop() || repo),
      h("div", { className: "branch-pill" }, branch),
    ),
  );
}

function SessionSelector(props: { snapshot: DashboardSnapshot; session: SessionView | null }): any {
  if (props.snapshot.sessions.length <= 1) {
    return h(
      "div",
      { className: "session-single" },
      props.session ? `Session ${shortId(props.session.rollout_id)}` : "No session",
    );
  }
  return h(
    "label",
    { className: "session-select-wrap" },
    h("span", null, "Session"),
    h(
      "select",
      {
        value: props.session?.id || "",
        onChange: (event: Event) => {
          selectedSessionId = (event.target as HTMLSelectElement).value;
          renderApp();
        },
      },
      props.snapshot.sessions.map((session) =>
        h(
          "option",
          { key: session.id, value: session.id },
          `${formatTime(session.started_at_unix_ms)} · ${shortId(session.rollout_id)} · ${session.status}`,
        ),
      ),
    ),
  );
}

function AgentCard(props: { agent: AgentView; compact?: boolean }): any {
  const agent = props.agent;
  const title = agent.task_name || agent.nickname || (agent.kind === "main" ? "Main" : agent.agent_path);
  return h(
    "article",
    {
      className: classNames("agent-card", `agent-${agent.kind}`, props.compact && "agent-compact"),
      title: agent.result_preview || undefined,
    },
    h(
      "div",
      { className: "agent-card-top" },
      h("span", { className: "agent-kind" }, agent.kind.toUpperCase()),
      h(StatusDot, { status: agent.status }),
    ),
    h("div", { className: "agent-title" }, title),
    h(
      "div",
      { className: "agent-model" },
      h("strong", null, modelLabel(agent)),
      h("span", null, effortLabel(agent)),
    ),
    h(
      "div",
      { className: "agent-meta" },
      h("span", null, formatDuration(agent.duration_ms)),
      h("span", null, `${formatNumber(agent.tokens.total_tokens)} tok`),
      agent.compactions > 0 ? h("span", { className: "warn-text" }, `${agent.compactions} compact`) : null,
    ),
  );
}

function AgentGraph(props: { session: SessionView }): any {
  const main = props.session.agents.find((agent) => agent.kind === "main") || null;
  const workers = props.session.agents.filter((agent) => agent.kind === "worker");
  const reviewers = props.session.agents.filter((agent) => agent.kind === "reviewer");
  return h(
    "section",
    { className: "panel graph-panel" },
    h(PanelHeader, { title: "Agent graph", meta: `${props.session.metrics.agent_count} agents` }),
    h(
      "div",
      { className: "agent-graph" },
      h("div", { className: "graph-column graph-main" }, main ? h(AgentCard, { agent: main }) : null),
      workers.length > 0
        ? h("div", { className: "graph-connector" }, h("span", null, "→"))
        : null,
      h(
        "div",
        { className: "graph-column graph-workers" },
        workers.length > 0
          ? workers.map((agent) => h(AgentCard, { key: agent.thread_id, agent, compact: true }))
          : h("div", { className: "empty-mini" }, "No delegated workers"),
      ),
      reviewers.length > 0
        ? h("div", { className: "graph-connector" }, h("span", null, "→"))
        : null,
      h(
        "div",
        { className: "graph-column graph-reviewers" },
        reviewers.map((agent) => h(AgentCard, { key: agent.thread_id, agent, compact: true })),
      ),
    ),
  );
}

function PanelHeader(props: { title: string; meta?: string }): any {
  return h(
    "div",
    { className: "panel-header" },
    h("h2", null, props.title),
    props.meta ? h("span", { className: "panel-meta" }, props.meta) : null,
  );
}

function Timeline(props: { session: SessionView }): any {
  const start = props.session.started_at_unix_ms;
  const end = props.session.ended_at_unix_ms || Date.now();
  const span = Math.max(1, end - start);
  return h(
    "section",
    { className: "panel timeline-panel" },
    h(PanelHeader, {
      title: "Parallel timeline",
      meta: `peak ${props.session.metrics.peak_worker_concurrency} · overlap ${formatDuration(props.session.metrics.parallel_overlap_ms)}`,
    }),
    h(
      "div",
      { className: "timeline" },
      props.session.timeline.map((item) => {
        const itemEnd = item.ended_at_unix_ms || end;
        const left = Math.max(0, Math.min(100, ((item.started_at_unix_ms - start) / span) * 100));
        const width = Math.max(1.5, Math.min(100 - left, ((itemEnd - item.started_at_unix_ms) / span) * 100));
        return h(
          "div",
          { className: "timeline-row", key: item.thread_id },
          h("div", { className: "timeline-label", title: item.label }, item.label),
          h(
            "div",
            { className: "timeline-track" },
            h("div", {
              className: classNames("timeline-bar", `timeline-${item.kind}`, `bar-${item.status}`),
              style: { left: `${left}%`, width: `${width}%` },
              title: `${formatTime(item.started_at_unix_ms)} · ${formatDuration(itemEnd - item.started_at_unix_ms)}`,
            }),
          ),
        );
      }),
      h(
        "div",
        { className: "timeline-axis" },
        h("span", null, "+0s"),
        h("span", null, formatDuration(span / 2)),
        h("span", null, formatDuration(span)),
      ),
    ),
  );
}

function ReviewPanel(props: { review: ReviewSummary }): any {
  const review = props.review;
  return h(
    "section",
    { className: "panel review-panel" },
    h(PanelHeader, {
      title: "Review",
      meta: review.present ? `${review.rounds} round${review.rounds === 1 ? "" : "s"}` : "not observed",
    }),
    review.present
      ? h(
          "div",
          null,
          h(
            "div",
            { className: "review-verdict-row" },
            h("span", { className: "muted" }, "Verdict"),
            h(
              "span",
              { className: classNames("verdict", `verdict-${(review.verdict || "pending").toLowerCase()}`) },
              review.verdict || "PENDING",
            ),
          ),
          review.findings.length > 0
            ? h(
                "div",
                { className: "finding-list" },
                review.findings.map((finding) =>
                  h(
                    "div",
                    { className: "finding-row", key: finding.id },
                    h("span", { className: "finding-id" }, finding.id),
                    h("span", { className: classNames("finding-status", `finding-${finding.status}`) }, finding.status),
                    h("span", { className: "finding-title", title: finding.title }, finding.title),
                  ),
                ),
              )
            : h("div", { className: "empty-mini" }, "No AX-* findings parsed from reviewer output."),
        )
      : h("div", { className: "empty-mini" }, "A delegated Sol review has not been observed in this trace."),
  );
}

function CompliancePanel(props: { checks: ComplianceCheck[] }): any {
  return h(
    "section",
    { className: "panel compliance-panel" },
    h(PanelHeader, { title: "Axiom principles", meta: "observed evidence" }),
    h(
      "div",
      { className: "check-list" },
      props.checks.map((item) =>
        h(
          "div",
          { className: "check-row", key: item.key },
          h("div", { className: classNames("check-icon", `check-${item.status}`) }, checkGlyph(item.status)),
          h(
            "div",
            { className: "check-copy" },
            h("div", { className: "check-label" }, item.label),
            h("div", { className: "check-detail" }, item.detail),
          ),
        ),
      ),
    ),
  );
}

function checkGlyph(status: CheckStatus): string {
  switch (status) {
    case "pass":
      return "✓";
    case "fail":
      return "×";
    case "warn":
      return "!";
    case "unknown":
      return "?";
    default:
      return "–";
  }
}

function TokenPanel(props: { session: SessionView }): any {
  const session = props.session;
  const rows = [
    ["Main", session.metrics.main_tokens, "main"],
    ["Workers", session.metrics.worker_tokens, "worker"],
    ["Reviewer", session.metrics.reviewer_tokens, "reviewer"],
  ] as const;
  const total = Math.max(1, session.metrics.total_tokens);
  return h(
    "section",
    { className: "panel token-panel" },
    h(PanelHeader, { title: "Context & tokens", meta: `${formatNumber(session.metrics.total_tokens)} total` }),
    h(
      "div",
      { className: "token-bars" },
      rows.map(([label, value, kind]) =>
        h(
          "div",
          { className: "token-row", key: label },
          h("div", { className: "token-label" }, label),
          h(
            "div",
            { className: "token-track" },
            h("div", {
              className: classNames("token-fill", `token-${kind}`),
              style: { width: `${Math.max(value > 0 ? 2 : 0, (value / total) * 100)}%` },
            }),
          ),
          h("div", { className: "token-value" }, formatNumber(value)),
        ),
      ),
    ),
    h(
      "div",
      { className: "token-foot" },
      h("span", null, `Main share ${formatPercent(session.metrics.main_token_share)}`),
      h("span", null, `${session.metrics.compactions} compactions`),
      h("span", null, `${session.metrics.tool_calls} tool calls`),
    ),
  );
}

function GitPanel(props: { git: GitState }): any {
  const git = props.git;
  return h(
    "section",
    { className: "panel git-panel" },
    h(PanelHeader, { title: "Git", meta: git.available ? git.branch || "detached" : "unavailable" }),
    git.available
      ? h(
          "div",
          null,
          h(
            "div",
            { className: "git-stats" },
            h("div", null, h("strong", null, git.changed_files), h("span", null, "changed")),
            h("div", null, h("strong", { className: "plus" }, `+${git.insertions}`), h("span", null, "insertions")),
            h("div", null, h("strong", { className: "minus" }, `−${git.deletions}`), h("span", null, "deletions")),
          ),
          h(
            "div",
            { className: "git-file-list" },
            git.files.slice(0, 8).map((file) =>
              h(
                "div",
                { className: "git-file", key: file.path },
                h("span", { className: "git-code" }, `${file.index_status}${file.worktree_status}`),
                h("span", { title: file.path }, file.path),
              ),
            ),
            git.files.length > 8 ? h("div", { className: "muted" }, `+${git.files.length - 8} more`) : null,
          ),
        )
      : h("div", { className: "empty-mini" }, git.error || "Git repository was not detected."),
  );
}

function Warnings(props: { warnings: string[] }): any {
  if (props.warnings.length === 0) return null;
  return h(
    "div",
    { className: "warning-stack" },
    props.warnings.map((warning, index) => h("div", { className: "warning-banner", key: index }, warning)),
  );
}

function EmptyState(props: { snapshot: DashboardSnapshot }): any {
  return h(
    "main",
    { className: "empty-state" },
    h("div", { className: "empty-orbit" }, h("div", { className: "empty-core" }, "A")),
    h("h1", null, "Waiting for a Codex rollout trace"),
    h(
      "p",
      null,
      "Rollout tracing is opt-in. Set the environment variable before starting Codex, then launch a new session.",
    ),
    h(
      "pre",
      null,
      `export CODEX_ROLLOUT_TRACE_ROOT="${props.snapshot.trace_root}"\ncodex`,
    ),
    h("p", { className: "privacy-note" }, "Traces remain local and may contain sensitive prompts, outputs, paths, and terminal data."),
    h(Warnings, { warnings: props.snapshot.warnings }),
  );
}

function App(props: { snapshot: DashboardSnapshot }): any {
  const snapshot = props.snapshot;
  const session = selectSession(snapshot);
  if (!session) {
    return h("div", { className: "app-shell" }, h(Header, { snapshot, session: null }), h(EmptyState, { snapshot }));
  }
  const warnings = [...snapshot.warnings, ...session.warnings];
  return h(
    "div",
    { className: "app-shell" },
    h(Header, { snapshot, session }),
    h(
      "main",
      { className: "dashboard" },
      h(
        "div",
        { className: "session-toolbar" },
        h(SessionSelector, { snapshot, session }),
        h(
          "div",
          { className: "session-meta" },
          h(StatusDot, { status: session.status }),
          h("span", null, session.status),
          h("span", null, formatTime(session.started_at_unix_ms)),
          h("code", null, shortId(session.rollout_id)),
        ),
      ),
      h(Warnings, { warnings }),
      h(
        "section",
        { className: "metrics-grid" },
        h(MetricCard, {
          label: "Session",
          value: formatDuration(session.duration_ms),
          detail: session.status,
          accent: "blue",
        }),
        h(MetricCard, {
          label: "Agents",
          value: session.metrics.agent_count.toString(),
          detail: `${session.metrics.worker_count} workers · ${session.metrics.reviewer_count} reviewer`,
          accent: "cyan",
        }),
        h(MetricCard, {
          label: "Parallelism",
          value: `×${session.metrics.peak_worker_concurrency}`,
          detail: `${formatDuration(session.metrics.parallel_overlap_ms)} overlap`,
          accent: "violet",
        }),
        h(MetricCard, {
          label: "Review",
          value: session.review.verdict || (session.review.present ? "ACTIVE" : "—"),
          detail: session.review.present ? `${session.review.rounds} round(s)` : "not observed",
          accent: "amber",
        }),
        h(MetricCard, {
          label: "Main share",
          value: formatPercent(session.metrics.main_token_share),
          detail: `${formatNumber(session.metrics.total_tokens)} tokens observed`,
          accent: "green",
        }),
      ),
      h(AgentGraph, { session }),
      h(Timeline, { session }),
      h(
        "div",
        { className: "two-column" },
        h(ReviewPanel, { review: session.review }),
        h(CompliancePanel, { checks: session.compliance }),
      ),
      h(
        "div",
        { className: "two-column bottom-grid" },
        h(TokenPanel, { session }),
        h(GitPanel, { git: snapshot.git }),
      ),
      h(
        "footer",
        null,
        h("span", null, `Axiom Dashboard ${snapshot.dashboard_version}`),
        h("span", null, "localhost only · read-only repository observation · no telemetry"),
      ),
    ),
  );
}

function shortId(value: string): string {
  return value.length <= 10 ? value : value.slice(0, 10);
}

function selectSession(snapshot: DashboardSnapshot): SessionView | null {
  if (snapshot.sessions.length === 0) return null;
  const selected = selectedSessionId
    ? snapshot.sessions.find((session) => session.id === selectedSessionId)
    : null;
  if (selected) return selected;
  selectedSessionId = snapshot.sessions[0].id;
  return snapshot.sessions[0];
}

async function refreshState(): Promise<void> {
  try {
    const response = await fetch("/api/state", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    latestSnapshot = (await response.json()) as DashboardSnapshot;
    connectionState = "live";
    renderApp();
  } catch (error) {
    connectionState = "offline";
    console.error("Axiom Dashboard state refresh failed", error);
    renderApp();
  }
}

function connectEvents(): void {
  const events = new EventSource("/api/events");
  events.addEventListener("open", () => {
    connectionState = "live";
    renderApp();
  });
  events.addEventListener("refresh", () => {
    void refreshState();
  });
  events.addEventListener("error", () => {
    connectionState = "offline";
    renderApp();
  });
}

function renderApp(): void {
  const root = document.getElementById("root");
  if (!root) return;
  if (!latestSnapshot) {
    ReactDOM.render(
      h("div", { className: "boot-screen" }, h("div", { className: "boot-mark" }, "A"), h("p", null, "Loading Axiom observability…")),
      root,
    );
    return;
  }
  ReactDOM.render(h(App, { snapshot: latestSnapshot }), root);
}

renderApp();
void refreshState();
connectEvents();
