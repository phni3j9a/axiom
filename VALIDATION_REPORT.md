# Validation Report

Generated: 2026-08-17 02:39 UTC  
Axiom version: 0.1.2  
Target Codex: v0.147.x

## Structural validator

```text
Axiom validation PASSED (96 checks)
```

## Unit tests

```text
test_direct_spawn_roles (test_plugin.AxiomPluginTests.test_direct_spawn_roles) ... ok
test_manifest_and_marketplace_names (test_plugin.AxiomPluginTests.test_manifest_and_marketplace_names) ... ok
test_no_custom_agent_toml (test_plugin.AxiomPluginTests.test_no_custom_agent_toml) ... ok
test_proactive_invocation (test_plugin.AxiomPluginTests.test_proactive_invocation) ... ok
test_rigid_workflow_artifacts_removed (test_plugin.AxiomPluginTests.test_rigid_workflow_artifacts_removed) ... ok
test_same_reviewer_convergence_without_hard_caps_or_verdict_schema (test_plugin.AxiomPluginTests.test_same_reviewer_convergence_without_hard_caps_or_verdict_schema) ... ok
test_validator (test_plugin.AxiomPluginTests.test_validator) ... ok
test_wait_agent_uses_sixty_minute_default (test_plugin.AxiomPluginTests.test_wait_agent_uses_sixty_minute_default) ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.540s

OK
```

## Confirmed design constraints

- One proactively invokable `axiom` skill
- `allow_implicit_invocation: true`
- guidance separated into hard constraints, strong defaults, and heuristics
- direct-spawn Luna MAX worker guidance
- initially fresh direct-spawn Sol XHIGH reviewer guidance
- same Sol reviewer session reused for re-review
- Main adjudicates reviewer findings and controls convergence
- no fixed reviewer verdict/severity schema
- no arbitrary maximum finding count or review-round count
- no mandatory Task Packet schema or default step sequence
- worker commit, parallel-write, context-fork, and follow-up rules expressed as adaptive defaults/heuristics where appropriate
- no Terra default route
- no custom agent TOML
- `wait_agent` recommended/configured at the v0.147 60-minute maximum (`3600000` ms)
- no mandatory workflow phases or runtime state
- local marketplace entry included

This is repository-local structural and policy validation. It is not a live authenticated model-routing probe.
