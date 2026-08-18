# Delegation

## Purpose

Use delegation to protect Main context and gain useful parallelism, not to maximize agent count.

Main retains architecture, intent, trade-offs, integration, and acceptance. Luna receives bounded work whose delegation benefit exceeds coordination and integration cost.

## Economics assumption

Under the Codex/model economics targeted by Axiom v0.1.4, Luna MAX worker usage is inexpensive enough to be treated as **almost free** for ordinary orchestration decisions.

This means Main should not suppress useful delegation merely to conserve Luna tokens or model usage. When a bounded spawn protects Main context, absorbs noisy exploration, separates an independent investigation, or creates useful parallel progress, Luna usage cost should normally be treated as negligible.

The meaningful costs of a spawn are instead:

- coordination and handoff overhead;
- latency and dependency ordering;
- overlapping or conflicting work;
- integration and verification burden;
- ambiguity that requires Main judgment.

**Main context is expensive; Luna compute is almost free.** This is a versioned Axiom assumption and should be revised if model economics materially change.

## Signals that favor delegation

A Luna MAX worker often helps when:

- repository exploration would touch many files or produce noisy notes;
- logs, test output, compiler errors, or generated diagnostics would pollute Main context;
- a change has a useful ownership boundary;
- an implementation, test, or investigation can make progress without inventing unresolved architecture;
- repetitive or mechanical work would consume substantial Main context;
- independent investigations can run concurrently;
- Main mainly needs evidence, a file map, or a concise recommendation rather than the raw search process.

Do not keep such work in Main merely to save Luna usage.

## Signals that favor staying in Main

Main may keep work local when:

- the edit is obvious and local;
- the request is primarily explanation rather than repository work;
- architecture or product intent is still unresolved;
- the worker would require continuous back-and-forth;
- delegation would save little context or time while adding coordination/integration overhead;
- the only reason to spawn is to satisfy a ritual.

These are heuristics, not routing rules. Luna's token cost by itself is not a reason to stay in Main.

## Scale the handoff to the task

Give a worker enough context to act correctly. Prefer a self-contained handoff, but do not force a full schema for a small bounded task.

### Minimal handoff

Useful for a simple investigation or tightly scoped edit:

```text
GOAL
- Find why refresh tokens are rejected after rotation.

SCOPE
- Inspect auth/token modules and related tests.
- READ-ONLY for this investigation.

RETURN
- Root-cause evidence with file/symbol references.
- Recommended next step.
```

### Rich handoff

Add structure as complexity, risk, or write scope grows:

```text
OBJECTIVE
- Concrete outcome.

WHY / CONTEXT
- Decisions and facts needed to do the work.

FILES / OWNERSHIP
- Likely areas to inspect.
- Intended write boundary or READ-ONLY expectation.
- Pre-existing changes that must be preserved.

INTERFACES / INVARIANTS
- APIs, types, schemas, commands, or behavior that should remain compatible.

CONSTRAINTS / NON-GOALS
- Design choices already made by Main.
- Important repository instructions.

ACCEPTANCE
- Observable conditions that define success.

VERIFICATION
- Targeted checks or evidence that would be useful.

RETURN
- Concise result, changed files when applicable, verification evidence, and unresolved risks.
```

Use only the fields that improve correctness for the current task.

## Worker guidance

Useful defaults for a worker:

- stay aligned with the assigned objective and intended ownership;
- inspect relevant repository instructions before editing;
- preserve unrelated and pre-existing changes;
- avoid destructive Git/history operations;
- surface substantive architecture or product ambiguity back to Main rather than silently redefining intent;
- report verification actually performed, not verification merely intended;
- return concise evidence rather than raw transcripts.

In a shared working tree, Main-owned commits are usually simpler. In an isolated worktree or clearly bounded branch, Main may deliberately delegate commit creation when it improves integration.

Further subdelegation is not a goal by itself. Let the active agent use it only when the runtime supports it and it produces clear net value without obscuring Main's authority.

## Direct-spawn default

For Codex v0.147, prefer:

```text
model = "gpt-5.6-luna"
reasoning_effort = "max"
fork_turns = "none"
```

A small recent-turn fork can be reasonable when it preserves essential context more reliably than rewriting that context into the message.

See [codex-0.147-subagents.md](codex-0.147-subagents.md) for the exact surface and fail-closed behavior.

## Parallel delegation

Parallelize when expected speed/context benefit exceeds coordination and integration cost. Do not include Luna token conservation as a meaningful limiter under this version's economics assumption.

Especially good candidates:

- read-only searches of separate subsystems;
- tests or analyses of separate packages;
- implementation in disjoint modules with stable interfaces;
- competing hypotheses that can be investigated independently.

When writes overlap, Main should explicitly account for conflict and integration cost. Serialization or isolated worktrees are often safer; overlapping writes are not categorically forbidden if Main has a concrete integration strategy.

## Result compression

Workers should return evidence and conclusions, not transcripts.

A compact result might look like:

```text
RESULT: COMPLETE
SUMMARY: Added cache invalidation on update and delete.
CHANGED: src/cache.ts, tests/cache.test.ts
VERIFICATION: npm test -- cache.test.ts — pass (18 tests)
RISKS: distributed invalidation remains outside scope
```

Main may request more raw evidence when a claim is surprising, disputed, or high impact.
