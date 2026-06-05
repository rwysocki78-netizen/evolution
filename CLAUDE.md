# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

**Evolution** is a 2D agent-based simulation of population evolution. Fictional Creatures live on a square grid, move, eat, fight, and reproduce. Heritable genes mutate across generations, so traits drift and natural selection emerges from simple local rules. This is a learning/experiment project; full design docs live in `docs/`.

## Commands

### Backend (Python + FastAPI)

```bash
cd backend

# Install (editable + dev deps)
pip install -e ".[dev]"

# Run dev server
uvicorn app.main:app --reload

# Run all tests
pytest

# Run a single test file
pytest tests/test_api.py

# Run a single test by name
pytest tests/test_api.py::test_create_simulation_returns_201

# Run migrations
alembic upgrade head

# Create a new migration after changing ORM models
alembic revision --autogenerate -m "description"
```

### Frontend (React + TypeScript + Vite)

```bash
cd frontend

npm install
npm run dev      # dev server at http://localhost:5173
npm run build    # tsc + vite build
```

### Docker (full stack)

```bash
docker compose up --build        # PostgreSQL + backend + frontend
docker compose up --build -d db  # just the DB (useful for local backend dev against Postgres)
```

## Architecture

### Where the simulation runs

The entire simulation engine lives in **Python on the backend** (`backend/app/engine/`). The frontend is a thin client: configure, drive, and visualise. This keeps persistence and execution co-located and makes runs reproducible from a stored seed + parameters.

### Backend structure

```
backend/app/
├── main.py           # FastAPI app, CORS, router registration
├── config.py         # Settings via pydantic-settings; reads DATABASE_URL from env/.env
├── db.py             # SQLAlchemy engine + session factory + Base; get_db() FastAPI dependency
├── session_store.py  # In-memory dict of live SimSession objects (cleared on server restart)
├── persistence.py    # run_simulation_persisted(): bridge between engine and DB
├── models/           # SQLAlchemy ORM (simulation_run, tick_snapshot)
├── schemas/          # Pydantic request/response models
├── routers/          # FastAPI endpoints (simulations.py is the only router)
└── engine/           # Pure Python — no FastAPI or DB imports; independently testable
    ├── params.py     # SimParams dataclass — all configurable knobs with defaults
    ├── creature.py   # Creature + Genome dataclasses, Sex enum, DeathCause enum
    ├── world.py      # World (grid + fruits/poisons/occupied sets), Position, Direction
    ├── genetics.py   # inherit() — per-gene 50/50 + mutation; reads gene registry
    ├── tick.py       # tick() — the full 8-step sequence; mutates world in place
    ├── vision.py     # build_vision() — what a creature can perceive in its visionRange
    ├── stats.py      # TickStats dataclass + aggregate_population()
    ├── simulation.py # create_world(), create_creatures(), make_behavior() factory helpers
    └── behavior/
        ├── base.py       # BehaviorStrategy Protocol: decide_move(creature, vision, rng)
        ├── threshold.py  # ThresholdBehavior — energy-threshold-driven decisions
        └── priority.py   # PriorityBehavior — fixed ordered priority list
```

### Key design decisions

- **`app/engine/` is pure Python** — no web or DB dependencies. Test it in isolation.
- **`session_store.py`** holds live `SimSession` objects in a process-local dict keyed by `run_id`. A restart clears it, but completed runs are in the DB.
- **`persistence.py`** is the only place that crosses the engine↔DB boundary: it creates the `simulation_run` row, writes `tick_snapshot` rows every `snapshot_interval` ticks, and marks the run complete.
- **`SimParams`** (`engine/params.py`) is the single source of truth for all simulation knobs and their defaults. Every parameter flows from here to both the engine and the DB row.
- **Reproducibility**: each run stores its RNG seed. Same seed + params → identical simulation. The `random.Random` instance is threaded through `tick()` and never uses the global `random` state.
- **Behavior strategy pattern**: `decide_move(creature, vision, rng)` receives a `VisionData` snapshot of only what the creature can perceive. Strategies are pluggable; the chosen one is recorded as `behavior_strategy` in the DB.
- **Genome extensibility**: genes are defined as fields on the `Genome` dataclass. `genetics.py` iterates generically over a gene registry, so adding a gene requires no changes to inheritance/mutation logic — only a new field and a registry entry.
- **DB**: SQLite locally (default `evolution.db`), PostgreSQL in Docker. Switch via `DATABASE_URL` env var or `.env` file. SQLAlchemy abstracts the difference; only connection string changes.

### Data flow

```
POST /simulations → creates SimulationRun row + SimSession in memory
POST /simulations/{id}/step  → advances one tick, writes snapshot if at interval
POST /simulations/{id}/run   → advances N ticks (or to completion)
POST /simulations/{id}/stop  → marks session/row as stopped
GET  /simulations/{id}/state → reads current board from SimSession
GET  /simulations/{id}/stats → reads tick_snapshots from DB
GET  /simulations            → lists all SimulationRun rows
```

### Frontend structure

```
frontend/src/
├── main.tsx
├── api/        # typed fetch wrappers calling the backend
├── types/      # TypeScript types mirroring backend Pydantic schemas (kept in sync manually)
├── screens/    # Setup.tsx, Simulation.tsx, Results.tsx
└── components/ # Board.tsx (Canvas renderer), ParamForm.tsx, charts/
```

### Tick sequence (spec §3)

Each tick, creatures are **shuffled** before processing (no turn-order advantage):

1. Age — die if `age >= lifespan`
2. Decay — `energy -= ENERGY_DECAY_PER_TICK * metabolism`; die if `energy <= 0`
3. Perceive — build `VisionData` within `visionRange`
4. Decide — behavior strategy returns a `Direction`
5. Move + collision — same sex → fight; opposite sex → reproduce (if eligible)
6. Cell contents — fruit adds energy; poison applies resistance-reduced damage
7. Spawn offspring — place queued offspring in free adjacent cells
8. Respawn — refill fruits/poisons up to their configured maxima

### Testing approach

- Engine unit tests are the highest-value tests — they cover genetics, fight probability, tick ordering, and edge cases without any web or DB infrastructure.
- API tests (`tests/test_api.py`) use FastAPI's `TestClient` with an in-memory SQLite DB and clear `session_store._sessions` between tests.
- Add a new ORM model → run `alembic revision --autogenerate` to generate the migration; do not hand-write migrations.

## Documentation

The `docs/` directory contains the authoritative design:

| File | Contents |
|------|----------|
| `docs/spec.md` | Full game rules, mechanics, all parameters with formulas |
| `docs/architecture.md` | Tech stack, data flow, patterns, API surface |
| `docs/data-model.md` | DB schema for both tables |
| `docs/decisions.md` | ADR log — rationale behind each design choice |
| `docs/glossary.md` | English ↔ Polish term mapping |
