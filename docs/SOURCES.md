# Sources and version notes

Checked: 2026-08-17.

Axiom intentionally keeps Codex-version-specific facts isolated from the general playbook.

## Authoritative OpenAI sources

- Plugin packaging and manifest/marketplace structure: https://developers.openai.com/plugins/build/plugins
- Skill structure and implicit invocation metadata: https://developers.openai.com/codex/skills
- Codex 0.147.0 release: https://github.com/openai/codex/releases/tag/rust-v0.147.0
- Codex 0.147.0 Multi-Agent V2 spawn implementation: https://github.com/openai/codex/blob/rust-v0.147.0/codex-rs/core/src/tools/handlers/multi_agents_v2/spawn.rs
- Codex 0.147.0 spawn tool schema: https://github.com/openai/codex/blob/rust-v0.147.0/codex-rs/core/src/tools/handlers/multi_agents_spec.rs
- Codex 0.147.0 V2 feature config fields: https://github.com/openai/codex/blob/rust-v0.147.0/codex-rs/features/src/feature_configs.rs

## Design reference

- sol-advisor: https://github.com/DannyMac180/sol-advisor

Axiom borrows general ideas such as a strong Main architect, bounded worker packets, and fresh independent review, but deliberately does **not** copy sol-advisor's route/mode ceremony.

## Facts encoded in the 0.147 reference

At the `rust-v0.147.0` tag:

- the release includes support for leaf models in Multi-Agent V2;
- the V2 handler accepts `task_name`, `message`, optional `agent_type`, `model`, `reasoning_effort`, `service_tier`, `fork_turns`, and a rejected compatibility `fork_context` field;
- V2 rejects `fork_context` and tells callers to use `fork_turns`;
- omitted `fork_turns` defaults to `all`; valid explicit forms are `none`, `all`, or a positive integer string;
- the spawn tool schema removes `model` and `reasoning_effort` unless model overrides are exposed;
- the V2 feature config contains `expose_spawn_agent_model_overrides` specifically for exposing those two fields.

These are version-specific implementation details. Re-verify them before retargeting Axiom to another Codex release.
