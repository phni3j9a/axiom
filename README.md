# Axiom

**Axiom is an adaptive agentic-engineering playbook for Codex, not a workflow engine.**

Axiom teaches a capable Main agent how to delegate bounded work, protect its context, use independent review, and coordinate Git **without forcing phases, gates, run state, or one-task-one-commit ceremony**.

## Design in one picture

```text
                         Main: GPT-5.6 Sol XHIGH
                   requirements / architecture / judgment
                                  /  |  \
                                 /   |   \
                                v    v    v
                         Luna MAX  Luna MAX  Luna MAX
                         bounded workers as useful
                                \    |    /
                                 \   |   /
                                  v  v  v
                              Main integrates
                                   |
                          meaningful/risky change?
                              /          \
                            no            yes
                            |              |
                            v              v
                         verify      fresh Sol XHIGH
                                      direct review
                                           |
                                     Main adjudicates
                               ACCEPT / DEFER / REJECT
                                           |
                                   accepted fixes only
                                           |
                                Sol verification review
                                  (Finding Freeze)
```

## What Axiom does

- Keeps product intent, architecture, decomposition, integration, and final acceptance in Main.
- Uses **GPT-5.6 Luna at MAX effort** as the default general-purpose worker for bounded exploration, implementation, tests, debugging, and repetitive work.
- Uses **fresh GPT-5.6 Sol at XHIGH effort** for independent review when review is warranted.
- Uses **direct `spawn_agent` only**. No custom subagent profiles need to be installed.
- Defaults isolated V2 workers to `fork_turns: "none"` when a self-contained task packet is available.
- Stops review churn with **Finding Freeze** and a default two-round ceiling.
- Treats Git as an integration boundary rather than a mandatory commit protocol.
- Allows an optional tiny task anchor for long-horizon/compaction-prone work; it does not create a workflow database.

## What Axiom deliberately does not do

Axiom does **not** require Spec/Plan approval phases, Runs, Gates, Terra orchestration, custom agent TOMLs, hooks, runtime state files, automatic commits, mandatory worktrees, mandatory review for trivial edits, or a fixed number of subagents.

Small work should remain small.

## Codex target

The version-specific routing reference targets **Codex 0.147.x**. In that release, Multi-Agent V2 supports leaf-model delegation. Axiom explicitly requests Luna/Sol model and reasoning overrides instead of trusting inheritance.

If the active V2 `spawn_agent` schema does not expose `model` and `reasoning_effort`, add this to `~/.codex/config.toml` and start a new Codex session:

```toml
[features.multi_agent_v2]
expose_spawn_agent_model_overrides = true
```

Axiom does not silently fall back to Terra or pretend Luna routing succeeded when the runtime surface cannot express the requested model override.

## Installation / local development

This repo contains a repo-scoped marketplace at `.agents/plugins/marketplace.json` and the plugin at `plugins/axiom/`.

### Repo marketplace

1. Clone/extract the repository.
2. Open Codex from this repository root.
3. In Codex CLI, open `/plugins` and install **Axiom** from the **Axiom Local** marketplace.
4. Start a new session after installation so bundled skills are loaded.

On builds where plugins are still feature-gated, launch Codex with the plugin feature enabled before opening `/plugins`.

### Skill-only development shortcut

For local skill iteration without plugin installation, copy or symlink:

```text
plugins/axiom/skills/axiom
```

into:

```text
~/.agents/skills/axiom
```

This is only a development shortcut; the distributable form is the plugin.

## Invocation model

The Axiom skill allows implicit invocation. Its description is intentionally scoped to **non-trivial software engineering where delegation, context isolation, review, or Git coordination materially helps**.

You can also invoke it explicitly with `$axiom`.

Examples that should normally trigger Axiom:

- “Implement this feature across API, persistence, and tests.”
- “Refactor this subsystem without losing the original behavior.”
- “Investigate this large regression and fix it.”
- “Make this change, but keep the main agent context small.”

Examples that should normally stay simple:

- “Fix this typo.”
- “Rename this local variable.”
- “Explain what this function does.”

## Repository layout

```text
.
├── .agents/plugins/marketplace.json
├── plugins/axiom/
│   ├── .codex-plugin/plugin.json
│   ├── README.md
│   └── skills/axiom/
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       └── references/
│           ├── codex-0.147-subagents.md
│           ├── context.md
│           ├── delegation.md
│           ├── git.md
│           └── review.md
├── docs/
│   ├── DESIGN.md
│   ├── SCENARIOS.md
│   └── SOURCES.md
├── tests/
└── tools/
```

`skills/axiom/agents/openai.yaml` is **skill metadata**, not a custom subagent profile. Axiom installs no worker/reviewer TOML profiles.

## Validation

No third-party Python packages are required.

```bash
python tools/validate.py
python -m unittest discover -s tests -v
```

Build release archives with:

```bash
python tools/package_release.py --output-dir dist
```

## License

MIT
