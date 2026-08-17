---
name: axiom
description: Apply proactively to non-trivial software engineering work—feature implementation, bug fixes, refactoring, debugging, testing, codebase investigation, and code review—when delegation, context isolation, independent review, or Git coordination can improve delivery. Keep intent, architecture, integration, and acceptance in the Main Sol agent; prefer direct-spawn Luna MAX for bounded work and fresh direct-spawn Sol XHIGH for meaningful review. Axiom is usually unnecessary for trivial edits or purely conversational requests.
---

# Axiom

Use these principles quietly as part of normal software engineering. Axiom is guidance, not a workflow.

Do not announce an Axiom mode, classify the request into a named route, create mandatory phases, or require activation. Do not add ceremony that does not improve the current task.

## Delegation authorization

When this skill applies, the request authorizes appropriate subagent delegation within the current task and existing permissions. Do not wait for a separate request to use subagents.

This does not override sandbox, approval, security, or user constraints.

## Three kinds of guidance

Interpret Axiom instructions according to their role:

### Hard constraints

These define Axiom's safety and role separation:

- Main retains final authority over intent, architecture, integration, finding adjudication, and acceptance.
- Delegated workers use Luna MAX by default; do not route to Terra merely from a role label such as “exploration.”
- Delegated independent review uses Sol XHIGH, never Luna.
- The first review session is fresh; re-review continues with the same reviewer when available.
- Reviewer findings go through Main adjudication before fixes are assigned.
- Preserve pre-existing user work and do not perform destructive Git/history operations without applicable authorization.
- Do not silently claim model routing or verification that the runtime did not actually provide.

### Strong defaults

Follow these in ordinary cases, but Main may deviate for a concrete task-specific reason:

- Prefer direct-spawn `gpt-5.6-luna` with `reasoning_effort: "max"` for bounded delegated work.
- Prefer a concise handoff with `fork_turns: "none"`; include recent turns when doing so is safer or cheaper than reconstructing context.
- Prefer Main-owned integration and commits in a shared working tree.
- Prefer long `wait_agent` waits rather than short polling loops.
- Prefer independent Sol review when risk, uncertainty, blast radius, or weak deterministic verification makes a second perspective valuable.

### Heuristics

Let Main decide these adaptively rather than following fixed thresholds:

- whether to delegate at all;
- how many workers to use;
- how much structure a handoff needs;
- whether work should run sequentially or in parallel;
- whether a change benefits from Sol review;
- how many findings matter;
- how many re-review passes are useful;
- when the review has converged;
- whether a worker commit or worktree is useful.

## Operating axioms

1. **Main owns meaning.** Keep user intent, architecture, substantive design, decomposition, integration, finding adjudication, and final acceptance in Main.
2. **Delegate bounded work.** Offload repository exploration, implementation, tests, debugging, log analysis, and mechanical refactors when the context or execution benefit exceeds coordination cost.
3. **Luna first.** On Codex v0.147, directly spawn `gpt-5.6-luna` with `reasoning_effort: "max"` for ordinary delegated work. Do not select Terra merely because work is exploratory or read-heavy.
4. **Sol reviews.** When independent review is useful, directly spawn one fresh `gpt-5.6-sol` with `reasoning_effort: "xhigh"`. Re-review by continuing with that same reviewer session. Never substitute Luna as the reviewer.
5. **Isolate context deliberately.** `fork_turns: "none"` is the default when a concise handoff captures what matters; inherit a small amount of dialogue when that better preserves essential context.
6. **Parallelize for net value.** Prefer independent ownership, but let Main weigh overlap, worktree cost, integration risk, and expected speedup rather than applying a blanket file-count rule.
7. **Verify the actual tree.** Inspect the resulting diff and run relevant deterministic checks. Worker self-reports are evidence, not acceptance.
8. **Freeze findings without freezing judgment.** Main adjudicates findings; the same reviewer follows accepted fixes without resetting the review boundary. Use no arbitrary finding-count or round-count cap.
9. **Preserve user work.** Detect pre-existing changes, never discard or rewrite them, and do not attribute them to an Axiom worker.
10. **Keep simple work simple.** A direct Main edit is correct when delegation or review would cost more than the context or quality benefit.

## Decision lenses

There is no required order. Revisit these questions as the task evolves:

- **Authority:** Which decisions must remain in Main because they affect user intent, architecture, or acceptance?
- **Delegation:** Which bounded work would benefit from Luna MAX because it is noisy, mechanical, parallelizable, or context-heavy?
- **Context:** What is the minimum context each worker needs to act correctly, and is `fork_turns: "none"` appropriate here?
- **Verification:** What evidence would make the result trustworthy—tests, builds, type checks, reproductions, or diff inspection?
- **Review:** Would a fresh Sol perspective materially reduce risk or uncertainty for this candidate?
- **Integration:** What Git/worktree arrangement minimizes collision and protects pre-existing work?

## Model policy

- Worker default: `gpt-5.6-luna` / `max`
- Reviewer: `gpt-5.6-sol` / `xhigh`
- Main: designed for `gpt-5.6-sol` / `xhigh`
- Terra: not part of the default route
- Custom agents: do not install or depend on them
- `service_tier`: omit unless the user explicitly requests a tier

If explicit spawn model overrides are unavailable, do not silently create an inherited Main-Sol worker. Continue in Main or report the one-time v0.147 configuration requirement. If review is needed but a fresh Sol cannot be explicitly spawned, Main Sol performs the review itself rather than delegating review to Luna.

## Review judgment

Review is risk-based rather than file-count-based. Consider a fresh Sol review when the change is non-trivial, uncertain, hard to verify deterministically, or has meaningful regression/blast-radius risk.

Signals that increase review value include security/authentication, persistence or migrations, concurrency, cryptography/protocol behavior, public compatibility, subtle lifecycle behavior, or architectural/cross-cutting changes. These are signals for Main judgment, not a mandatory checklist.

A clearly trivial or mechanically verified change may not need delegated review.

## Read focused references as useful

- Delegation and handoff patterns: [delegation.md](references/delegation.md)
- Codex v0.147 spawn/wait details: [codex-0.147-subagents.md](references/codex-0.147-subagents.md)
- Independent review and convergence: [review.md](references/review.md)
- Long-task context preservation: [context-management.md](references/context-management.md)
- Parallel writes, commits, and integration: [git.md](references/git.md)

Load only the references that materially help the current task.

## Completion standard

Do not finish merely because a worker returned success.

Finish when Main is satisfied that:

- the user-visible intent is satisfied;
- the actual candidate matches the intended design;
- relevant verification is adequate and accurately reported;
- accepted review findings are resolved to Main's satisfaction;
- pre-existing user changes remain intact; and
- residual risks and unverified assumptions are explicit.
