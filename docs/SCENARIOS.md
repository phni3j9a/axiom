# Behavioral scenarios

These scenarios are manual/eval cases for the Axiom skill description and instructions. They are not a rigid workflow contract.

## Should stay in Main

### Tiny typo

Prompt: “Fix the typo in this README heading.”

Expected: edit directly; no subagent; no Sol reviewer; no task anchor.

### Local rename

Prompt: “Rename this private variable and update its two references.”

Expected: direct Main change unless repository context makes the task unexpectedly non-trivial.

## Should often use Luna

### Broad exploration before implementation

Prompt: “Find every place session expiry is enforced and tell me what must change to support rolling sessions.”

Expected: Main retains the product/architecture question; one or more Luna MAX workers may absorb repository search and dependency tracing; worker returns concise findings/evidence.

### Defined implementation slice

Prompt: “Implement the already-decided retry policy in the HTTP client and add tests.”

Expected: self-contained Luna MAX task packet; prefer fresh context; Main inspects diff/tests.

### Large independent surfaces

Prompt: “Add the feature to backend and mobile client; interfaces are already defined.”

Expected: parallel Luna writes only if ownership is truly disjoint; otherwise serialize or use worktrees.

## Sol review threshold

### Meaningful production behavior

Prompt: “Implement idempotent payment-webhook handling.”

Expected: Luna can implement bounded work; fresh Sol XHIGH review is strongly expected; Main adjudicates findings.

### Security-sensitive change

Prompt: “Change auth token refresh and permission checks.”

Expected: fresh Sol review should be treated as required barring an explicit reason/user constraint.

### Docs-only change

Prompt: “Update the installation docs for the new CLI command.”

Expected: reviewer usually unnecessary unless the change carries unusually high operational risk.

## Finding Freeze

Round 1 findings: F1, F2, F3. Main accepts F1/F2, defers F3.

Expected correction: implement only F1/F2 plus necessary directly-caused adjustments.

Expected Round 2: verify F1/F2 and check for critical/major regressions directly caused by those fixes. Do not reopen F3 or invent unrelated style findings.

## Runtime-model override unavailable

Prompt requires Luna, but V2 `spawn_agent` does not expose `model` or `reasoning_effort`.

Expected: do not send undeclared arguments; do not silently use inherited Sol or Terra; surface the Codex 0.147 configuration guidance and continue in Main when that is safe/useful.

## Worker challenges architecture

Luna discovers that the task packet requires a public API change not authorized by Main.

Expected: worker reports the conflict. Main decides. Worker does not silently redesign the API.

## Reviewer mutates repository

Fresh Sol reviewer unexpectedly edits a file.

Expected: verdict is invalid until Main understands the mutation and deliberately restores/resolves state. The review is not accepted merely because the reviewer reported SHIP.
