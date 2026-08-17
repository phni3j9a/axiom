# Axiom Design

Version: 0.1.2  
Target: Codex v0.147.x  
Status: Initial implementation

## 1. Problem

Large software tasks can fill Main context with repository exploration, logs, test output, patch details, and repeated reviews. After compaction, intent and important decisions may be diluted. A rigid orchestration workflow can reduce some context loss, but it introduces ceremony and can prevent a capable Main model from choosing a better route.

## 2. Design thesis

Axiom does not orchestrate the agent. Axiom teaches the agent how to orchestrate itself.

The Main Sol model remains the authority for user intent, architecture/design, decomposition, integration, review adjudication, and final acceptance.

Bounded cognitive labor is normally externalized to Luna MAX when doing so creates net context, cost, or execution benefit. Independent review starts with a fresh Sol XHIGH reviewer when Main judges a second perspective useful; subsequent re-review stays in that same reviewer session when available.

## 3. Rule taxonomy

Axiom intentionally separates three kinds of guidance.

### Hard constraints

Keep these few and structural:

- Main retains final authority over intent, architecture, integration, review adjudication, and acceptance.
- Delegated independent reviewer is Sol XHIGH, not Luna.
- Initial reviewer is fresh; same reviewer is reused for re-review when available.
- Reviewer findings are adjudicated by Main before becoming fix requirements.
- Pre-existing user work is not discarded or rewritten without applicable authorization.
- Destructive Git/history operations require applicable authorization.
- Routing/verification claims must reflect actual runtime evidence.

### Strong defaults

These are expected to be good in ordinary Axiom use, but Main may deviate for a concrete reason:

- direct-spawn Luna MAX for bounded work;
- `fork_turns: "none"` for clean handoffs;
- Main-owned commits in a shared working tree;
- long event-driven `wait_agent` waits;
- independent Sol review for high-risk/high-uncertainty candidates.

### Heuristics

These stay deliberately model-judged:

- whether to delegate;
- agent count;
- handoff structure/detail;
- parallelism and worktree use;
- review threshold;
- finding count;
- review-pass count;
- convergence/stop decision;
- worker commit use.

This taxonomy prevents useful defaults from accidentally becoming a workflow.

## 4. Core axioms

1. **Main owns meaning.** Do not delegate final architecture, product intent, or acceptance.
2. **Delegate bounded work for net benefit.** Use Luna when context isolation, cost, parallelism, or execution focus justifies coordination overhead.
3. **Luna first.** Use direct-spawn Luna MAX for ordinary delegated work, including exploration.
4. **Sol reviews.** If independent review is useful, use fresh direct-spawn Sol XHIGH initially, then reuse that reviewer for re-review.
5. **Context isolation is deliberate.** Prefer `fork_turns: "none"`, but recent-turn inheritance is allowed when it preserves essential context better.
6. **Parallelism is an optimization problem.** Prefer disjoint ownership while letting Main trade speed against integration cost.
7. **Verify the actual candidate.** Worker claims do not replace inspection and deterministic evidence.
8. **Freeze findings, not judgment.** Stable IDs and same-reviewer continuity reduce churn; Main decides what matters and when review has converged.
9. **Preserve user work.** Never discard, overwrite, or misattribute pre-existing changes.
10. **Keep simple work simple.** Delegation and review are tools, not mandatory phases.

## 5. Why no Terra default

Axiom does not map “exploration” to Terra. Luna MAX is the default bounded worker for exploration, implementation, tests, debugging, and mechanical refactors. Another model is selected only for a concrete task-specific reason or an explicit user request.

Main Sol handles substantive ambiguity instead of delegating that ambiguity to a permanent intermediate orchestrator.

## 6. Why direct spawn only

Axiom deliberately avoids custom agent TOML files.

Benefits include simpler installation, fewer environment-specific paths, and visible model/effort choices at spawn time.

Trade-off: a direct-spawn reviewer cannot be hard-pinned by Axiom to a dedicated read-only custom sandbox. Read-only review is therefore a behavioral contract, and Main verifies the candidate tree after review.

## 7. Automatic use

Axiom has one broad but focused skill. Its description covers non-trivial software engineering tasks, while `allow_implicit_invocation: true` permits automatic selection.

It does not announce an “Axiom mode,” require route labels, or pause for activation. The user should experience normal Codex behavior with better delegation and review decisions.

## 8. Review policy

Review is risk-based; reviewer identity is fixed.

File count and rigid severity enums are not review policy. Main weighs uncertainty, blast radius, deterministic verification quality, and domain risk. The reviewer returns material findings with stable IDs and evidence; Main adjudicates them. Re-review reuses the same reviewer session and preserves context. No fixed finding or round cap is imposed.

## 9. v0.147 wait policy

Codex v0.147 defaults Multi-Agent V2 `wait_agent` to 30 seconds and permits a maximum of 60 minutes. Axiom's example config sets `default_wait_timeout_ms` and `max_wait_timeout_ms` to `3600000`, and its runtime guidance prefers `wait_agent(timeout_ms = 3600000)` for long worker activity.

Because `wait_agent` returns on mailbox activity or steering input before the deadline, 60 minutes is a maximum wait window, not a forced 60-minute stall. This avoids unnecessary 30-second timeout/wakeup cycles during long Luna or Sol work.

## 10. Non-goals

Axiom is not:

- a project-management workflow;
- a planner approval system;
- a persistent runtime state machine;
- a custom-agent installer;
- a commit generator;
- a substitute for deterministic tests;
- a fixed reviewer verdict/severity framework;
- a promise that more agents always improve results.
