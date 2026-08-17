# Git coordination

## Preserve the user's working tree

Before editing or delegating writes, inspect enough Git state to distinguish task work from pre-existing user work. Commonly useful commands include:

```bash
git status --short
git branch --show-current
```

Inspect staged/unstaged diffs when they matter to the task.

Hard safety rules:

- do not reset, clean, checkout, restore, or otherwise discard pre-existing user changes;
- do not rewrite history without applicable authorization;
- do not stash user changes merely to make the tree look clean;
- do not claim pre-existing changes as worker output.

## Commit ownership

In a shared working tree, **prefer** Main-owned integration and commits because Main sees the combined candidate and user intent.

Worker commits can still be useful when Main deliberately chooses them—for example, in an isolated worktree/branch with a clean semantic boundary. Commit ownership is therefore a coordination choice, not a hard Axiom rule.

Do not force `one task = one commit`.

Prefer semantic commit boundaries that make the change understandable and verifiable. Several worker tasks may belong in one coherent commit; one worker task may justify multiple commits when there are genuinely independent boundaries.

## Parallel writes

Prefer disjoint ownership for parallel writes. When scopes overlap, explicitly weigh:

- expected speedup;
- conflict probability;
- shared interfaces or generated files;
- lockfile/schema/migration ordering;
- cost of worktree setup and integration.

Serialization or separate worktrees are often safer when overlap is high. Same-file parallel edits are usually a poor tradeoff, but Axiom does not impose a blanket prohibition when Main has a concrete integration strategy.

## Review boundary

Review the candidate that Main actually intends to accept, not merely the most recent worker patch.

When the tree contains pre-existing user changes:

- establish a baseline when practical;
- tell reviewer which paths/hunks belong to the task when that distinction matters;
- avoid exposing unrelated sensitive diffs unnecessarily;
- verify that accepted fixes did not overwrite user work.

## Final integration checks

Use the Git evidence appropriate to the repository and task. Commonly useful checks include:

```bash
git status --short
git diff --check
git diff
git diff --cached
```

Not every command is mandatory on every task. Main should inspect enough state to confirm that the accepted candidate contains no accidental changes, unresolved conflicts, or unsafe additions and that commit state matches the user's request.

## Destructive operations

Destructive or history-changing operations require explicit justification and any applicable user approval. Axiom never treats delegation as permission to bypass Git safety.
