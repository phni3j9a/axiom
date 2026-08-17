# Fresh Sol review and convergence

## Reviewer identity

When Axiom calls for independent review, the reviewer is a freshly direct-spawned `gpt-5.6-sol` at `xhigh` reasoning effort. Do not use the Luna implementer as its own independent reviewer and do not route review to Terra.

A direct-spawn reviewer does not have a custom read-only sandbox profile. Therefore enforce **behavioral read-only review** in the prompt and verify repository state in Main before/after review. The reviewer must not edit files, apply patches, commit, install dependencies, or run commands that intentionally mutate the working tree.

## When to review

Fresh Sol review is normally worth the cost when any of these are true:

- Luna changed meaningful production behavior;
- auth, security, privacy, permissions, crypto, or trust boundaries changed;
- persistence, schema, migration, or destructive data behavior changed;
- concurrency, async ordering, caching, or lifecycle behavior changed;
- a public API/interface changed;
- a refactor has meaningful blast radius;
- the change is difficult to validate deterministically;
- Main has material uncertainty after inspecting the diff.

Review may be skipped for read-only investigation, docs-only changes, trivial mechanical changes, or tiny low-risk edits directly verified by Main.

## Review packet

Give the fresh Sol reviewer a self-contained packet containing:

- **INTENT** — what the change is supposed to accomplish;
- **SCOPE** — actual diff/range/files to inspect;
- **ACCEPTANCE** — behavior that must hold;
- **VERIFICATION EVIDENCE** — tests/checks already run and their results;
- **FOCUS** — specific high-risk areas when known;
- **READ-ONLY RULE** — do not mutate repository or artifacts.

Ask the reviewer to inspect the actual implementation, not just the worker summary.

## Reviewer output

Prefer a compact verdict:

```text
VERDICT: SHIP | FIX_FIRST | RETHINK

FINDINGS:
- F1 | critical|major | file:line | issue | impact | evidence | fix intent
- F2 | ...
```

Limit Round 1 to the most important actionable findings, normally no more than five. Ignore pure style/preferences unless they hide a correctness, security, maintenance, or regression risk.

`RETHINK` means the current design/approach is materially wrong; return architecture ownership to Main rather than asking the reviewer to redesign and implement it.

## Main adjudication

Main judges every Round-1 finding:

- **ACCEPT** — valid and required before completion;
- **DEFER** — valid but outside the current acceptance boundary or not worth immediate change;
- **REJECT** — incorrect, irrelevant, already covered, or not supported by evidence.

Only accepted findings are sent for correction. Reviewer findings are advice, not authority.

## Finding Freeze

After Main adjudicates Round 1, freeze the finding set.

If accepted findings require code changes, the implementer (usually Luna) applies only those corrections plus necessary directly-caused adjustments. Main reruns verification and inspects the resulting diff.

Round 2 is a **verification review**, not a fresh hunt for more improvements. Ask fresh Sol to check:

1. whether each accepted frozen finding is actually resolved;
2. whether those fixes introduced a **critical or major regression directly caused by the fix**.

Do not add new general findings in Round 2. Do not reopen rejected/deferred items. If an unrelated possible improvement is noticed, omit it unless it is critical enough that shipping would be unsafe.

Two review rounds are the default ceiling. If a required finding remains unresolved after Round 2, Main decides the next engineering action or asks the user when a product/design decision is required; do not enter an automatic review-fix loop.

## Mutation guard for direct-spawn reviewers

Because the reviewer is not backed by a custom read-only agent profile:

- Main should note the pre-review repository state (`git status --short` and relevant diff identity when useful).
- The reviewer prompt must explicitly forbid writes.
- Main checks state again after review.
- Any unexpected reviewer mutation invalidates the verdict until Main understands and resolves that mutation.
