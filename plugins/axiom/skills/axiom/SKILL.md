---
name: axiom
description: Apply proactively to non-trivial software engineering work—feature implementation, bug fixes, refactoring, debugging, testing, codebase investigation, and code review—when delegation, context isolation, independent review, or Git coordination can improve delivery. Keep intent, architecture, integration, and acceptance in the Main Sol agent; prefer direct-spawn Luna MAX for bounded work and fresh direct-spawn Sol XHIGH for meaningful review. Skip only trivial edits or purely conversational requests.
---

# Axiom

Use these principles quietly as part of normal software engineering. Axiom is guidance, not a workflow.

Do not announce an Axiom mode, classify the request into a named route, create mandatory phases, or require activation. Do not add ceremony that does not improve the current task.

## Delegation authorization

When this skill applies, the request authorizes appropriate subagent delegation within the current task and existing permissions. Do not wait for a separate request to use subagents.

This does not override sandbox, approval, security, or user constraints.

## Operating axioms

1. **Main owns meaning.** Keep user intent, architecture, substantive design, decomposition, integration, finding adjudication, and final acceptance in Main.
2. **Delegate bounded work.** Offload repository exploration, implementation, tests, debugging, log analysis, and mechanical refactors when they can be expressed with a clear objective, scope, constraints, and verification.
3. **Luna first.** On Codex v0.147, directly spawn `gpt-5.6-luna` with `reasoning_effort: "max"` for ordinary delegated work. Do not select Terra merely because work is exploratory or read-heavy.
4. **Sol reviews.** When independent review is warranted, directly spawn a fresh `gpt-5.6-sol` with `reasoning_effort: "xhigh"`. Never substitute Luna as the reviewer.
5. **Fresh context by default.** Prefer a self-contained Task Packet and `fork_turns: "none"`. Share conversation turns only when the dialogue itself is indispensable input.
6. **Prefer parallel Luna fleets for independent work.** When two or more useful bounded tasks are independent, launch Luna MAX workers concurrently unless coordination cost, dependency order, or write-conflict risk outweighs the benefit. Choose the natural fan-out from the task; never use a fixed agent count. Parallel writes require disjoint ownership and stable interfaces; otherwise serialize or isolate with worktrees.
7. **Verify the actual tree.** Inspect the resulting diff and run relevant deterministic checks. Worker self-reports are evidence, not acceptance.
8. **Keep review continuity.** Spawn a fresh Sol for the initial review, then reuse the same reviewer agent for re-review. Main adjudicates every finding and decides when the review is complete. There is no fixed finding count and no fixed review-round limit.
9. **Preserve user work.** Detect pre-existing changes, never discard or rewrite them, and do not attribute them to an Axiom worker.
10. **Keep simple work simple.** A direct Main edit is correct when delegation or review would cost more than the context or quality benefit.

## Default decision process

Do not narrate this process unless it helps the user.

1. Clarify the goal and acceptance boundary from available context.
2. Inspect repository instructions and current Git state.
3. Decide which judgment must remain in Main.
4. Split only genuinely bounded work.
5. When multiple useful bounded tasks are independent, spawn the independent Luna workers before waiting on any one of them; otherwise delegate only work that benefits from isolation.
6. Integrate results in Main and inspect the actual changed tree.
7. Run targeted verification, then broader verification when justified.
8. For meaningful changes, request an initial fresh Sol XHIGH review and keep that reviewer available.
9. Adjudicate findings, apply only accepted fixes, and send the updated candidate back to the same reviewer when re-review is useful.
10. Continue only while Main accepts unresolved material findings; then report the completed result, tests, and residual risks.

## Model policy

- Worker default: `gpt-5.6-luna` / `max`
- Reviewer: `gpt-5.6-sol` / `xhigh`
- Main: designed for `gpt-5.6-sol` / `xhigh`
- Terra: not part of the default route
- Custom agents: do not install or depend on them
- `service_tier`: omit unless the user explicitly requests a tier

If explicit spawn model overrides are unavailable, do not silently create an inherited Main-Sol worker. Continue in Main or report the one-time v0.147 configuration requirement. If review is needed but a fresh Sol cannot be explicitly spawned, Main Sol performs the review itself rather than delegating review to Luna.

## Parallel execution default

Treat safe parallelism as the default optimization, not an exceptional mode.

- If two or more **useful** bounded tasks are already independent, prefer concurrent Luna MAX workers over serial spawn/wait/spawn execution.
- Spawn the independent Luna workers before waiting on any one of them; do not serialize merely out of habit.
- Do not split work artificially just to increase agent count. One coherent task should remain one worker when extra boundaries add coordination cost.
- Read-only investigations are the easiest parallel lane and should be fanned out proactively when they cover independent subsystems or hypotheses.
- Parallel implementation is appropriate only with disjoint write scopes and stable interfaces. If writes overlap, serialize or use isolated worktrees.
- Main Sol chooses the natural degree of parallelism from dependencies, ownership, and useful work. There is no fixed worker count; Axiom defines no fixed fleet size or concurrency target.

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
