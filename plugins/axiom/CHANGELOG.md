# Changelog

## 0.1.8 — 2026-08-24

- Added direct-spawn Sol MAX design workers for bounded tasks that require material visual, interaction, or information-design judgment.
- Kept Luna MAX as the default for ordinary bounded work and for frontend implementation whose design decisions are already settled.
- Defined unresolved interface judgment—not frontend file ownership—as the design-routing boundary.
- Allowed Design Sol to implement UI when design and code iteration are inseparable, with mixed Luna lanes for disjoint non-visual work.
- Kept independent review on a separate fresh Sol XHIGH and explicitly prohibited reusing a Design Sol as the reviewer.
- Added routing examples, trigger evals, validation, and regression coverage for the new role separation.

## 0.1.7 — 2026-08-22

- Scoped same-reviewer continuity to materially stable user intent, acceptance, non-goals, and substantive design while leaving boundary-reset decisions with Main.
- Clarified that reviewers provide independent evidence but do not set user risk tolerance or product policy, and that optional hardening should be distinguished from demonstrated failures and requirement gaps.
- Clarified that `task_complete` is a per-turn return signal, not proof of a terminal agent session or Main acceptance.
- Extended evidence-aware waiting guidance to shell sessions, tests, builds, benchmarks, and external processes without imposing a fixed polling interval.
- Added a context-cost heuristic for overlapping Main/worker inspection without introducing an ownership prohibition.
- Added qualitative rollout trace eval guidance and a read-only metrics script; trace signals inform judgment and do not gate agent behavior.

## 0.1.6 — 2026-08-19

- Removed the breaking `hide_spawn_agent_metadata = false` metadata visibility setting from current setup/config guidance.
- Added a migration warning for v0.1.5 users to delete that setting because Codex CLI 0.147.0 returns HTTP 400 for the reserved `collaboration.spawn_agent` schema mismatch before the first model response.
- Clarified that routing verification uses runtime/rollout evidence—the requested spawn args, child `turn_context` model/effort, and `task_complete`—rather than child self-report alone.
- Added regression coverage for the schema/config change and rollout-based routing verification.

## 0.1.5 — 2026-08-19

- Removed the optional Axiom Dashboard introduced in v0.1.3.
- Removed the Rust/Axum backend, React/TypeScript frontend, platform launchers, and explicit Dashboard Skill.
- Removed Dashboard-specific Rust/Node CI and multi-platform binary release jobs.
- Simplified Plugin packaging to a Core-only distribution.
- Removed Dashboard/observability metadata, setup instructions, runtime documentation, and the stale validation report.
- Preserved Axiom Core delegation, parallel Luna, same-reviewer continuity, Git safety, direct-spawn policy, and the v0.1.4 Luna economics principle unchanged.

## 0.1.4 — 2026-08-18

- Made the current Luna MAX economics assumption explicit: for ordinary Axiom orchestration decisions, Luna worker compute is treated as almost free.
- Added the principle **“Main context is expensive; Luna compute is almost free.”**
- Instructed Main not to suppress useful bounded delegation merely to conserve Luna tokens or model usage.
- Shifted the practical spawn-cost model toward coordination, latency, dependency ordering, overlap/write conflicts, integration, and verification burden.
- Strengthened proactive delegation and parallel fan-out while retaining natural task boundaries, no fixed worker count, and safeguards against artificial fragmentation.
- Preserved the v0.1.3 Dashboard and existing Sol reviewer continuity policies unchanged.
- Added validation/tests to prevent accidental removal of the almost-free Luna economics policy.

## 0.1.3 — 2026-08-17

- Bundled Axiom Dashboard v0.1.0 inside the existing Plugin package while keeping Axiom Core and Dashboard runtime responsibilities separate.
- Added a Rust/Axum/Tokio read-only collector and local API with an embedded React/TypeScript UI.
- Added live Agent Graph, parallel timeline, token and compaction metrics, review/Finding inspection, Git status, recent sessions, and evidence-based Axiom principle checks.
- Added direct raw Rollout Trace projection with optional `state.json` enrichment; the Dashboard does not invoke the reducer or create execution state.
- Added localhost-only defaults, explicit non-loopback opt-in, no telemetry, no hooks, and read-only Git inspection.
- Added an explicit-only `axiom-dashboard` Skill so ordinary Axiom engineering requests remain unaffected.
- Added platform launchers, binary overlay packaging, source packaging, CI validation, and multi-platform release workflow.
- Preserved all v0.1.2 parallel Luna and same-Sol-reviewer policies unchanged.

## 0.1.2 — 2026-08-17

- Made safe parallel Luna MAX execution a first-class default when two or more useful bounded tasks are independent.
- Added dependency-driven fleet sizing: Main chooses the natural worker count; Axiom has no fixed fan-out or concurrency target.
- Instructed Main to spawn known-independent workers before waiting, avoiding accidental serial `spawn -> wait -> spawn` execution.
- Strengthened proactive parallel read-only investigation and disjoint-write guidance.
- Preserved safeguards against artificial task fragmentation, overlapping writes, unstable interfaces, and unnecessary intermediary orchestrators.
- Kept the v0.1.1 same-Sol-reviewer continuity and Main adjudication policy unchanged.

## 0.1.1 — 2026-08-17

- Reuse the same Sol reviewer agent for all re-review in a review cycle.
- Keep only the initial reviewer context fresh; subsequent checks use follow-up on the same reviewer handle.
- Removed the maximum-five-findings rule.
- Removed the fixed two-review-round limit.
- Made Main adjudication and stable Finding IDs the convergence mechanism.
- Allow genuinely new material findings when supported by changed evidence, while preventing rejected or deferred findings from being reopened without new evidence.

## 0.1.0 — 2026-08-17

Initial Axiom release.

- Added proactively invoked guidance-first engineering skill.
- Added Codex v0.147 direct-spawn recipes.
- Set Luna MAX as the default bounded worker.
- Set fresh Sol XHIGH as the only delegated reviewer.
- Removed Terra from the default route.
- Avoided all custom agent TOML installation.
- Added risk-based review and initial review convergence guidance.
- Added context-isolation and Git coordination guidance.
- Added local marketplace packaging, validation, tests, and release tooling.
