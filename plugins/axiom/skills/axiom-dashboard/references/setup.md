# Axiom Dashboard setup and troubleshooting

## No traces found

Codex only writes Rollout Trace bundles when `CODEX_ROLLOUT_TRACE_ROOT` exists in the environment of the Codex process at startup.

macOS / Linux:

```bash
export CODEX_ROLLOUT_TRACE_ROOT="$HOME/.codex/axiom-traces"
mkdir -p "$CODEX_ROLLOUT_TRACE_ROOT"
codex
```

PowerShell:

```powershell
$env:CODEX_ROLLOUT_TRACE_ROOT = "$HOME/.codex/axiom-traces"
New-Item -ItemType Directory -Force $env:CODEX_ROLLOUT_TRACE_ROOT | Out-Null
codex
```

A Dashboard started from the current session cannot retroactively enable tracing for that already-running parent process.

## Binary missing

Official release packages include supported platform binaries. Source archives include the Rust crate and use Cargo as a development fallback.

```bash
cargo build --release --manifest-path plugins/axiom/dashboard/Cargo.toml
```

Copy the resulting executable to the platform directory documented in `dashboard/bin/README.md`, or run through the launcher while Cargo is available.

## Port occupied

The default is `127.0.0.1:43127`. The server automatically tries nearby ports. Use an explicit port when needed:

```bash
./dashboard/launch/axiom-dashboard.sh serve --port 43200 --repo "$PWD" --open
```

## Incomplete metrics

The raw trace schema does not guarantee that every optional model override, reasoning effort, token usage, or spawn setting is present in every payload. `unknown` is a valid observability result. Do not reinterpret it as failure.

## Sensitive traces

Do not commit trace roots. Do not expose the Dashboard over a network by default. Delete old bundles according to the user's local retention policy.
