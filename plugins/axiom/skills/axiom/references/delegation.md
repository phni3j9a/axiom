# Delegation guide

## Main owns the decisions

Keep these in the Main session:

- user intent and material ambiguity;
- architecture, interfaces, data model, and responsibility boundaries;
- decomposition and dependency ordering;
- whether an observed problem changes the plan;
- integration of competing approaches;
- final diff inspection, verification judgment, and acceptance.

A worker may make local implementation choices inside an already-defined boundary, but it must not silently expand scope or redesign an unresolved interface.

## Luna MAX is the default worker

Treat Luna MAX as a general-purpose bounded worker, not merely an implementer. Appropriate assignments include:

- codebase exploration with a concrete question;
- implementation of a defined slice;
- test creation and targeted debugging;
- repetitive or mechanical refactors;
- dependency tracing;
- log/test-output analysis;
- documentation or migration of clearly specified content.

Do not choose Terra simply because a task is exploratory, context-heavy, or read-heavy. Axiom's default delegated model is Luna MAX. Use another model only for a concrete task-specific reason or explicit user request.

## Delegation threshold

Good delegation substitutes for Main work. Bad delegation duplicates it.

Prefer delegation when the packet can be self-contained and the expected context/noise saved in Main is larger than the coordination cost. Prefer Main for a two-line fix, unresolved architecture, or work whose core value is the design judgment itself.

## Parallelism

Parallelize independent searches freely when results do not depend on one another. Parallelize writes only when ownership is disjoint enough that two workers will not edit the same logical surface.

If write scopes overlap, use one worker, sequential delegation, or isolated worktrees. Never spawn a fleet just because concurrency is available.

## Worker packet

Every write-capable delegated task should contain enough information to stand alone:

### OBJECTIVE
What outcome is required and why.

### OWNERSHIP
Exact files/modules or logical scope the worker owns. State what it must not edit when relevant.

### INTERFACES
Contracts that must remain stable: APIs, types, schemas, behavior, call sites, or integration assumptions.

### CONSTRAINTS
Design decisions already made, forbidden shortcuts, dependencies, compatibility requirements, and non-goals.

### VERIFICATION
Commands/checks to run and concrete completion criteria.

Also request a compact return containing:

- files changed;
- implementation summary;
- verification run and result;
- risks/assumptions;
- anything Main must decide.

For read-only exploration, simplify the packet but still state the question, scope, constraints, and expected output.

## Worker correction

If the worker misunderstood the packet, correct the packet and reuse/follow up only when preserving that worker's context is genuinely useful. If independence is more valuable, spawn a fresh Luna. Do not create an automatic repair loop.
