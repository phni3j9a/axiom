# Context management

## Goal

Keep Main context rich in intent and decisions, not raw execution noise.

## Keep in Main

Usually keep:

- user requirements and constraints;
- architecture and substantive design decisions;
- acceptance criteria and non-goals;
- decomposition/integration choices;
- review adjudication;
- final verification summary and residual risk.

## Delegate or compress

Good candidates for externalization include:

- broad repository searches;
- raw logs and stack traces;
- long compiler/test output;
- dependency inventories;
- generated-file inspection;
- repetitive edits;
- local implementation details that do not alter architecture;
- first-pass issue classification.

Workers should return concise evidence and conclusions rather than full transcripts unless raw evidence is actually needed.

## Handoff discipline

A handoff can be very small or richly structured. Include the context that materially affects correctness, such as objective, scope, constraints, acceptance, verification, or a return expectation. Do not add fields merely to satisfy a template.

Do not fork full conversation history merely because it is available.

`fork_turns: "none"` is the default when a concise handoff captures what matters. A positive turn count can be better when recent dialogue is compact and materially relevant. `"all"` can be appropriate when the broader conversation itself is important input; use it deliberately because it weakens context isolation.

Delegation does not prohibit Main from inspecting the same area. Main should prefer overlap that adds integration judgment, targeted verification, or an independent challenge rather than recreating broad exploration that a worker already owns. This is a context-cost heuristic, not an ownership rule.

## Evidence-aware waiting

For long-running agents or processes, prefer waits and monitoring that return on meaningful activity. Avoid repeatedly waking Main when no new evidence is expected. The right cadence depends on the task and may be shortened for safety, cancellation, liveness, or external-state risks.

User preferences about update cadence are part of the task context, subject to higher-level constraints. Internal monitoring and user-facing progress updates need not have the same cadence: a runner may enforce continuous safety checks while Main reports only meaningful state changes.

## Optional long-task anchor

Do not create state for ordinary work.

When compaction or session continuation is a material risk, Main may maintain one concise anchor under Git metadata:

```bash
git rev-parse --git-path axiom
```

Suggested file:

```text
<git-path axiom>/anchor.md
```

Possible contents:

```markdown
# Goal
# Acceptance criteria
# Decisions and rationale
# Non-goals
# Current integrated state
# Verification status
# Review adjudication that still matters
# Next action
# Open questions
```

Keep the anchor lightweight. It is an external memory aid, not a phase ledger or state machine. Never put secrets in it, and do not treat a model-generated compact summary as the sole source of truth for repository state.

## Worker result compression

A compact return often leads with status/conclusion, changed files when applicable, verification evidence, and risks/blockers. This is a useful shape, not a required output schema.

Request raw output when a disputed, surprising, or high-impact claim requires it.

## Main integration

Before accepting a worker conclusion, Main should inspect the relevant code, diff, or other evidence. Compression removes noise, not the need for evidence.
