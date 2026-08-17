# Axiom plugin

Axiom is a lightweight engineering playbook for Codex. It does not impose a fixed software-development workflow.

## Contract

- Main owns requirements, architecture, decomposition, integration, reviewer adjudication, and final acceptance.
- Delegated bounded work defaults to direct-spawned `gpt-5.6-luna` with `reasoning_effort: max`.
- Independent review, when warranted, uses a fresh direct-spawned `gpt-5.6-sol` with `reasoning_effort: xhigh`.
- No custom subagent profiles, hooks, runtime state machine, mandatory phases, or mandatory one-task-one-commit rule.
- Review uses Finding Freeze to prevent open-ended review/fix loops.

The primary instructions live in `skills/axiom/SKILL.md`; version-specific Codex 0.147 details live under `skills/axiom/references/`.

The `skills/axiom/agents/openai.yaml` file is skill UI/invocation metadata, not a custom subagent definition.

## Codex 0.147 model-routing prerequisite

When Multi-Agent V2 does not expose `model` and `reasoning_effort` on `spawn_agent`, enable the version's model-override surface and restart the session:

```toml
[features.multi_agent_v2]
expose_spawn_agent_model_overrides = true
```

## License

MIT
