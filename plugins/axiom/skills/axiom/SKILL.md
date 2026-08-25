---
name: axiom
description: Apply proactively to non-trivial software engineering work—feature implementation, bug fixes, refactoring, debugging, testing, codebase investigation, interface design, and code review—when delegation, context isolation, independent review, or Git coordination can improve delivery. Keep intent, architecture, design constraints, integration, and acceptance in the Main Sol agent; prefer direct-spawn Luna MAX for ordinary bounded work, Sol MAX for bounded design-sensitive work, and fresh direct-spawn Sol XHIGH for meaningful review. Skip only trivial edits or purely conversational requests.
---

# Axiom

Use these principles quietly as part of normal software engineering. Axiom is guidance, not a workflow.

Do not announce an Axiom mode, classify the request into a named route, create mandatory phases, or require activation. Do not add ceremony that does not improve the current task.

## Delegation authorization

When this skill applies, the request authorizes appropriate subagent delegation within the current task and existing permissions. Do not wait for a separate request to use subagents.

This does not override sandbox, approval, security, or user constraints.

## Luna economics

Under the current Codex/model economics preserved by Axiom v0.1.8, Luna MAX is so inexpensive that ordinary worker usage can be treated as **almost free** for orchestration decisions. This keeps the v0.1.4 economics principle unchanged.

**Main context is expensive; Luna compute is almost free.** Protect Main Sol context aggressively when bounded work can be delegated cleanly.

Do not avoid a useful Luna spawn merely to conserve Luna tokens or model usage. When delegation can protect Main context, isolate noisy work, investigate independently, or make useful parallel progress, prefer spawning Luna. The practical costs that should limit delegation are coordination, latency, overlapping work, dependency order, and integration complexity—not Luna MAX usage itself.

This is an explicit economics assumption of this Axiom version, not a timeless claim about model pricing. If Codex/model economics change materially, update this policy.

## Operating axioms

1. **Main owns meaning.** Keep user intent, architecture, design constraints and direction, decomposition, integration, finding adjudication, and final acceptance in Main.
2. **Delegate bounded work proactively.** Offload repository exploration, implementation, tests, debugging, log analysis, and mechanical refactors when they can be expressed with a clear objective, scope, constraints, and verification. Do not keep bounded work in Main merely to save Luna usage.
3. **Luna first for ordinary work.** On Codex v0.147, directly spawn `gpt-5.6-luna` with `reasoning_effort: "max"` for ordinary delegated work. Do not select Terra merely because work is exploratory or read-heavy.
4. **Sol designs when judgment is material.** Directly spawn `gpt-5.6-sol` with `reasoning_effort: "max"` when a bounded task must create, compare, or iteratively refine material visual, interaction, or information-design decisions. Do not route work to Sol merely because it touches frontend files. When the relevant design decisions are already specified, prefer Luna MAX for the remaining bounded implementation.
5. **Sol reviews.** When independent review is warranted, directly spawn a fresh `gpt-5.6-sol` with `reasoning_effort: "xhigh"`. Never substitute Luna as the reviewer, and never reuse a design worker as the independent reviewer.
6. **Fresh context by default.** Prefer a self-contained Task Packet and `fork_turns: "none"`. Share conversation turns only when the dialogue itself is indispensable input.
7. **Prefer parallel Luna fleets for independent work.** When two or more useful bounded tasks are independent, launch Luna MAX workers concurrently unless coordination cost, dependency order, or write-conflict risk outweighs the benefit. Choose the natural fan-out from the task; never use a fixed agent count. Parallel writes require disjoint ownership and stable interfaces; otherwise serialize or isolate with worktrees.
8. **Verify the actual tree.** Inspect the resulting diff and run relevant deterministic checks. Worker self-reports are evidence, not acceptance.
9. **Keep review continuity within a stable boundary.** Spawn a fresh Sol for the initial review, then reuse the same reviewer agent for re-review while user intent, acceptance, and substantive design remain stable. Main adjudicates every finding, decides whether a material boundary change warrants a reset, and decides when review is complete. There is no fixed finding count and no fixed review-round limit.
10. **Preserve user work.** Detect pre-existing changes, never discard or rewrite them, and do not attribute them to an Axiom worker.
11. **Keep simple work simple.** A direct Main edit is correct when coordination and integration overhead would exceed the context or quality benefit. Luna's token cost alone is not a reason to stay in Main.

