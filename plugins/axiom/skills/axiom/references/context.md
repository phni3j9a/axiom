# Context isolation and long-horizon memory

## Protect Main context

The Main session should retain the information whose loss would change the solution:

- user intent and acceptance criteria;
- architecture and important design decisions;
- interface contracts;
- unresolved questions and tradeoffs;
- integration state and final verification judgment.

Push disposable detail outward when possible:

- broad code search output;
- long logs and stack traces;
- repetitive implementation steps;
- test output that can be summarized;
- dependency tracing;
- local worker scratch reasoning.

Ask subagents to return compact evidence and conclusions rather than replaying their full exploration transcript.

## Fresh task packets

Prefer `fork_turns: none` when a clear packet can carry the needed context. This keeps old conversational noise and unrelated decisions out of the worker.

Use a small recent-turn fork only when the recent dialogue itself is a material input and reconstructing it would be error-prone. Full-history forks are an exception, not the default.

## Task anchor

For a long task likely to survive one or more compactions, keep one small human-readable anchor in a project-appropriate scratch location chosen by Main/user. It is optional and must not become a workflow database.

Suggested shape:

```markdown
# Task Anchor

## Goal
...

## Acceptance criteria
- ...

## Decisions
- ...

## Non-goals
- ...

## Current status
...

## Next step
...

## Open questions
- ...
```

Update it only when a material decision/status changes. Do not log every action, spawn, test, or review event.

If the repository should remain untouched by agent metadata, place temporary notes outside the product tree or under a Git metadata/scratch location rather than adding a committed `.axiom/` directory.

## After compaction

Reconstruct intent from durable project artifacts, the task anchor, actual Git diff/history, and the user's latest instructions. Treat an auto-generated compacted conversation summary as useful context, not the sole source of truth.
