# Axiom Design

Version: 0.1.6
Target: Codex v0.147.x
Status: Core-only guidance-first implementation

## 1. Problem

Large software tasks can fill Main context with repository exploration, logs, test output, patch details, and repeated reviews. After compaction, intent and important decisions may be diluted. A rigid orchestration workflow can avoid some context loss, but it introduces ceremony, limits when the plugin is useful, and may prevent a capable Main model from choosing a better route.

## 2. Design thesis

Axiom does not orchestrate the agent. Axiom teaches the agent how to orchestrate itself.

The Main Sol model remains the authority for:

- user intent
- architecture and design
- decomposition
- integration
- review adjudication
- final acceptance

Bounded cognitive labor is externalized to Luna MAX. Independent review is externalized to a fresh Sol XHIGH only when the change is meaningful.

Axiom v0.1.6 preserves the worker economics made explicit in v0.1.4: under the current Codex/model economics targeted by this version, ordinary Luna MAX worker usage is treated as **almost free** for orchestration decisions. This deliberately makes Main context preservation more important than minimizing Luna usage.

> **Main context is expensive; Luna compute is almost free.**

This is a versioned assumption. If model economics change materially, the policy should be updated rather than treated as timeless.

## 3. Core axioms

1. **Main owns meaning.** Do not delegate final architecture, product intent, or acceptance.
2. **Delegate bounded work proactively.** Use workers for work that has a clear objective, scope, constraints, and verification; do not keep such work in Main merely to save Luna usage.
3. **Luna first.** Use direct-spawn Luna MAX for ordinary delegated work, including exploration.
4. **Sol reviews.** If independent review is warranted, use a fresh direct-spawn Sol XHIGH.
5. **Fresh context by default.** Prefer self-contained packets with `fork_turns: "none"`.
6. **Prefer useful parallelism.** When multiple bounded tasks are independent, launch Luna MAX workers concurrently. Main chooses the natural fleet size; there is no fixed fan-out. Parallel writes require disjoint scopes and stable interfaces.
7. **Verify the actual tree.** Worker claims never replace inspection, tests, or diff review.
8. **Preserve review continuity.** Spawn a fresh Sol for the initial review, then reuse that same reviewer for re-review while Main owns every finding decision.
9. **Preserve user work.** Never discard, overwrite, or misattribute pre-existing changes.
10. **Keep simple work simple.** Delegation and review are tools, not mandatory phases. Coordination/integration overhead can justify staying in Main; Luna token cost alone cannot.

## 4. Why no Terra default

Axiom does not map “exploration” to Terra. Luna MAX is the default bounded worker for exploration, implementation, tests, debugging, and mechanical refactors. Another model is selected only for a concrete task-specific reason or an explicit user request.

Main Sol handles substantive ambiguity instead of delegating that ambiguity to a permanent intermediate orchestrator.

## 5. Parallel Luna fleet policy

Luna MAX is cheap enough that Axiom lowers the threshold for useful fan-out. The explicit v0.1.4 assumption remains unchanged in v0.1.6: ordinary Luna worker compute is treated as almost free, so Luna usage itself is not a meaningful reason to serialize or retain bounded work in Main.

If Main can identify two or more bounded tasks whose results do not depend on each other, parallel execution is the preferred default rather than serial spawn/wait cycles.

The policy is deliberately dependency-driven rather than numeric:

- no fixed worker count
- no target concurrency number
- no artificial task fragmentation
- read-only investigations may fan out aggressively
- write tasks may fan out when ownership is disjoint and interfaces are stable
- overlapping writes are serialized or isolated with worktrees

The practical constraints are coordination, latency, dependency ordering, write conflicts, integration, and verification—not Luna token conservation.

Main Sol owns the task graph and integration. Axiom does not introduce a permanent intermediary orchestrator.

## 6. Why direct spawn only

Axiom deliberately avoids custom agent TOML files.

Benefits:

- no separate agent installation
- fewer environment-specific paths
- easier plugin installation and removal
- the Main can create the exact number of workers needed
- model and effort remain visible in each spawn request

Trade-off:

- a direct-spawn reviewer inherits the runtime environment and cannot be hard-pinned to a dedicated read-only sandbox by Axiom
- read-only review is therefore enforced by instructions and checked by Main

## 7. Automatic use

Axiom has one broad but focused skill. Its description covers non-trivial software engineering tasks, while `allow_implicit_invocation: true` explicitly permits automatic selection.

It must not announce an “Axiom mode,” require route labels, or pause for activation. The user should experience normal Codex behavior with better delegation and review decisions.

## 8. Review policy

Review is risk-based; reviewer identity is fixed.

- trivial/non-behavioral change: Main verification may be enough
- meaningful behavioral change: fresh Sol XHIGH review strongly preferred
- security, auth, persistence, migration, concurrency, public API, broad refactor: fresh Sol XHIGH review expected

The initial reviewer is fresh and independent. The same reviewer agent is then reused for re-review so finding IDs, prior evidence, and Main adjudications remain in context. Main decides which findings are accepted, deferred, rejected, or escalated and decides when review is complete. Axiom imposes no fixed finding count or review-round limit.

## 9. Non-goals

Axiom is not:

- a project-management workflow
- a planner approval system
- a persistent runtime state machine
- a custom-agent installer
- a commit generator
- a substitute for deterministic tests
- a fixed-size agent fleet
- a promise that more agents always improve results
