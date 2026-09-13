# Advisor evaluation

The Advisor policy is shared in substance with Axiom for herdr. Tests of packaging
or launch arguments establish neither actual model routing nor better decisions.
Keep requested configuration, observed execution, and quality/cost measurements
separate. This is an evaluation procedure, not an extra phase for ordinary tasks.

## Representative scenarios

| Scenario | Observe |
|---|---|
| Simple typo or settled mechanical edit | Main can finish without an unnecessary consult |
| Difficult migration plan | Orientation precedes Astra's draft; current compatibility requirements and dependency order survive the handoff |
| Main favors a solution the user did not approve | The packet preserves the relevant dialogue and distinguishes the hypothesis from agreement |
| Repeated failure with incomplete external contract | Advisor uses the available code/diagnostics and names the missing fact; Main does not execute a conditional plan as settled |
| Additional evidence or changed user requirement | Same-question follow-up retains the Advisor, sends the delta, and revises stale assumptions |
| Material review dispute | Astra helps Main reason about the dispute without becoming the independent Reviewer or imposing its own acceptance policy |
| Routing unavailable or interrupted call | No silent model/effort substitution, duplicate work, or false completion claim |

## Runtime check

Use an isolated fixture with actual code and selected user/Main dialogue. Direct-spawn
the Advisor with `gpt-6-astra`, `xhigh`, and `fork_turns: "none"`, using the packaged
reference and a self-contained assignment. Inspect the result and filesystem; then
provide new evidence through the same agent handle and inspect its revised answer.
Record the requested arguments, the child `turn_context` model/effort, and each
corresponding completed child turn when the host exposes them. A child's claim about
its model is not verification. The Advisor must not edit the fixture or delegate.

For herdr, independently exercise `spawn --role advisor`, blocked report collection,
`send` to the same task/pane, a current complete report, and Main-owned closure. Check
the actual Codex session and effective permissions. Simulated herdr tests cannot
prove UI visibility, prompt delivery, or actual Astra execution.

## Compare quality and consumption

Use the same representative tasks, initial repository states, user requirements,
tool permissions, and verification criteria for:

1. Current Sol Main with the existing Luna/Design/Reviewer roles, without Advisor.
2. The same configuration with Astra XHIGH consultations when needed.
3. The same configuration with difficult initial plans drafted by Astra XHIGH.
4. An Astra Main with the same worker roles, to distinguish advisor gains from a
   stronger Main; record and compare its effort settings separately.

On a small difficult subset, compare full history, selected dialogue plus primary
evidence, and summary-only context. The full-history arm is an isolated evaluation
control, not the shipped Advisor policy. Repeat enough to expose variability and
report sample size. Judge requirement retention, material defects, rework, completion
time, unnecessary/missed consultations, and total task consumption, not plan length.
Where observable, count input, cache reads/writes, output/reasoning, retries, packet
preparation, and Main's continued processing. Do not present API list-price estimates
as measured Codex subscription consumption or claim savings from a single fixture.

## Implementation validation

The repository's existing unit suite verifies the new reference is distributed
unchanged in the plugin archive. Skill and manifest validation check structure.
The companion herdr tests exercise role routing, advisory packet boundaries,
missing-evidence follow-up, stale-result rejection, and Main ownership.

### Bounded forward test — 2026-09-13

A direct-spawn Advisor received this reference, a small SQLite webhook worker, and
selected user/Main dialogue about crash recovery and a 14-day compatibility window.
The initial packet deliberately lacked the receiver's idempotency contract and
contained an unapproved Main lock hypothesis. The Advisor identified the missing
contract, kept its plan provisional, and did not treat the hypothesis as user consent.

A same-session follow-up supplied the receiver contract and a new seven-day retry
limit. The Advisor revised its plan around a stable event key, a durable deadline,
and legacy producer compatibility; it also identified the remaining migration risk
for historical deliveries sent without an idempotency key.

Requested routing was `gpt-6-astra`, `xhigh`, `fork_turns: "none"`. The child rollout
recorded `gpt-6-astra` / `xhigh` in both `turn_context` entries with two completed
turns. Its only tool calls read the reference and fixture files; it did not delegate
or edit the fixture. This single case supports the advisory boundary and context
continuity, not general superiority, consultation-trigger reliability, or savings.
It did not exercise herdr transport. The final reference also explicitly permits
required begin/report protocol metadata at the assigned report location.

Consultation quality/cost comparisons across real tasks remain unmeasured. See the
PR for the exact checks run for this change.
