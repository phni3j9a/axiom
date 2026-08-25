# Axiom Design

Version: 0.1.8
Target: Codex v0.147.x
Status: Core-only guidance-first implementation

## 1. Problem

Large software tasks can fill Main context with repository exploration, logs, test output, patch details, and repeated reviews. After compaction, intent and important decisions may be diluted. A rigid orchestration workflow can avoid some context loss, but it introduces ceremony, limits when the plugin is useful, and may prevent a capable Main model from choosing a better route.

## 2. Design thesis

Axiom does not orchestrate the agent. Axiom teaches the agent how to orchestrate itself.

The Main Sol model remains the authority for:

- user intent
- architecture and design direction
- decomposition
- integration
- review adjudication
- final acceptance

Ordinary bounded cognitive labor is externalized to Luna MAX. Bounded work that requires material visual, interaction, or information-design judgment is externalized to Sol MAX. Independent review is externalized to a separate fresh Sol XHIGH only when the change is meaningful.

Axiom v0.1.8 preserves the worker economics made explicit in v0.1.4: under the current Codex/model economics targeted by this version, ordinary Luna MAX worker usage is treated as **almost free** for orchestration decisions. This deliberately makes Main context preservation more important than minimizing Luna usage.

> **Main context is expensive; Luna compute is almost free.**

This is a versioned assumption. If model economics change materially, the policy should be updated rather than treated as timeless.

## 3. Core axioms

1. **Main owns meaning.** Do not delegate final architecture, product intent, or acceptance.
2. **Delegate bounded work proactively.** Use workers for work that has a clear objective, scope, constraints, and verification; do not keep such work in Main merely to save Luna usage.
3. **Luna first for ordinary work.** Use direct-spawn Luna MAX for ordinary delegated work, including exploration.
4. **Sol designs when judgment is material.** Use direct-spawn Sol MAX for bounded work that must create, compare, or iteratively refine material visual, interaction, or information-design decisions. Frontend file ownership alone is not a routing signal.
5. **Sol reviews independently.** If independent review is warranted, use a fresh direct-spawn Sol XHIGH that did not implement the candidate.
6. **Fresh context by default.** Prefer self-contained packets with `fork_turns: "none"`.
7. **Prefer useful parallelism.** When multiple bounded tasks are independent, launch them concurrently. Main chooses the natural fleet size; there is no fixed fan-out. Parallel writes require disjoint scopes and stable interfaces.
8. **Verify the actual tree.** Worker claims never replace inspection, tests, or diff review.
9. **Preserve review continuity within a stable boundary.** Spawn a fresh Sol for the initial review, then reuse that same reviewer for re-review while user intent, acceptance, and substantive design remain stable. Main owns every finding and boundary decision.
10. **Preserve user work.** Never discard, overwrite, or misattribute pre-existing changes.
11. **Keep simple work simple.** Delegation and review are tools, not mandatory phases. Coordination/integration overhead can justify staying in Main; Luna token cost alone cannot.

## 4. Why no Terra default

Axiom does not map “exploration” to Terra. Luna MAX is the default bounded worker for exploration, implementation, tests, debugging, and mechanical refactors. Sol MAX is the deliberate exception for bounded design-sensitive work; another model is selected only for a concrete task-specific reason or an explicit user request.

Main Sol handles substantive ambiguity instead of delegating that ambiguity to a permanent intermediate orchestrator.

## 5. Design-sensitive routing

The decision boundary is unresolved interface judgment, not frontend technology. Sol MAX is used when a bounded task must materially choose or iteratively refine visual hierarchy, layout, typography, color, interaction, navigation, responsive behavior, information architecture, or usability-affecting component composition.

If a finished design, explicit tokens and dimensions, or settled behavior makes the remaining change mechanical, Luna MAX remains the preferred worker even when the task edits CSS, HTML, JSX, TSX, templates, or UI components.

A Sol MAX design worker may implement its design when separating design from code would damage the feedback loop. Once the design stabilizes, Main may split repetitive expansion, non-visual wiring, tests, and cleanup to Luna. Mixed tasks may run a Design Sol lane beside disjoint Luna lanes when ownership is safe.

The Design Sol is an implementation participant. It is never reused as the fresh independent Sol XHIGH reviewer.

## 6. Parallel Luna fleet policy

Luna MAX is cheap enough that Axiom lowers the threshold for useful fan-out. The explicit v0.1.4 assumption remains unchanged in v0.1.8: ordinary Luna worker compute is treated as almost free, so Luna usage itself is not a meaningful reason to serialize or retain bounded work in Main.

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

## 7. Why direct spawn only

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

## 8. Automatic use

Axiom has one broad but focused skill. Its description covers non-trivial software engineering tasks, while `allow_implicit_invocation: true` explicitly permits automatic selection.

It must not announce an “Axiom mode,” require route labels, or pause for activation. The user should experience normal Codex behavior with better delegation and review decisions.

## 9. Review policy

Review is risk-based; reviewer identity is fixed.

- trivial/non-behavioral change: Main verification may be enough
- meaningful behavioral change: fresh Sol XHIGH review strongly preferred
- security, auth, persistence, migration, concurrency, public API, broad refactor: fresh Sol XHIGH review expected

The initial reviewer is fresh and independent from Luna implementation workers and Sol design workers. The same reviewer agent is then reused for re-review so finding IDs, prior evidence, and Main adjudications remain in context while the review boundary is materially stable. A material change to user intent, acceptance, non-goals, architecture, or risk policy is a judgment point: Main may re-adjudicate in place, reset the boundary explicitly, or begin a fresh review cycle. This is not an automatic workflow transition.

Reviewers provide evidence; they do not set user risk tolerance or product policy. Main preserves concrete correctness, safety, and requirement evidence while deciding which mitigations fit the user's accepted intent. Axiom imposes no fixed finding count or review-round limit.

## 10. Evidence-aware operation

Axiom favors monitoring that returns on meaningful activity for long-running agents and processes, but it does not prescribe a universal polling interval. Main may shorten cadence for safety, cancellation, liveness, or external-state risks. Similarly, overlapping Main/worker inspection is evaluated by whether it adds integration, verification, or independent challenge rather than prohibited as a duplicate lane.

Optional rollout metrics and qualitative trace evals make these patterns visible. They provide evidence for Main and maintainers; they are not an orchestration gate or persistent runtime state.

## 11. Non-goals

Axiom is not:

- a project-management workflow
- a planner approval system
- a persistent runtime state machine
- a custom-agent installer
- a commit generator
- a substitute for deterministic tests
- a fixed-size agent fleet
- a promise that more agents always improve results
