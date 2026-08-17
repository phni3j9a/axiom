---
name: axiom-dashboard
description: Start, inspect, or troubleshoot the optional local Axiom Dashboard when the user explicitly asks to open the dashboard, monitor Axiom agents, inspect a Codex rollout trace, or check dashboard setup. Do not invoke for ordinary engineering work; the core axiom skill remains independent of the dashboard.
---

# Axiom Dashboard

Use this skill only for an explicit dashboard or observability request. It is intentionally separate from the proactive `axiom` engineering skill.

## Boundaries

- The Dashboard is an observation plane, not a control plane.
- Do not use it to spawn, stop, message, approve, reject, or otherwise control agents.
- Do not modify the target repository.
- Bind to localhost only unless the user explicitly requests remote exposure and understands there is no authentication.
- Do not add hooks or background daemons.
- Do not enable telemetry.

## Launch procedure

1. Resolve the Plugin root from this skill directory. The launcher is at `../../dashboard/launch/` relative to this `SKILL.md` directory.
2. Determine the current repository path with `pwd` or the platform equivalent.
3. Check setup first:

   ```bash
   ../../dashboard/launch/axiom-dashboard.sh doctor --repo "$PWD"
   ```

   On Windows PowerShell use:

   ```powershell
   ../../dashboard/launch/axiom-dashboard.ps1 doctor --repo $PWD
   ```

4. If no trace root is configured, explain that `CODEX_ROLLOUT_TRACE_ROOT` must be set **before starting Codex**. Use `$HOME/.codex/axiom-traces` as the documented default, but do not alter shell profiles or Codex configuration without a separate user request.
5. Start the server with the repository path and browser opening enabled:

   ```bash
   ../../dashboard/launch/axiom-dashboard.sh serve --repo "$PWD" --open
   ```

6. Use a long-running terminal process rather than blocking the conversation. Report the localhost URL printed by the server.
7. If the release binary is absent, the launcher may use `cargo run --release`. If neither a matching binary nor Cargo exists, report the launcher's actionable build error instead of inventing a URL.

## Troubleshooting

Read [setup.md](references/setup.md) when traces are missing, the binary cannot be found, or the port cannot be opened.

## Privacy notice

Rollout traces can contain prompts, responses, tool inputs and outputs, terminal data, and filesystem paths. Keep them local and treat the trace directory as sensitive.
