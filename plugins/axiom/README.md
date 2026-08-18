# Axiom v0.1.3

Axiom is a guidance-first Codex plugin for non-trivial software engineering.

> Sol thinks. Luna works. Sol reviews.

- Main Sol owns intent, architecture, integration, and acceptance.
- Direct-spawn Luna MAX performs bounded exploration and implementation.
- Independent useful bounded work fans out to parallel Luna MAX workers; there is no fixed fleet size.
- Fresh direct-spawn Sol XHIGH performs meaningful independent review.
- The initial Sol reviewer is reused for re-review while Main adjudicates every finding.
- No fixed workflow, no Terra default, and no custom agent installation.
- `allow_implicit_invocation: true` makes the core Axiom skill available proactively.

## Optional Dashboard

Axiom v0.1.3 bundles Axiom Dashboard v0.1.0 as an optional observability companion. Distribution is unified, but runtime responsibilities remain separate.

- Rust/Axum local server with an embedded React UI
- reads Codex Rollout Trace and Git without modifying either
- live Agent Graph and parallel timeline
- review, token, compaction, Git, and Axiom-principle views
- localhost-only by default, no telemetry, no hooks, no daemon
- explicit `axiom-dashboard` skill with `allow_implicit_invocation: false`

The Dashboard is an observation plane, never an agent control plane. See `dashboard/README.md` for trace setup, launch commands, privacy notes, and build details.

See the repository root `README.md` for installation and configuration.
