# Independent Sol review

## Reviewer identity

When delegated independent review is useful, use:

- model: `gpt-5.6-sol`
- reasoning effort: `xhigh`
- initial context: fresh, normally `fork_turns: "none"`
- launch: direct `spawn_agent`
- role: evidence-based reviewer, not implementer

Do not use Luna as reviewer. Do not install or depend on a custom reviewer agent.

The reviewer is **fresh at the start of the review cycle**. If fixes are made and re-review is useful, continue with the **same reviewer agent/session** so it retains the original findings, Main adjudication, and review boundary. Do not spawn a new reviewer merely because the candidate changed.

Continuity assumes that user intent, acceptance criteria, non-goals, and substantive design remain materially stable. When one of those changes, Main decides whether the existing findings can be re-adjudicated within the current context, whether an explicit review-boundary reset is enough, or whether a fresh review cycle would restore useful independence. A material steer is a judgment point, not an automatic reset rule.

## When review adds value

Use risk, uncertainty, and verification quality rather than file count.

Review value tends to rise when:

- correctness depends on subtle behavior or edge cases;
- deterministic tests are incomplete or expensive;
- regression/blast-radius risk is meaningful;
- security, auth, persistence, migration, concurrency, cryptography, protocols, or public compatibility are involved;
- the implementation changes cross-cutting assumptions or architecture;
- Main wants an independent challenge before accepting the candidate.

A mechanically verified or clearly trivial change may not need delegated review. A one-file change can be high risk; a many-file mechanical change can be low risk.

## Useful review context

Before initial review, Main should normally provide enough evidence for the reviewer to understand:

- user-visible intent and acceptance criteria;
- important design decisions and non-goals;
- the actual candidate diff/change boundary;
- relevant verification already performed;
- pre-existing user changes that are outside scope;
- known limitations or unresolved uncertainty.

This is context guidance, not a required ceremony. Main may omit fields that add no value.

## Finding admissibility and complexity discipline

A material finding needs an independent current basis. Before reporting a finding, the reviewer should be able to connect it to at least one of:

- the accepted intent or acceptance criteria;
- an existing supported behavior, contract, or compatibility obligation;
- a concrete failure or regression demonstrated by the candidate;
- a concrete security, data-integrity, or trust-boundary risk;
- a verification gap that materially prevents judging one of the above.

Do not turn hypothetical future needs, generic hardening, future-proofing, broader reuse, defense in depth, or preference for a more elaborate architecture into findings without such a basis.

Candidate-authored code, tests, schemas, migrations, documentation, compatibility layers, state, or abstractions do not by themselves prove that the capability they introduce is required. Prior reviewer suggestions also do not create requirements. Trace the need back to independent current evidence rather than reasoning from the existence of newly added machinery.

Unnecessary complexity is itself reviewable when an added mechanism lacks independent current justification **and** materially increases failure surface, state, migration burden, operational behavior, dependency surface, or maintenance cost. Examples include unjustified caches, retries, fallbacks, persistent state, migrations, abstraction layers, compatibility shims, schedulers, reconciliation loops, configuration, or dependencies. These mechanisms are not forbidden when the current task actually needs them.

When a demonstrated problem can be corrected either by removing unjustified machinery or by adding another mechanism, prefer the smallest subtractive correction that still satisfies the current contract. Do not create work merely to make the candidate more generic, configurable, resilient to unspecified scenarios, or architecturally elaborate.

Optional hardening is not a material finding. Preserve concrete safety and correctness evidence, but omit speculative risk-reduction suggestions from `FINDINGS` unless they satisfy the admissibility rule above.

## Initial Review Packet

```text
READ-ONLY REVIEW.
Do not edit files, commit, format, auto-fix, generate code into the working
 tree, or run commands likely to mutate it. Inspect and report evidence only.

INTENT / ACCEPTANCE
- <goal and relevant acceptance criteria>

DESIGN CONTEXT
- <important decisions/non-goals only>

CANDIDATE
- <how to inspect the actual diff/change>
- <pre-existing changes outside scope if relevant>

VERIFICATION EVIDENCE
- <checks already run and notable gaps>

FOCUS
- Correctness, regressions, concrete security/data-integrity risks, requirement
  gaps, compatibility, unjustified complexity, and missing verification with
  material impact.

OUTPUT
- Report material findings only, each with independent current evidence.
- Give each finding a stable ID.
- Cite concrete file/line/symbol/behavior evidence.
- Explain concrete impact and a bounded remediation direction.
- Omit style-only, preference-only, speculative, optional-hardening, and low-value nit findings.
- Do not treat candidate-created machinery or prior review suggestions as requirements by themselves.
- Prefer removing unjustified machinery over adding machinery when both satisfy the current contract.
- Do not redesign beyond the accepted intent unless the current design cannot satisfy it.
```

