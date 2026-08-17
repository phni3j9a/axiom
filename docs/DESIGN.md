# Axiom design

## Purpose

Axiom exists to improve large software-engineering sessions without replacing the Main model's judgment with a rigid orchestration state machine.

The design assumes a strong Main model and treats subagents primarily as **context and labor isolation**.

## Ten principles

1. **Keep simple work simple.** Coordination must earn its cost.
2. **Main owns high-value reasoning.** User intent, architecture, interfaces, ambiguity, decomposition, integration, and final acceptance stay in Main.
3. **Delegate bounded work to protect Main context.** Exploration noise, logs, repetitive implementation detail, and test output are good candidates.
4. **Luna MAX is the default worker.** It is a general bounded worker, not only an implementer.
5. **Do not add a Terra lane by habit.** Exploration/read-heavy work is not by itself a reason to choose Terra.
6. **Fresh Sol is the independent reviewer.** Review and implementation use different fresh contexts and different model roles.
7. **Fresh packets beat inherited history.** Prefer self-contained packets and `fork_turns: "none"` when practical.
8. **Review findings are advice; Main adjudicates.** ACCEPT / DEFER / REJECT belongs to Main.
9. **Finding Freeze prevents review loops.** Round 2 verifies accepted fixes and directly-caused critical/major regressions rather than restarting review from zero.
10. **Git and memory are pragmatic tools.** Use coherent change boundaries, worktrees only when useful, and a tiny optional task anchor only when compaction risk justifies it.

## Why no fixed workflow

A fixed `spec -> plan -> run -> task review -> integration review -> gate -> finish` sequence gives predictable checkpoints, but it also turns ordinary development into a mode switch. Strong Main models can decide when planning, delegation, review, or a Git boundary is useful.

Axiom therefore supplies **decision rules and execution recipes** rather than mandatory phase transitions.

## Model topology

```text
Main: Sol XHIGH
  ├─ Luna MAX worker (0..N as useful)
  ├─ Luna MAX worker
  └─ fresh Sol XHIGH reviewer (when risk warrants)
```

There is no permanent orchestrator subagent. Main orchestrates directly.

## Why Luna is a general worker

The key distinction is not “explorer vs implementer.” It is:

- **judgment that must remain coupled to the user's intent** -> Main;
- **bounded work that can be specified and verified** -> Luna.

That includes repository exploration, dependency tracing, implementation, tests, debugging, and mechanical refactors.

## Review model

Review is risk-based rather than universally mandatory. When selected, it is always a fresh Sol direct spawn under Axiom.

Direct spawn does not rely on an installed custom read-only reviewer profile. The reviewer is instructed not to mutate and Main compares repository state before/after review. This is behavioral read-only enforcement, not a sandbox guarantee.

The first review produces a small set of important findings. Main adjudicates them. The second review is bounded verification; it is not permission to discover endless new improvements.

## Context model

Subagent output should return conclusions and evidence, not a transcript of every search/test step. Main can retain a small durable task anchor when work is likely to cross compaction. That anchor is an external memory aid, not Axiom runtime state.

## Git model

No one-task-one-commit invariant exists. Commits should reflect coherent, reviewable/revertible change boundaries when the project/user expects commits.

Parallel writes require disjoint ownership or worktrees. Main remains responsible for semantic integration even when Git can merge text.

## Deliberate non-goals

- no workflow state machine;
- no Run/Gate protocol;
- no custom subagent TOML installation;
- no hooks;
- no mandatory Spec/Plan files;
- no mandatory `/compact` step;
- no mandatory commits;
- no Terra-by-role routing;
- no auto-repair/review loop;
- no “spawn as many agents as possible” objective.

## Version boundary

The runtime recipe in `codex-0.147-subagents.md` is intentionally isolated because spawn-agent schemas and feature flags can change between Codex releases. When upgrading Codex, update that reference instead of rewriting the general engineering principles.
