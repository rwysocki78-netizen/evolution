# Evolution — Decision Log (ADR)

A short record of the significant design decisions and **why** they were made.
Each entry is dated and numbered. New decisions append; superseded ones are
marked rather than deleted.

Format: ID · Decision · Context/Rationale · Alternatives considered.

---

### ADR-001 — Square grid, discrete time
**Decision:** The board is a square grid; time advances in discrete ticks.
**Rationale:** Integer positions and a 2D-array board are simple to render, debug,
and serialise. Discrete ticks give a clear loop and make ordering of effects
explicit and controllable.
**Alternatives:** Continuous space (more realistic movement, much harder to render
and reason about); real-time loop (timing-dependent, non-reproducible).

### ADR-002 — Name: "Creature" (PL: *Stworzenie*)
**Decision:** The species is called *Creatures*.
**Rationale:** Clear English identifier (`Creature`, `creatures[]`), clean plural,
no collision with common programming terms, translates naturally to Polish for
presentation.
**Alternatives:** Pseudo-Latin (*Genari*), playful coinages (*Morphlings*,
*Sparks*), Polish-first (*osobniki*). Rejected in favour of simplicity.

### ADR-003 — 8-direction movement
**Decision:** Creatures move in any of 8 directions, one cell per tick.
**Rationale:** Richer movement than 4-direction without added complexity; vision
already spans all 8 directions.

### ADR-004 — Hard walls at board edges
**Decision:** Edges are impassable.
**Rationale:** Creates a bounded environment and density effects near edges.
**Alternatives:** Wrap-around torus (removes edges/corners as distinct habitats).

### ADR-005 — Energy as health
**Decision:** A single `energy` value serves as both health and fuel; 0 = death.
**Rationale:** One resource keeps the model simple and ties every action
(movement decay, fighting, reproduction, eating) to one currency, which makes
trade-offs legible.

### ADR-006 — Fight: energy-weighted random
**Decision:** `P(A wins) = energyA / (energyA + energyB)`. Loser dies; winner
takes loser's energy minus fight cost, surviving with at least 1.
**Rationale:** Healthier creatures usually win but not always — avoids total
determinism while still rewarding fitness. No separate strength gene needed.
The min-1 floor prevents mutual annihilation and keeps a fight from being lethal
to the victor.
**Alternatives:** Highest energy always wins (too deterministic); dedicated
strength trait (more depth, more complexity — deferred).

### ADR-007 — Reproduction requires minimum energy
**Decision:** Both parents must meet `REPRODUCTION_MIN_ENERGY`; both pay
`REPRODUCTION_ENERGY_COST`.
**Rationale:** Creates automatic selection pressure — only creatures that gather
enough energy reproduce, so energy-gathering traits propagate.

### ADR-008 — Reproduction with no free cells: pay cost, lose offspring (Option A)
**Decision:** If there is no free adjacent cell, the energy cost is still paid and
the un-placeable offspring are lost.
**Rationale:** Makes overcrowding a genuine selective pressure; creatures whose
behaviour spreads them out reproduce more successfully.
**Alternatives:** Block reproduction with no cost (crowding becomes free); partial
litter scaled to free cells (reasonable middle ground, kept as fallback).

### ADR-009 — Lifespan is heritable and per-individual
**Decision:** Each creature has its own `lifespan` gene.
**Rationale:** Lets longevity itself evolve, rather than being a global constant.

### ADR-010 — Inheritance: per-gene 50/50, plus mutation
**Decision:** Each gene independently comes from one parent or the other (50/50);
each gene may then mutate with probability `MUTATION_RATE`.
**Rationale:** Simpler and more extensible than "exactly half each", and works for
any number of genes. Mutation is essential — without it traits only regress to the
mean and no real evolution occurs.

### ADR-011 — Litter size from configurable weighted probabilities
**Decision:** Number of offspring drawn from `REPRODUCTION_WEIGHTS`
(`[{children, weight}, ...]`).
**Rationale:** Tunable reproductive strategy; lets experiments vary fecundity.

### ADR-012 — Randomised processing order each tick
**Decision:** Shuffle the creature list every tick before processing.
**Rationale:** Fixed order (by id/position) would give some creatures a permanent
first-mover advantage (first pick of fruit, first to attack), biasing results.
Random order is the standard fix in agent-based simulations.

### ADR-013 — Behaviour behind a Strategy interface
**Decision:** Movement decisions are encapsulated in swappable
`BehaviorStrategy` implementations (threshold, priority, …).
**Rationale:** A core goal is experimenting with how decision models change
outcomes. The interface allows swapping strategies — even per-creature — without
touching the engine. Strategies receive only a `VisionData` snapshot.

### ADR-014 — Genome as an open, registry-driven container
**Decision:** Genes are defined in one registry; inheritance/mutation iterate
generically over it.
**Rationale:** Adding a gene shouldn't require editing inheritance logic. Keeps the
set of heritable traits easy to extend, which the user explicitly wants.

### ADR-015 — Simulation engine runs on the backend
**Decision:** The engine lives in Python on the server, not in the browser.
**Rationale:** Results must be persisted; engine and persistence belong together.
Server-side execution is reproducible from seed + parameters and independent of
browser performance. Frontend is a thin client.
**Alternatives:** Browser-side engine (smoother animation, but splits the source of
truth and complicates persistence) — possible future optimisation.

### ADR-016 — Persistence: SQLAlchemy, SQLite local / PostgreSQL hosted
**Decision:** One ORM (SQLAlchemy + Alembic); SQLite for local, PostgreSQL when
deployed, switched via connection string.
**Rationale:** Same codebase runs locally and hosted with no rewrite — matches the
"local now, deployable later" requirement.

