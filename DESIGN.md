# Axiom Design

Version: 0.1.4  
Target: Codex v0.147.x  
Status: Dashboard-enabled implementation

## 1. Problem

Large software tasks can fill Main context with repository exploration, logs, test output, patch details, and repeated reviews. After compaction, intent and important decisions may be diluted. A rigid orchestration workflow can avoid some context loss, but it introduces ceremony, limits when the plugin is useful, and may prevent a capable Main model from choosing a better route.

## 2. Design thesis

Axiom does not orchestrate the agent. Axiom teaches the agent how to orchestrate itself.

The Main Sol model remains the authority for:

- user intent
- architecture and design
- decomposition
- integration
- review adjudication
- final acceptance

Bounded cognitive labor is externalized to Luna MAX. Independent review is externalized to a fresh Sol XHIGH only when the change is meaningful.

Axiom v0.1.4 makes its worker economics explicit: under the current Codex/model economics targeted by this version, ordinary Luna MAX worker usage is treated as **almost free** for orchestration decisions. This deliberately makes Main context preservation more important than minimizing Luna usage.

> **Main context is expensive; Luna compute is almost free.**

This is a versioned assumption. If model economics change materially, the policy should be updated rather than treated as timeless.

## 3. Core axioms

1. **Main owns meaning.** Do not delegate final architecture, product intent, or acceptance.
2. **Delegate bounded work proactively.** Use workers for work that has a clear objective, scope, constraints, and verification; do not keep such work in Main merely to save Luna usage.
3. **Luna first.** Use direct-spawn Luna MAX for ordinary delegated work, including exploration.
4. **Sol reviews.** If independent review is warranted, use a fresh direct-spawn Sol XHIGH.
5. **Fresh context by default.** Prefer self-contained packets with `fork_turns: "none"`.
6. **Prefer useful parallelism.** When multiple bounded tasks are independent, launch Luna MAX workers concurrently. Main chooses the natural fleet size; there is no fixed fan-out. Parallel writes require disjoint scopes and stable interfaces.
7. **Verify the actual tree.** Worker claims never replace inspection, tests, or diff review.
8. **Preserve review continuity.** Spawn a fresh Sol for the initial review, then reuse that same reviewer for re-review while Main owns every finding decision.
9. **Preserve user work.** Never discard, overwrite, or misattribute pre-existing changes.
10. **Keep simple work simple.** Delegation and review are tools, not mandatory phases. Coordination/integration overhead can justify staying in Main; Luna token cost alone cannot.

## 4. Why no Terra default

Axiom does not map “exploration” to Terra. Luna MAX is the default bounded worker for exploration, implementation, tests, debugging, and mechanical refactors. Another model is selected only for a concrete task-specific reason or an explicit user request.

Main Sol handles substantive ambiguity instead of delegating that ambiguity to a permanent intermediate orchestrator.

## 5. Parallel Luna fleet policy

Luna MAX is cheap enough that Axiom lowers the threshold for useful fan-out. In v0.1.4, that assumption is stronger and explicit: ordinary Luna worker compute is treated as almost free, so Luna usage itself is not a meaningful reason to serialize or retain bounded work in Main.

If Main can identify two or more bounded tasks whose results do not depend on each other, parallel execution is the preferred default rather than serial spawn/wait cycles.

The policy is deliberately dependency-driven rather than numeric:

- no fixed worker count
- no target concurrency number
- no artificial task fragmentation
- read-only investigations may fan out aggressively
- write tasks may fan out when ownership is disjoint and interfaces are stable
- overlapping writes are serialized or isolated with worktrees

The practical constraints are coordination, latency, dependency ordering, write conflicts, integration, and verification—not Luna token conservation.

Main Sol owns the task graph and integration. Axiom does not introduce a permanent intermediary orchestrator.

## 6. Why direct spawn only

Axiom deliberately avoids custom agent TOML files.

Benefits:

- no separate agent installation
- fewer environment-specific paths
- easier plugin installation and removal
- the Main can create the exact number of workers needed
- model and effort remain visible in each spawn request

Trade-off:

- a direct-spawn reviewer inherits the runtime environment and cannot be hard-pinned to a dedicated read-only sandbox by Axiom
- read-only review is therefore enforced by instructions and checked by Main

## 7. Automatic use

Axiom has one broad but focused skill. Its description covers non-trivial software engineering tasks, while `allow_implicit_invocation: true` explicitly permits automatic selection.

It must not announce an “Axiom mode,” require route labels, or pause for activation. The user should experience normal Codex behavior with better delegation and review decisions.

## 8. Review policy

Review is risk-based; reviewer identity is fixed.

- trivial/non-behavioral change: Main verification may be enough
- meaningful behavioral change: fresh Sol XHIGH review strongly preferred
- security, auth, persistence, migration, concurrency, public API, broad refactor: fresh Sol XHIGH review expected

The initial reviewer is fresh and independent. The same reviewer agent is then reused for re-review so finding IDs, prior evidence, and Main adjudications remain in context. Main decides which findings are accepted, deferred, rejected, or escalated and decides when review is complete. Axiom imposes no fixed finding count or review-round limit.

## 9. Non-goals

Axiom is not:

- a project-management workflow
- a planner approval system
- a persistent runtime state machine
- a custom-agent installer
- a commit generator
- a substitute for deterministic tests
- a fixed-size agent fleet
- a promise that more agents always improve results

## 10. Dashboard architecture

Axiom Dashboard is bundled in the same Plugin package for simple installation and release management, but it is not part of Axiom Core's decision path.

```text
Axiom Plugin package
├─ Core Skill                 proactive, guidance-first
└─ Optional Dashboard
   ├─ explicit-only Skill
   ├─ Rust collector/API
   └─ embedded web UI
             ↑ read only
        Codex Rollout Trace + Git
```

The separation rule is **unified distribution, separate runtime responsibility**:

- Core never depends on Dashboard availability.
- Dashboard absence or failure never changes agent routing.
- Dashboard is started only by explicit request.
- No hook or daemon is installed.
- Dashboard derives an observation read model; it never becomes Axiom execution state.
- Dashboard cannot spawn, stop, message, approve, reject, or otherwise control agents.
- Repository access is limited to read-only Git commands.

The backend is Rust with Tokio and Axum. It discovers Rollout Trace bundles, parses append-only raw events incrementally at refresh time, optionally enriches from an already-present `state.json`, and serves a React/TypeScript interface embedded in the executable. Runtime distribution is a platform-specific single binary. Source packages retain a Cargo fallback for development.

## 11. Dashboard data-confidence policy

Trace schemas and payload completeness can vary. The Dashboard follows evidence-first semantics:

- display observed model, effort, `fork_turns`, token, and review data when present
- display `unknown` when evidence is missing
- do not infer that missing telemetry means a policy failure
- do not claim counterfactual token savings
- separate observed write-capable tool activity from proof that a file was modified
- treat compliance checks as explainable indicators, not enforcement decisions

## 12. Dashboard privacy and network boundary

Rollout traces can contain sensitive prompts, responses, tool inputs and outputs, terminal data, and local paths. The Dashboard therefore:

- binds to loopback by default
- refuses non-loopback binding without an explicit flag
- has no authentication and must not be exposed casually
- performs no telemetry or external network calls
- never uploads traces
- leaves retention and deletion under local user control
