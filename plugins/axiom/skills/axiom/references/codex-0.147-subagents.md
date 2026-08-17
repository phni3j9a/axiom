# Codex 0.147 direct-spawn contract

This reference is version-specific. It teaches the Main agent how to request Luna MAX workers and fresh Sol reviewers without installing custom agent profiles.

## Preferred surface: Multi-Agent V2

Codex 0.147 adds support for leaf models in Multi-Agent V2. When the active `spawn_agent` schema exposes `task_name`, `fork_turns`, `model`, and `reasoning_effort`, use this shape.

### Luna MAX worker

```text
spawn_agent
  task_name: <short_lowercase_task_name>
  message: <self-contained worker packet>
  model: gpt-5.6-luna
  reasoning_effort: max
  fork_turns: none
```

### Fresh Sol reviewer

```text
spawn_agent
  task_name: review_<short_task_name>
  message: <self-contained review packet; explicitly forbid writes>
  model: gpt-5.6-sol
  reasoning_effort: xhigh
  fork_turns: none
```

`max`/`xhigh` are reasoning-effort choices. They are not service tiers. Do not set `service_tier` merely to obtain MAX/XHIGH reasoning.

V2 defaults `fork_turns` to `all` when omitted, so specify `none` intentionally for isolated Axiom work. Valid values are `none`, `all`, or a positive integer string such as `3`.

Codex 0.147 reports: `fork_context is not supported in MultiAgentV2; use fork_turns instead`. Do not pass the V1-only `fork_context` argument to a V2 spawn call.

## V1 compatibility surface in 0.147

If the actual `spawn_agent` schema is V1 and exposes `fork_context` rather than `fork_turns`, use the explicit model override there instead:

### Luna MAX worker, V1

```text
spawn_agent
  message: <self-contained worker packet>
  model: gpt-5.6-luna
  reasoning_effort: max
  fork_context: false
```

### Fresh Sol reviewer, V1

```text
spawn_agent
  message: <self-contained review packet; explicitly forbid writes>
  model: gpt-5.6-sol
  reasoning_effort: xhigh
  fork_context: false
```

Use the schema that is actually exposed by the running Codex session; never invent fields from the other surface.

## If V2 hides model overrides

In Codex 0.147, the V2 implementation supports explicit `model` and `reasoning_effort`, but the tool schema may hide those fields unless model overrides are exposed. The version's feature configuration includes:

```toml
[features.multi_agent_v2]
expose_spawn_agent_model_overrides = true
```

If the fields are not present on the active tool schema:

1. Do not send undeclared arguments.
2. Do not assume the child will become Luna automatically.
3. Do not silently substitute Terra.
4. Tell the user/runtime operator that model overrides are not exposed in this session and point to the 0.147 setting above.
5. Continue in Main when practical, or wait for the user to adjust runtime configuration when the requested model split matters.

`hide_spawn_agent_metadata` is a different V2 option; it controls returned spawn metadata and should not be treated as the switch that exposes model/effort arguments.

## Waiting and reuse

Do not busy-poll. Let workers run while Main performs non-overlapping work. Use the available wait primitive only when the result blocks the next critical step, with a meaningful timeout rather than repeated short waits.

Reuse an existing worker only when the follow-up genuinely benefits from its local context. Prefer a fresh reviewer even if the implementer is still available.

## Runtime truth

Tool schema and returned runtime metadata are more trustworthy than a subagent's prose claim about its model. If the runtime rejects the requested model/effort, report the failure instead of pretending the requested routing succeeded.
