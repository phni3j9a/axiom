# Changelog

## 0.1.2 — 2026-08-17

- Reframed Axiom guidance as Hard constraints, Strong defaults, and Heuristics.
- Replaced the 10-step default decision process with adaptive decision lenses.
- Made Task Packet structure proportional to task complexity instead of mandatory.
- Removed reviewer `SHIP/FIX_FIRST/RETHINK` verdicts and Critical/Major severity enums.
- Changed review triggering from file-count/category rules to risk, uncertainty, blast radius, and verification quality.
- Softened worker commit, parallel-write, follow-up, and context-fork rules into defaults/heuristics where appropriate.
- Kept hard role/safety boundaries: Main adjudication, Sol-only delegated review, same-reviewer continuity, user-work preservation, and Git safety.
- Set Codex v0.147 `default_wait_timeout_ms` and `max_wait_timeout_ms` to 3,600,000 ms (60 minutes) in the example config and added long-wait guidance to avoid 30-second polling churn.

## 0.1.1 — 2026-08-17

- Reused the same direct-spawn Sol reviewer session for re-review instead of spawning a fresh reviewer per pass.
- Removed the arbitrary maximum finding count.
- Removed the arbitrary maximum review-round count.
- Kept Finding Freeze through stable finding IDs, Main adjudication, and verification-focused re-review.
- Added recovery guidance for reviewer-session loss.

## 0.1.0 — 2026-08-17

Initial Axiom release.

- Added proactively invoked guidance-first engineering skill.
- Added Codex v0.147 direct-spawn recipes.
- Set Luna MAX as the default bounded worker.
- Set fresh Sol XHIGH as the only delegated reviewer.
- Removed Terra from the default route.
- Avoided all custom agent TOML installation.
- Added risk-based review and Finding Freeze.
- Added context-isolation and Git coordination guidance.
- Added local marketplace packaging, validation, tests, and release tooling.