## Default decision process

Do not narrate this process unless it helps the user.

1. Clarify the goal and acceptance boundary from available context.
2. Inspect repository instructions and current Git state.
3. Decide which judgment must remain in Main.
4. Identify whether any bounded task requires material visual, interaction, or information-design judgment; route that task to Sol MAX and ordinary bounded work to Luna MAX.
5. Split genuinely bounded work whenever doing so protects Main context or creates useful independent progress; do not optimize for minimizing Luna usage.
6. When multiple useful bounded tasks are independent, spawn them before waiting on any one of them; otherwise delegate work that benefits from isolation.
7. Integrate results in Main and inspect the actual changed tree.
8. Run targeted verification, then broader verification when justified.
9. For meaningful changes, request an initial fresh Sol XHIGH review that is independent from all implementation workers, and keep that reviewer available.
10. Adjudicate findings, apply only accepted fixes, and send the updated candidate back to the same reviewer when re-review is useful and the review boundary remains stable.
11. Continue only while Main accepts unresolved material findings; then report the completed result, tests, and residual risks.

## Model policy

- Worker default: `gpt-5.6-luna` / `max`
- Design worker: `gpt-5.6-sol` / `max`
- Reviewer: `gpt-5.6-sol` / `xhigh`
- Main: designed for `gpt-5.6-sol` / `xhigh`
- Terra: not part of the default route
- Custom agents: do not install or depend on them
- `service_tier`: omit unless the user explicitly requests a tier

If explicit spawn model overrides are unavailable, do not silently create an inherited Main-Sol worker. Continue in Main or report the one-time v0.147 configuration requirement. If design-sensitive work cannot be explicitly routed to Sol MAX, keep it in Main rather than silently assigning it to Luna. If review is needed but a fresh Sol cannot be explicitly spawned, Main Sol performs the review itself rather than delegating review to Luna.

Routing verification must use runtime/rollout evidence: the requested spawn args, the child `turn_context` model/effort, and the corresponding child-turn `task_complete`. A completed child turn is not by itself an accepted result or a terminal agent session. Never rely on a child's self-report alone.

## Parallel execution default

Treat safe parallelism as the default optimization, not an exceptional mode. Luna usage itself is almost free under this version's economics assumption, so size the fleet around useful independent work and integration constraints rather than token conservation.

- If two or more **useful** bounded tasks are already independent, prefer concurrent Luna MAX workers over serial spawn/wait/spawn execution.
- Spawn the independent Luna workers before waiting on any one of them; do not serialize merely out of habit.
- Do not split work artificially just to increase agent count. One coherent task should remain one worker when extra boundaries add coordination cost.
- Read-only investigations are the easiest parallel lane and should be fanned out proactively when they cover independent subsystems or hypotheses.
- Parallel implementation is appropriate only with disjoint write scopes and stable interfaces. If writes overlap, serialize or use isolated worktrees.
- Main Sol chooses the natural degree of parallelism from dependencies, ownership, useful work, latency, and integration cost. There is no fixed worker count; Axiom defines no fixed fleet size or concurrency target.

## Review threshold

A fresh Sol review is strongly preferred for any meaningful behavioral implementation, multi-file change, complex bug fix, or substantial refactor.

Treat review as expected for security, authentication, authorization, persistence, migration, concurrency, cryptography, public APIs, cross-platform behavior, or broad blast radius.

Main verification may be enough for a clearly trivial, non-behavioral edit.

## Read the focused references

- Before delegating: [delegation.md](references/delegation.md)
- Before a v0.147 spawn or when routing fails: [codex-0.147-subagents.md](references/codex-0.147-subagents.md)
- Before independent review or a fix loop: [review.md](references/review.md)
- When the task is long or compaction risk is material: [context-management.md](references/context-management.md)
- Before parallel writes, commits, rebases, or final integration: [git.md](references/git.md)

Read only the references relevant to the current task.

## Completion standard

Do not finish merely because a worker returned success.

Finish when:

- the user-visible intent is satisfied
- the actual diff matches the intended design
- relevant tests or checks pass, or their absence is clearly reported
- accepted review findings are resolved
- pre-existing user changes remain intact
- residual risks and unverified assumptions are explicit
