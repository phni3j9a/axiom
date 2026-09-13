# Axiom v0.1.9

Axiom is a guidance-first Codex plugin for non-trivial software engineering.

> Main decides. Astra advises. Sol designs. Luna executes. Sol reviews.
>
> **Main context is expensive; Luna compute is almost free.**

- Main (Sol XHIGH) owns intent, architecture, design direction and constraints, integration, and acceptance.
- The recommended environment is Codex v0.147 or later, including v0.153. Main uses `gpt-5.6-sol` / `xhigh`, ordinary workers use `gpt-5.6-luna` / `max` / Fast, design uses `gpt-5.6-sol` / `max`, and review uses fresh `gpt-5.6-sol` / `xhigh`. The plugin cannot switch an active Main session.
- Axiom v0.1.9 preserves the v0.1.4 economics principle that ordinary Luna MAX worker usage is treated as almost free for orchestration decisions.
- Direct-spawn Luna MAX performs bounded exploration and implementation; useful spawns should not be suppressed merely to conserve Luna usage.
- Request Fast only for ordinary workers when the tool exposes a tier override or inherited Fast is verified. If Fast cannot be established, report the limitation and retain Luna MAX; see the direct-spawn reference.
- Direct-spawn Sol MAX performs bounded work that requires material visual, interaction, or information-design judgment; frontend files alone do not trigger this route.
- A Sol MAX design worker may implement its design when the feedback loop is inseparable, but it is never reused as the independent reviewer.
- Independent useful bounded work fans out to parallel Luna MAX workers; there is no fixed fleet size, and coordination/integration cost—not Luna token cost—limits fan-out.
- Astra XHIGH drafts difficult plans and advises on consequential decisions after orientation. Main selects relevant dialogue and primary evidence instead of forking its history; Astra can request missing facts. See [advisor guidance](skills/axiom/references/advisor.md).
- Keep the same Advisor for same-question follow-ups; its no-project-edit contract is behavioral, and it is not reused as the independent Reviewer.
- Fresh direct-spawn Sol XHIGH performs meaningful independent review.
- The initial Sol reviewer is reused for re-review while the review boundary remains materially stable; Main adjudicates every finding and any boundary reset.
- Reviewers provide evidence but do not set user risk tolerance or product policy.
- `task_complete` is treated as a child-turn return signal, not Main acceptance or terminal agent state.
- Evidence-aware wait and optional rollout metrics inform Main without imposing fixed cadence or workflow gates.
- Repeated status checks for long-running processes go to a Luna worker through completion, reusing the responsible Luna when available. Main waits for concise completion, failure, monitoring-blocker, or decision-needed reports instead of repeatedly checking progress; unchanged-status reports are unnecessary.
- No fixed workflow, no Terra default, and no custom agent installation.
- `allow_implicit_invocation: false` reserves Axiom for explicit invocation with `$axiom:axiom`; its delegation and review guidance applies throughout that task and its follow-up work.

See the repository root `README.md` for installation and configuration.

Codex CLI 0.147.0 migration: v0.1.5 users must delete `hide_spawn_agent_metadata = false` from their existing configuration. Leaving it in place causes an HTTP 400 reserved `collaboration.spawn_agent` schema mismatch before the first model response.

Routing verification uses runtime/rollout evidence—the requested spawn args, the child `turn_context` model/effort, and the corresponding child-turn `task_complete`—and never a child self-report alone. A returned child turn is not by itself Main acceptance or a terminal agent session.

Optional read-only rollout metrics:

```bash
python3 skills/axiom/scripts/audit_rollout.py /path/to/rollout.jsonl
```

Metrics support qualitative evaluation; they do not gate or control Main.
