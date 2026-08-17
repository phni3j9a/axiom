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
- Correctness, regressions, security/data integrity, requirement gaps,
  compatibility, and missing verification with material impact.

OUTPUT
- Report material findings only.
- Give each finding a stable ID.
- Cite concrete file/line/symbol/behavior evidence.
- Explain concrete impact and a bounded remediation direction.
- Omit style-only, preference-only, speculative, and low-value nit findings.
- Do not redesign beyond the accepted intent unless the current design cannot satisfy it.
```

## Reviewer output

A useful output is:

```text
FINDINGS:
- AX-001 Short title
  Evidence: exact file/line/behavior
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

Main assigns each material finding as useful:

- `ACCEPT` — valid and worth addressing in the current task;
- `DEFER` — valid but intentionally outside current scope, with residual risk understood;
- `REJECT` — unsupported, incorrect, preference-driven, or inconsistent with accepted intent;
- `ESCALATE` — resolving it requires user input or a substantive design/product decision.

Do not forward reviewer output blindly to an implementer. Translate accepted findings into bounded fix requirements that preserve Main's intended design.

Main also decides whether another review pass is useful. Reviewer output does not force another pass by itself.

## Finding Freeze and reviewer continuity

The initial review establishes stable finding IDs and a review boundary; it does not establish a fixed number of findings or rounds.

After accepted fixes, send a follow-up to the **same reviewer agent/session** when Main wants re-review. Include Main's adjudication and the evidence needed to inspect the updated candidate.

Example:

```text
RE-REVIEW WITH CONTINUITY.

Main adjudication:
- AX-001: ACCEPT — <required outcome>
- AX-002: REJECT — <brief rationale>
- AX-003: DEFER — <brief rationale>

Check the accepted findings against the updated candidate and consider whether
those fixes introduced or revealed any new material defect. Respect Main's
REJECT/DEFER decisions unless new concrete evidence materially changes them.
Do not restart style/preference review or rediscover already-adjudicated points.
```

Finding Freeze means:

- previously reported findings keep stable IDs;
- Main's adjudication controls task scope;
- re-review retains the original reviewer context instead of resetting it;
- accepted fixes remain the center of attention;
- genuinely new material defects may still be reported when supported by new evidence or caused/revealed by the fix;
- Main decides when further review has diminishing value and when the candidate is sufficiently resolved.

There is **no arbitrary finding-count limit and no arbitrary review-round limit**. Convergence comes from reviewer continuity, stable IDs, Main adjudication, and Main's judgment about remaining risk—not from numeric caps.

If reviewer and Main remain in substantive disagreement, Main decides whether to accept the risk, replan, escalate to the user, or request more evidence. The reviewer is not an autonomous loop controller.

## Reviewer session loss

If the original reviewer session is unavailable, do not silently substitute Luna. If independent review is still useful, direct-spawn a replacement Sol XHIGH reviewer and supply the prior findings, Main adjudication, relevant fixes, current candidate, and verification evidence needed to recover context.

Treat replacement as recovery, not the normal re-review pattern.

## Final acceptance

Main, not Reviewer, decides completion after considering the final candidate, verification evidence, accepted findings, pre-existing user work, and any residual risk.
