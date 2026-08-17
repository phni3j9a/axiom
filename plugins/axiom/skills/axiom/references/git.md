# Git coordination

## Commit principle

Do not enforce one task = one commit. Prefer commits that are coherent, independently understandable, and useful to review or revert.

A small feature may reasonably be one commit even if several worker subtasks contributed. A larger change may deserve separate commits for a migration, implementation, and cleanup when those boundaries make the history safer or clearer.

Do not create commits unless the user/project workflow expects the agent to do so.

## Dirty working tree

Before delegating writes, Main should understand pre-existing user changes well enough not to overwrite them. Workers must preserve unrelated edits and avoid broad cleanup outside their ownership.

Never reset, clean, checkout away, or otherwise discard existing changes merely to make delegation easier unless the user explicitly authorizes it.

## Parallel writes

Parallel write delegation is appropriate only when logical ownership is disjoint.

Safe patterns include:

- separate packages/modules with no shared generated files;
- independent test fixtures plus implementation areas that do not collide;
- separate Git worktrees for genuinely independent branches of work.

Unsafe patterns include:

- multiple workers editing the same central config/index/schema;
- one worker refactoring an interface while another implements against the old shape;
- parallel dependency or lockfile changes without explicit coordination.

When ownership becomes ambiguous, serialize the writes.

## Worktrees

Use worktrees when true parallel implementation would otherwise create merge/index contention and the integration value justifies the overhead. Worktrees are a tool, not a mandatory Axiom phase.

Main remains responsible for integration and for resolving semantic conflicts even when Git can merge text automatically.

## Review identity

A reviewer should inspect the exact current diff it is being asked to judge. If the implementation changes after Round 1, Round 2 reviews the updated diff only for frozen accepted findings and directly-caused major regressions, as described in `review.md`.
