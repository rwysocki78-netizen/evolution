# Evolution — Architecture

Version: 1.0
Status: Complete, ready for development

This document describes **how** the system is built. For game rules see
[spec.md](spec.md). For the database schema see [data-model.md](data-model.md).

---

## 1. Tech stack

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | React + TypeScript | Component model fits config panels and stats dashboards; strong typing |
| Board rendering | HTML5 Canvas | Efficient for grid redraws each tick; avoids DOM overhead |
| Backend | Python + FastAPI | Async, auto-generated API docs, clean type hints via Pydantic |
| ORM | SQLAlchemy | Engine-agnostic; same code for SQLite and PostgreSQL |
| Migrations | Alembic | Python-native schema versioning |
| DB (local) | SQLite | File-based, zero setup |
| DB (hosted) | PostgreSQL | Proper querying/comparison of many runs |
| Deployment | Docker Compose | Same codebase local and hosted; swap DB via connection string |

The SQLite → PostgreSQL switch is a single change to the connection string;
SQLAlchemy abstracts the rest.

---

## 2. Where the simulation runs

**Decision: the simulation engine lives in the Python backend, not the browser.**

Rationale:
- Results must be persisted to the DB — the engine and persistence belong together.
- Keeps the simulation deterministic and reproducible from a stored seed +
  parameters, independent of browser performance.
- The frontend becomes a thin client: configure, drive, and visualise.

The frontend renders state the backend produces. (A future optimisation could
mirror the engine in the browser for smooth animation, but v1 keeps a single
source of truth on the server.)

---

## 3. Project structure

```
evolution/
├── README.md
├── docker-compose.yml
├── docs/
│   ├── spec.md
│   ├── architecture.md
│   ├── data-model.md
│   ├── tasks.md
│   ├── decisions.md
│   └── glossary.md
│
├── backend/
│   ├── pyproject.toml
│   ├── alembic/                 # migrations
│   └── app/
│       ├── main.py              # FastAPI entry point
│       ├── config.py            # settings, DB URL
│       ├── db.py                # SQLAlchemy session/engine
│       ├── models/              # SQLAlchemy ORM models (DB tables)
│       │   ├── simulation_run.py
│       │   └── tick_snapshot.py
│       ├── schemas/             # Pydantic request/response models
│       ├── routers/             # FastAPI endpoints
│       │   ├── simulations.py
│       │   └── stats.py
│       └── engine/              # the simulation core (pure Python, no web deps)
│           ├── world.py         # grid, fruits, poisons
│           ├── creature.py      # Creature + Genome
│           ├── genetics.py      # inheritance + mutation
│           ├── tick.py          # the tick sequence
│           ├── stats.py         # per-tick stat aggregation
│           └── behavior/        # pluggable decision strategies
│               ├── base.py      # BehaviorStrategy interface
│               ├── threshold.py
│               └── priority.py
│
└── frontend/
    ├── package.json
    └── src/
        ├── main.tsx
        ├── api/                 # typed calls to the backend
        ├── types/               # shared TS types (mirror Pydantic)
        ├── screens/
        │   ├── Setup.tsx        # parameter configuration
        │   ├── Simulation.tsx   # run/pause/step + board
        │   └── Results.tsx      # charts, history
        └── components/
            ├── Board.tsx        # Canvas renderer
            ├── ParamForm.tsx
            └── charts/
```

**Key separation:** `app/engine/` is pure Python with no FastAPI or DB imports.
It can be unit-tested in isolation and could later run as a CLI or be ported.
Persistence and the web layer wrap around it.

---

## 4. Behaviour: Strategy pattern

Movement decisions are isolated behind an interface so different decision models
can be swapped — or even assigned per-creature for competing populations.

```python
# engine/behavior/base.py
class BehaviorStrategy(Protocol):
    name: str
    def decide_move(self, creature: Creature, vision: VisionData) -> Direction: ...
```

```python
# engine/behavior/threshold.py
class ThresholdBehavior:
    name = "threshold"
    def decide_move(self, creature, vision):
        # decisions emerge from hunger/safe thresholds
        ...
```

```python
# engine/behavior/priority.py
class PriorityBehavior:
    name = "priority"
    def decide_move(self, creature, vision):
        # fixed ordered priority list
        ...
```

`VisionData` is the world snapshot passed to a strategy — it deliberately exposes
only what a Creature could perceive:

```python
@dataclass
class VisionData:
    fruits: list[Position]
    poisons: list[Position]
    creatures: list[PerceivedCreature]   # position, sex, energy
    empty_directions: list[Direction]
```

The chosen strategy for a run is recorded as `behavior_strategy` in the DB so
results are tied to the decision model that produced them.

---

## 5. Genome extensibility

The genome is a structured but open container. Inheritance and mutation iterate
over its genes generically, so adding a new gene requires no change to those
functions:

```python
@dataclass
class Genome:
    lifespan: int
    vision_range: int
    hunger_threshold: int
    safe_threshold: int
    metabolism: float
    aggression: float
    # add a new gene here → it automatically inherits & mutates
```

`genetics.py` reads gene definitions (name, type, mutate-fn) from a single
registry, keeping inheritance/mutation logic decoupled from the specific gene set.

---

## 6. Determinism & reproducibility

A run stores its full parameter set and a random **seed**. Re-running with the
same seed + parameters reproduces the same simulation. This is what makes stored
results meaningful and comparable, and makes bugs reproducible.

---

## 7. Data flow

```
SETUP screen
   │  POST /simulations  (parameters)
   ▼
Backend creates simulation_run row (status=running), instantiates engine
   │
   ▼
SIMULATION screen drives ticks
   │  POST /simulations/{id}/run   (run N ticks / to completion)
   │  POST /simulations/{id}/step  (single tick)
   ▼
Engine advances ticks → writes tick_snapshot rows (every SNAPSHOT_INTERVAL)
   │  GET /simulations/{id}/state  → board state for Canvas
   ▼
On completion: simulation_run.status=completed, finished_at set
   │
   ▼
RESULTS screen
   │  GET /simulations            (history list)
   │  GET /simulations/{id}/stats (time series for charts)
   ▼
Charts render trait drift, population curves, death causes, etc.
```

---

## 8. API surface (initial)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/simulations` | Create a run from parameters; returns run id |
| POST | `/simulations/{id}/run` | Advance many ticks (or to completion) |
| POST | `/simulations/{id}/step` | Advance a single tick |
| POST | `/simulations/{id}/stop` | Stop a running simulation |
| GET | `/simulations/{id}/state` | Current board state for rendering |
| GET | `/simulations` | List past runs (history) |
| GET | `/simulations/{id}` | Run metadata + parameters |
| GET | `/simulations/{id}/stats` | Per-tick snapshot time series |

FastAPI auto-generates interactive docs at `/docs`.

---

## 9. Type sharing between backend and frontend

Pydantic schemas define the contract on the backend. The frontend mirrors them in
`frontend/src/types/`. Keeping these aligned manually is fine for v1; if drift
becomes a problem, generate TS types from the OpenAPI schema FastAPI already
produces.

---

## 10. Testing strategy

- **Engine unit tests** (most valuable): genetics (inheritance/mutation
  distributions), fight resolution probabilities, tick ordering, edge cases
  (no free cells on reproduction, walls).
- **API tests**: endpoint contracts via FastAPI's test client.
- **Frontend**: light component tests; the board renderer is mostly visual.

The pure-Python engine is the part most worth testing thoroughly, since it
contains all the rules and the least obvious behaviour.