### ADR-017 — Backend language: Python + FastAPI
**Decision:** FastAPI over Node.js/Express.
**Rationale:** User preference; FastAPI gives async, auto docs, and strong typing
via Pydantic.

### ADR-018 — Store every run; snapshot frequency configurable & toggleable
**Decision:** Every run is persisted. Per-tick snapshots are written every
`SNAPSHOT_INTERVAL` ticks and can be turned off entirely.
**Rationale:** Storing every tick can mean thousands of rows per run; making
frequency configurable controls DB size while preserving run-level results.

### ADR-019 — No individual creature/lineage tracking in v1
**Decision:** Statistics are aggregate (population + genome averages); individual
creatures and family trees are not stored.
**Rationale:** Keeps the data model and engine simpler for v1. Genome averages are
denormalised into snapshots. Lineage tracking is noted as a future extension.

### ADR-020 — Reproducibility via stored seed
**Decision:** Each run stores its RNG seed alongside its parameters.
**Rationale:** Same seed + parameters reproduce a run exactly — essential for
comparing results and for reproducing bugs.
### ADR-021 — Global maximum energy (`MAX_ENERGY`)
**Decision:** A global `MAX_ENERGY` parameter caps every Creature's energy. Energy
is clamped to this ceiling after any gain (eating fruit, winning a fight).
**Rationale:** The juvenile energy rule (ADR-022) needs a defined ceiling to halve;
previously energy had no hard upper bound. A single global cap keeps the model
simple and gives a reference point for relative limits.
**Alternatives:** Per-individual max as a heritable gene (deferred — more depth,
more complexity); no cap at all (incompatible with the juvenile rule).

### ADR-022 — Maturity age as a reproduction gate (`MATURITY_AGE`, global)
**Decision:** Creatures may reproduce only when `age >= MATURITY_AGE`, added to the
existing eligibility check (ADR-007). While `age < MATURITY_AGE` the Creature is a
juvenile and its energy ceiling is reduced (see ADR-023). `MATURITY_AGE` is a global
parameter, not a gene.
**Rationale:** Introduces a juvenile life stage and an extra selective filter.
Kept global for v1: as a free gene it would simply be driven to its minimum
(earlier maturity is a pure advantage with no cost), a degenerate outcome.
**Alternatives:** Maturity age as a heritable gene (deferred — would need an
associated cost, e.g. correlated with higher lifespan, to be an interesting
trade-off).

### ADR-023 — Reduced juvenile energy cap (`JUVENILE_MAX_ENERGY_FACTOR`)
**Decision:** While `age < MATURITY_AGE`, a Creature's energy ceiling is
`MAX_ENERGY * JUVENILE_MAX_ENERGY_FACTOR` (default 0.5). On reaching maturity the
ceiling rises to the full `MAX_ENERGY`. Enforced by clamping after any energy gain.
**Rationale:** Makes the juvenile stage a genuine vulnerability — young Creatures
hold a smaller reserve, so surviving to maturity is itself selective pressure.
**Alternatives:** Define the juvenile cap relative to `INITIAL_ENERGY` instead of
`MAX_ENERGY` (rejected for consistency now that `MAX_ENERGY` exists).

### ADR-024 — Poison resistance as a continuous gene; multiplicative damage
**Decision:** Add a heritable **continuous** gene `resistance`. Poison damage is:
```
damage = round(POISON_ENERGY_VALUE * (1 - RESISTANCE_REDUCTION_PER_POINT) ** resistance)
energy -= damage
```
`resistance` is seeded by `INITIAL_RESISTANCE` (e.g. 0–2) and its mutation is
lower-bounded at 0. No floor on `damage` in v1 (sufficiently high resistance may
round to 0 damage — accepted).
**Rationale:** Multiplicative (diminishing) reduction is self-limiting — damage
asymptotes toward but never reaches zero or negative, so poison never becomes
beneficial and no hard cap on resistance is required. As an ordinary continuous
gene, `resistance` rides the existing inheritance pipeline (ADR-010) with no
special logic.
**Alternatives:** Additive reduction `(1 - p * points)` (rejected — reaches 100%
then goes negative, requires a cap); discrete integer gene (rejected for
consistency with the other continuous genes `metabolism` and `aggression`).

### ADR-025 — Darwinian inheritance for v1; acquired/Lamarckian resistance deferred
**Decision:** v1 inherits `resistance` **purely Darwinian** — only the inherited
baseline, via ADR-010 (50/50 from one parent + mutation). Deferred to a later
version: acquired resistance (`eat X poisons → +1 resistance point`),
`POISON_TOLERANCE_THRESHOLD` (the X), inheritance of acquired resistance
(Lamarckian model), `RESISTANCE_INHERITANCE_FACTOR` (the brake, only needed for the
Lamarckian model), the `poisonsEaten` per-Creature state, and a
Darwinian/Lamarckian toggle for experiments.
**Rationale:** Keeps v1 minimal — resistance is just another gene with zero
special-case code. In a Darwinian model starting from low resistance, new
resistance enters the gene pool through mutation and spreads by selection; the
poison-eating counter would be evolutionarily inert, so it is not worth its state
cost yet. The Lamarckian variant is retained as a planned experiment because the
contrast in dynamics — and the role of the eating counter — is itself worth
measuring.
**Alternatives:** Implement the Lamarckian model in v1 (deferred — more
per-Creature state and special inheritance logic).
