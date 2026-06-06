# Evolution — Development Tasks

Version: 1.0
Status: Backlog

Build order is bottom-up: a tested simulation engine first, then persistence,
then the API, then the UI. This means the riskiest, rule-heavy code is validated
before any UI is built on top of it.

Legend: `[ ]` todo · `[~]` in progress · `[x]` done

---

## Phase 0 — Project scaffolding

- [x] Initialise repo, `.gitignore`, license
- [x] `backend/` Python project (`pyproject.toml`, venv, FastAPI, SQLAlchemy, Alembic, pytest)
- [x] `frontend/` React + TypeScript project (Vite)
- [x] `docker-compose.yml` (frontend, backend, PostgreSQL services)
- [x] Backend "hello world" endpoint reachable from frontend
- [x] Decide and document config for DB URL switching (SQLite vs PostgreSQL)

## Phase 1 — Simulation engine (pure Python, no web/DB)

This is the core. Build and unit-test in isolation.

- [x] `Position`, `Direction`, `Sex` primitives
- [x] `Genome` dataclass + gene registry (names, types, mutate fns)
- [x] `Creature` (state + genome)
- [x] `World` (grid, walls, fruit/poison placement, occupancy lookup)
- [x] `genetics.py` — inheritance (50/50 per gene) + mutation
  - [x] Unit test: child genes come from one parent or other
  - [x] Unit test: mutation rate/magnitude behave as configured
- [x] Fight resolution (energy-weighted probability, winner survives min 1)
  - [x] Unit test: win probability matches energy ratio over many trials
- [x] Reproduction (eligibility, cost, litter size from weights, queued placement)
  - [x] Unit test: no free cells → cost paid, offspring lost
  - [x] Eligibility includes `age >= MATURITY_AGE` (juveniles cannot reproduce)
- [x] Energy ceiling: clamp to `MAX_ENERGY` (or juvenile cap) after every gain
  - [x] Unit test: juvenile capped at `MAX_ENERGY * JUVENILE_MAX_ENERGY_FACTOR`, full cap after maturity
- [x] Poison resistance: `resistance` continuous gene + multiplicative damage
  - [x] Unit test: damage = `round(POISON_ENERGY_VALUE * (1-p) ** resistance)`; mutation floored at 0
- [x] `VisionData` builder (scan visionRange, 8 directions)
- [x] Behaviour interface + `ThresholdBehavior` + `PriorityBehavior`
- [x] `tick.py` — full tick sequence with **randomised order**
  - [x] Unit test: death by age, death by starvation, walls block movement
  - [x] Unit test: deterministic given a fixed seed
- [x] `stats.py` — aggregate per-tick statistics

## Phase 2 — Persistence

- [x] SQLAlchemy models: `simulation_run`, `tick_snapshot`
- [x] Alembic initial migration
- [x] Write run row on create; update status/finished_at on completion
- [x] Write `tick_snapshot` rows respecting `snapshot_enabled` / `snapshot_interval`
- [ ] Verify SQLite locally; verify PostgreSQL via Docker

## Phase 3 — API

- [x] Pydantic schemas for parameters, state, stats
- [x] `POST /simulations` (create from parameters, return id + seed)
- [x] `POST /simulations/{id}/step` and `/run`
- [x] `POST /simulations/{id}/stop`
- [x] `GET /simulations/{id}/state` (board state for rendering)
- [x] `GET /simulations` (history) and `GET /simulations/{id}`
- [x] `GET /simulations/{id}/stats` (time series)
- [x] API tests via FastAPI test client

## Phase 4 — Frontend shell & config

- [x] App shell + screen routing (Setup / Simulation / Results)
- [x] Shared TS types mirroring Pydantic schemas
- [x] Typed API client
- [x] `Setup` screen: full parameter form with sensible defaults + validation
- [ ] Parameter presets (save/load a config) — nice-to-have

## Phase 5 — Board rendering

- [x] `Board.tsx` Canvas renderer (grid, creatures by sex, fruits, poisons)
- [x] Run / pause / step controls
- [x] Tick counter + live population readout (with ♂/♀ breakdown)
- [x] Adjustable playback speed (slider, 0.5–20 t/s)

## Phase 6 — Results & statistics

- [ ] Population-over-time chart
- [ ] Trait-drift charts (genome averages over time)
- [ ] Death-cause breakdown
- [ ] Births vs deaths
- [ ] Run history list with parameter summary
- [ ] Compare two runs side by side — nice-to-have

## Phase 7 — Deployment

- [ ] Dockerfiles for frontend and backend
- [ ] `docker-compose up` brings up the full stack with PostgreSQL
- [ ] README run instructions verified on a clean machine

---

## Experiments backlog (post-v1, the fun part)

- [ ] Threshold vs. priority behaviour: compare outcomes under identical params
- [ ] Mixed populations: some creatures use one strategy, some another
- [ ] Sweep mutation rate and observe trait-drift speed
- [ ] Scarcity experiments: low fruit / high poison and watch selection pressure
- [ ] Add a new gene (e.g. `speed`) end-to-end to validate extensibility
- [ ] Acquired poison tolerance: `poisonsEaten` counter, `POISON_TOLERANCE_THRESHOLD` (eat X → +1 resistance point)
- [ ] Lamarckian inheritance of acquired resistance + `RESISTANCE_INHERITANCE_FACTOR` brake; Darwinian/Lamarckian toggle to compare dynamics (see ADR-025)
