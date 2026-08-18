use serde::Serialize;

#[derive(Debug, Clone, Serialize, PartialEq)]
pub struct DashboardSnapshot {
    pub dashboard_version: &'static str,
    pub generated_at_unix_ms: i64,
    pub trace_root: String,
    pub repo: Option<String>,
    pub live: bool,
    pub git: GitState,
    pub warnings: Vec<String>,
    pub sessions: Vec<SessionView>,
}

#[derive(Debug, Clone, Serialize, PartialEq)]
pub struct SessionView {
    pub id: String,
    pub bundle_path: String,
    pub trace_id: String,
    pub rollout_id: String,
    pub status: String,
    pub started_at_unix_ms: i64,
    pub ended_at_unix_ms: Option<i64>,
    pub duration_ms: i64,
    pub root_thread_id: String,
    pub agents: Vec<AgentView>,
    pub timeline: Vec<TimelineItem>,
    pub metrics: SessionMetrics,
    pub review: ReviewSummary,
    pub compliance: Vec<ComplianceCheck>,
    pub warnings: Vec<String>,
}

#[derive(Debug, Clone, Serialize, PartialEq, Default)]
pub struct AgentView {
    pub thread_id: String,
    pub agent_path: String,
    pub nickname: Option<String>,
    pub parent_thread_id: Option<String>,
    pub task_name: Option<String>,
    pub agent_role: Option<String>,
    pub kind: String,
    pub status: String,
    pub model: Option<String>,
    pub reasoning_effort: Option<String>,
    pub fork_turns: Option<String>,
    pub started_at_unix_ms: i64,
    pub ended_at_unix_ms: Option<i64>,
    pub duration_ms: i64,
    pub turns: u64,
    pub inference_calls: u64,
    pub review_rounds: u64,
    pub compactions: u64,
    pub tokens: TokenUsage,
    pub result_preview: Option<String>,
    pub write_activity_detected: bool,
}

#[derive(Debug, Clone, Serialize, PartialEq)]
pub struct TimelineItem {
    pub thread_id: String,
    pub label: String,
    pub kind: String,
    pub status: String,
    pub started_at_unix_ms: i64,
    pub ended_at_unix_ms: Option<i64>,
}

#[derive(Debug, Clone, Copy, Serialize, PartialEq, Eq, Default)]
pub struct TokenUsage {
    pub input_tokens: u64,
    pub cached_input_tokens: u64,
    pub cache_write_input_tokens: u64,
    pub output_tokens: u64,
    pub reasoning_output_tokens: u64,
    pub total_tokens: u64,
}

impl TokenUsage {
    pub fn add_assign(&mut self, other: TokenUsage) {
        self.input_tokens = self.input_tokens.saturating_add(other.input_tokens);
        self.cached_input_tokens = self
            .cached_input_tokens
            .saturating_add(other.cached_input_tokens);
        self.cache_write_input_tokens = self
            .cache_write_input_tokens
            .saturating_add(other.cache_write_input_tokens);
        self.output_tokens = self.output_tokens.saturating_add(other.output_tokens);
        self.reasoning_output_tokens = self
            .reasoning_output_tokens
            .saturating_add(other.reasoning_output_tokens);
        self.total_tokens = self.total_tokens.saturating_add(other.total_tokens);
    }

    pub fn normalized(mut self) -> Self {
        if self.total_tokens == 0 {
            self.total_tokens = self
                .input_tokens
                .saturating_add(self.output_tokens);
        }
        self
    }
}

#[derive(Debug, Clone, Serialize, PartialEq, Default)]
pub struct SessionMetrics {
    pub total_tokens: u64,
    pub main_tokens: u64,
    pub worker_tokens: u64,
    pub reviewer_tokens: u64,
    pub main_token_share: Option<f64>,
    pub agent_count: usize,
    pub worker_count: usize,
    pub reviewer_count: usize,
    pub tool_calls: u64,
    pub compactions: u64,
    pub peak_worker_concurrency: usize,
    pub parallel_overlap_ms: i64,
}

#[derive(Debug, Clone, Serialize, PartialEq, Default)]
pub struct ReviewSummary {
    pub present: bool,
    pub reviewer_thread_ids: Vec<String>,
    pub rounds: u64,
    pub verdict: Option<String>,
    pub findings: Vec<ReviewFinding>,
}

#[derive(Debug, Clone, Serialize, PartialEq)]
pub struct ReviewFinding {
    pub id: String,
    pub severity: Option<String>,
    pub status: String,
    pub title: String,
    pub source_thread_id: String,
}

#[derive(Debug, Clone, Serialize, PartialEq)]
pub struct ComplianceCheck {
    pub key: String,
    pub label: String,
    pub status: String,
    pub detail: String,
}

#[derive(Debug, Clone, Serialize, PartialEq, Default)]
pub struct GitState {
    pub available: bool,
    pub root: Option<String>,
    pub branch: Option<String>,
    pub changed_files: usize,
    pub staged_files: usize,
    pub unstaged_files: usize,
    pub untracked_files: usize,
    pub insertions: u64,
    pub deletions: u64,
    pub files: Vec<GitFile>,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Serialize, PartialEq)]
pub struct GitFile {
    pub path: String,
    pub index_status: String,
    pub worktree_status: String,
}
