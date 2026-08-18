# Axiom v0.1.3 Validation Report

Generated: 2026-08-17 15:17 JST  
Axiom version: 0.1.3  
Dashboard version: 0.1.0  
Target Codex: v0.147.x

## Completed checks

### Plugin structural validator

```text
Axiom validation PASSED (158 checks)
```

The validator covers manifests, marketplace metadata, Skill policy, direct-spawn routing guidance, review continuity, Dashboard isolation, read-only boundaries, embedded web assets, launchers, release workflows, and archive rules.

### Python unit tests

```text
Ran 10 tests
OK
```

Covered behaviors include:

- proactive Axiom Core and explicit-only Dashboard invocation
- Luna MAX worker routing and dependency-driven parallelism
- fresh Sol XHIGH review and same-reviewer re-review continuity
- absence of custom agent TOML and fixed review caps
- Dashboard observation-plane/read-only constraints
- local embedded web bundle
- Plugin and source archive generation

### Frontend checks

```text
TypeScript no-emit check: PASS
TypeScript build: PASS
Generated app.js syntax check: PASS
Deterministic committed bundle: PASS
```

`web/dist/app.js` remained byte-identical after rebuilding from `web/src/app.ts`.

### Static and packaging checks

```text
Python bytecode compilation: PASS
JSON parsing: PASS
YAML parsing: PASS
POSIX launcher shell syntax: PASS
ZIP integrity: PASS
```

### Axiom Core compatibility

The following v0.1.2 Core files are byte-identical in v0.1.3:

- `skills/axiom/SKILL.md`
- `skills/axiom/agents/openai.yaml`
- `skills/axiom/references/delegation.md`
- `skills/axiom/references/review.md`
- `skills/axiom/references/git.md`
- `skills/axiom/references/context-management.md`
- `skills/axiom/references/codex-0.147-subagents.md`

This confirms that v0.1.3 adds the optional Dashboard without changing the agreed v0.1.2 Core behavior.

## Rust validation status

The current execution environment does not contain `cargo`, `rustc`, or `rustfmt`, and external binary installation is restricted. Consequently, the Rust crate could not be compiled or executed locally in this environment.

The repository includes GitHub Actions that run the following with a stable Rust toolchain:

```text
cargo check --all-targets
cargo clippy --all-targets
cargo test
cargo build --release
```

The release workflow builds and packages native Dashboard binaries for:

- Linux x86_64
- macOS Apple Silicon
- macOS Intel
- Windows x86_64

The release packager refuses `--require-dashboard-binaries` packaging unless all four required binaries are present.

## Distribution note

The locally generated Plugin ZIP in this delivery contains the complete Axiom Core, Dashboard source, committed web UI, and platform launchers, but no prebuilt native Dashboard executable because Rust compilation was unavailable here.

- Axiom Core installs and operates normally.
- Dashboard launchers use a matching bundled binary when present.
- In this source-capable package, the launchers fall back to `cargo run --release` when Cargo is installed.
- The included GitHub release workflow creates the intended self-contained Plugin ZIP with native binaries overlaid.

## Result

All checks available in this environment passed. Native Rust compilation remains delegated to the included CI workflow and is the only unexecuted validation category.
