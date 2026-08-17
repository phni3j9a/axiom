# Axiom Dashboard v0.1.0

Axiom Dashboard is the optional local observability companion bundled with Axiom v0.1.3.

> Distribution is unified. Runtime responsibilities remain separate.

Axiom Core supplies engineering principles. The Dashboard does not orchestrate agents, assign work, accept findings, or mutate the repository. It builds a read-only projection from Codex Rollout Trace and Git inspection.

## What v0.1.0 shows

- root and spawned agent graph
- model, reasoning effort, task name, lifecycle, duration, tokens, and compactions when observable
- parallel worker timeline, peak concurrency, and overlap
- delegated reviewer detection, review rounds, verdicts, and `AX-*` findings
- Main / Worker / Reviewer token distribution
- read-only Git branch, status, files, and diff statistics
- evidence-based Axiom principle checks
- recent trace-session history

Some trace fields are optional or version-dependent. The UI reports `unknown` rather than guessing when model overrides, `fork_turns`, token usage, or review semantics are not observable.

## Privacy and security

- Binds to `127.0.0.1` by default.
- Refuses a non-loopback bind unless `--allow-remote` is explicit.
- Sends no telemetry.
- Uses read-only Git commands.
- Reads raw trace payloads only from safe bundle-relative paths.
- Does not run `codex debug trace-reduce` or write `state.json`.
- Uses an existing `state.json` only as optional enrichment.

Rollout traces can contain prompts, responses, tool data, terminal output, and local paths. Protect the trace directory as sensitive data.

## Enable tracing

Tracing must be enabled **before Codex starts**:

```bash
export CODEX_ROLLOUT_TRACE_ROOT="$HOME/.codex/axiom-traces"
codex
```

PowerShell:

```powershell
$env:CODEX_ROLLOUT_TRACE_ROOT = "$HOME/.codex/axiom-traces"
codex
```

Changing the variable from inside an already-running Codex session cannot retroactively trace that process. Start a new Codex process after setting it.

## Launch

Installed release package:

```bash
./dashboard/launch/axiom-dashboard.sh serve --repo "$PWD" --open
```

PowerShell:

```powershell
./dashboard/launch/axiom-dashboard.ps1 serve --repo $PWD --open
```

The bundled `axiom-dashboard` skill performs this lookup for the user.

Useful commands:

```bash
axiom-dashboard doctor --repo "$PWD"
axiom-dashboard snapshot --repo "$PWD"
axiom-dashboard serve --repo "$PWD" --open
```

Common options:

```text
--trace-root <path>   override CODEX_ROLLOUT_TRACE_ROOT
--repo <path>         repository inspected with read-only Git commands
--max-sessions <n>    recent sessions retained in the read model
--refresh-ms <n>      live refresh interval, minimum 250 ms
--port <n>            preferred localhost port; nearby ports are tried when busy
```

## Build

Requirements:

- stable Rust toolchain
- no Node runtime is required for the committed web bundle
- TypeScript is needed only when changing `web/src/app.ts`

```bash
cargo test --manifest-path plugins/axiom/dashboard/Cargo.toml
cargo build --release --manifest-path plugins/axiom/dashboard/Cargo.toml
```

The React web assets are embedded into the Rust executable with `include_str!`, so the release runtime is a single local binary.

Rebuild the web application:

```bash
cd plugins/axiom/dashboard/web
npm run build
```

The web build deliberately has no npm runtime dependencies. React 16 UMD assets are vendored under the MIT license so the dashboard remains offline and reproducible.

## Architecture

```text
Codex runtime
   │
   └─ CODEX_ROLLOUT_TRACE_ROOT
          └─ manifest.json + trace.jsonl + payloads/
                         │ read only
                         ▼
                 axiom-dashboard (Rust)
                 ├─ trace discovery
                 ├─ lightweight semantic projection
                 ├─ review and compliance analysis
                 ├─ read-only Git inspection
                 ├─ Axum localhost server
                 └─ embedded React UI
```

The Dashboard read model is derived observation state. It is not Axiom execution state and never becomes a source of truth for agent behavior.
