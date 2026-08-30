# Axiom Rollout Trace Evals

These evals use Codex rollout JSONL as evidence about orchestration behavior. They are diagnostic, not gates: no single count, timeout, compaction, or communication pattern is automatically good or bad.

## Read-only metrics

The optional `plugins/axiom/skills/axiom/scripts/audit_rollout.py` script reads one or more rollout JSONL files and emits deterministic JSON metrics. It does not modify sessions, repositories, or Codex state.

Useful signals include:

- session and agent lineage;
- first recorded model and reasoning effort;
- task starts, completed turns, aborted turns, and compactions;
- collaboration call counts;
- wait timeout distribution;
- open-turn balance.

Interpret these signals with the task context. An open turn may simply be active, a short wait may be required for cancellation or safety, and a compaction may be reasonable for a large task.

## Qualitative scenarios

### Long-running work

Look for repeated Main wakeups when no new evidence was expected. Ask whether an event-driven wait, runner heartbeat, resource limit, or cleanup contract could have carried the monitoring instead. Do not apply a universal polling interval; safety, cancellation, liveness, and external state may justify shorter cadence.

### Review-boundary change

When the user changes acceptance, non-goals, substantive design, or risk tolerance, inspect whether Main re-adjudicated earlier findings. Continuing with the same reviewer may be correct, an explicit boundary reset may be enough, or a fresh review cycle may restore independence. The eval checks that Main noticed and judged the change, not that it selected a prescribed route.

### Reviewer authority

Inspect whether material findings were tied to independent current evidence rather than hypothetical hardening, candidate-created machinery, or a prior reviewer suggestion. The reviewer supplies evidence; Main adjudicates it against the user's accepted intent. Concrete safety, correctness, requirement, and unjustified-complexity evidence must remain visible even when a mitigation is rejected. Optional hardening should not enter `FINDINGS` merely because it could reduce an unspecified future risk.

### Complexity ratchet

Inspect a bounded change across initial review, accepted fixes, and re-review. Look for follow-on findings whose only basis is machinery introduced by the previous fix—for example retry state leading to persistence, persistence leading to migration, or a compatibility shim leading to another compatibility obligation. Such chains need independent current evidence; the existence of the new mechanism is not enough. At the same time, Finding Freeze must not hide a concrete material correctness, security, data-integrity, trust-boundary, or compatibility defect that new independent evidence reveals during re-review, even when the initial review missed it and the accepted fix did not cause it. The distinction is concrete evidenced defect versus speculative follow-on hardening, not old finding versus new finding.

### Subtractive review

When the candidate introduces state, abstraction, fallback, retry, migration, scheduling, reconciliation, configuration, or dependencies that are not justified by the current contract, inspect whether review considers removing that machinery instead of adding protection around it. The eval is qualitative: extra mechanisms may be correct when independently justified. The desired signal is that complexity is treated as a liability requiring evidence, not that fewer lines or files are automatically better.

### Lifecycle interpretation

Check that a child-turn `task_complete` was not treated as proof that the reusable agent session was terminal or that Main accepted the work. Acceptance should rest on the relevant diff, artifacts, scope, and verification.

### Main and worker overlap

Overlapping inspection is not a failure by itself. Ask whether Main added integration judgment, targeted verification, or independent challenge, or merely recreated broad exploration already delegated to a worker.

### Communication and compaction

High message or compaction counts are prompts for inspection, not release blockers. Consider whether communication preserved a material decision or instead streamed unchanged status and raw output back into Main context.

## Example

```bash
python3 plugins/axiom/skills/axiom/scripts/audit_rollout.py \
  ~/.codex/sessions/2026/08/21/rollout-example.jsonl
```

Use the resulting metrics alongside the actual conversation, repository state, and user steering. The script cannot infer whether a risk trade-off or overlapping inspection was justified.
