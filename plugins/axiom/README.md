# Axiom v0.1.7

Axiom is a guidance-first Codex plugin for non-trivial software engineering.

> Sol thinks. Luna works. Sol reviews.
>
> **Main context is expensive; Luna compute is almost free.**

- Main Sol owns intent, architecture, integration, and acceptance.
- Axiom v0.1.7 preserves the v0.1.4 economics principle that ordinary Luna MAX worker usage is treated as almost free for orchestration decisions.
- Direct-spawn Luna MAX performs bounded exploration and implementation; useful spawns should not be suppressed merely to conserve Luna usage.
- Independent useful bounded work fans out to parallel Luna MAX workers; there is no fixed fleet size, and coordination/integration cost—not Luna token cost—limits fan-out.
- Fresh direct-spawn Sol XHIGH performs meaningful independent review.
- The initial Sol reviewer is reused for re-review while the review boundary remains materially stable; Main adjudicates every finding and any boundary reset.
- Reviewers provide evidence but do not set user risk tolerance or product policy.
- `task_complete` is treated as a child-turn return signal, not Main acceptance or terminal agent state.
- Evidence-aware wait and optional rollout metrics inform Main without imposing fixed cadence or workflow gates.
- No fixed workflow, no Terra default, and no custom agent installation.
- `allow_implicit_invocation: true` makes the core Axiom skill available proactively.

See the repository root `README.md` for installation and configuration.

Codex CLI 0.147.0 migration: v0.1.5 users must delete `hide_spawn_agent_metadata = false` from their existing configuration. Leaving it in place causes an HTTP 400 reserved `collaboration.spawn_agent` schema mismatch before the first model response.

Routing verification uses runtime/rollout evidence—the requested spawn args, the child `turn_context` model/effort, and the corresponding child-turn `task_complete`—and never a child self-report alone. A returned child turn is not by itself Main acceptance or a terminal agent session.

Optional read-only rollout metrics:

```bash
python3 skills/axiom/scripts/audit_rollout.py /path/to/rollout.jsonl
```

Metrics support qualitative evaluation; they do not gate or control Main.