## Reviewer output

A useful output is:

```text
FINDINGS:
- AX-001 Short title
  Evidence: exact file/line/behavior and current basis
  Impact: concrete failure or risk
  Remediation direction: smallest useful correction

RESIDUAL_RISK:
- concise remaining uncertainty, if useful

VERIFICATION_GAPS:
- checks that still matter, if useful
```

If there are no material findings:

```text
FINDINGS: none
```

Do not require the reviewer to issue `SHIP`, `FIX_FIRST`, `RETHINK`, severity enums, or other release verdicts. Main owns acceptance and scope.

## Main adjudication

Reviewer findings are proposals, not commands.

The reviewer supplies independent evidence; it does not set the user's risk tolerance or product policy. Main should preserve concrete correctness, safety, requirement, and unjustified-complexity evidence while adjudicating which mitigations fit the user's accepted intent. An explicit user non-goal or rejected hardening should not be reintroduced as a requirement without materially new independent evidence. When concrete evidence may materially conflict with accepted intent, Main makes the conflict and residual risk explicit, then decides within its authority whether to accept, defer, reject, replan, or escalate. The reviewer does not decide for Main.

Main assigns each material finding as useful:

- `ACCEPT` — valid and worth addressing in the current task;
- `DEFER` — valid but intentionally outside current scope, with residual risk understood;
- `REJECT` — unsupported, incorrect, preference-driven, optional hardening, or inconsistent with accepted intent;
- `ESCALATE` — resolving it requires user input or a substantive design/product decision.

Do not forward reviewer output blindly to an implementer. Translate accepted findings into bounded fix requirements that preserve Main's intended design and avoid unnecessary additive machinery.

Main also decides whether another review pass is useful. Reviewer output does not force another pass by itself.

## Finding Freeze and reviewer continuity

The initial review establishes stable finding IDs and a review boundary; it does not establish a fixed number of findings or rounds.

Finding Freeze applies inside that boundary. A material change to user intent, acceptance, non-goals, architecture, or risk policy may make earlier findings stale, newly optional, or newly relevant. Main re-adjudicates them and chooses the continuity strategy; it does not keep a prior finding binding merely because the same reviewer session still exists.

After accepted fixes, send a follow-up to the **same reviewer agent/session** when Main wants re-review. Include Main's adjudication and the evidence needed to inspect the updated candidate.

Example:

```text
RE-REVIEW WITH CONTINUITY.

Main adjudication:
- AX-001: ACCEPT — <required outcome>
- AX-002: REJECT — <brief rationale>
- AX-003: DEFER — <brief rationale>

Check the accepted findings against the updated candidate. A new finding is
admissible only when the accepted fix directly introduced/revealed a material
defect, or when independent current evidence shows a violation of a requirement
that was already inside the review boundary. Newly added machinery, its own
schemas/docs/tests/state, or a prior reviewer suggestion do not by themselves
create a new requirement. Respect Main's REJECT/DEFER decisions unless new
concrete evidence materially changes them. Do not restart style/preference or
optional-hardening review.
```

Finding Freeze means:

- previously reported findings keep stable IDs;
- Main's adjudication controls task scope;
- re-review retains the original reviewer context instead of resetting it;
- accepted fixes remain the center of attention;
- new material findings require either a defect directly introduced/revealed by an accepted fix or independent current evidence against an in-boundary requirement;
- candidate-created machinery does not create follow-on obligations merely by existing;
- Main decides when further review has diminishing value and when the candidate is sufficiently resolved.

There is no fixed finding count and no fixed review-round limit. Convergence comes from reviewer continuity, stable IDs, evidence-bounded findings, Main adjudication, and Main's judgment about remaining risk—not from numeric caps.

If reviewer and Main remain in substantive disagreement, Main decides whether to accept the risk, replan, escalate to the user, or request more evidence. The reviewer is not an autonomous loop controller.

## Reviewer session loss

If the original reviewer session is unavailable, do not silently substitute Luna. If independent review is still useful, direct-spawn a replacement Sol XHIGH reviewer and supply the prior findings, Main adjudication, relevant fixes, current candidate, and verification evidence needed to recover context.

Treat replacement as recovery, not the normal re-review pattern.

## Final acceptance

Main, not Reviewer, decides completion after considering the final candidate, verification evidence, accepted findings, pre-existing user work, and any residual risk.
