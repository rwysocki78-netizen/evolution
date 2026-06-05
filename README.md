# Evolution

A 2D agent-based simulation of population evolution. Fictional **Creatures**
(PL: *Stworzenia*) live on a square grid, move, eat, fight, reproduce, and die.
Heritable genes mutate across generations, so traits drift and natural selection
emerges from simple local rules.

This is a learning project — the goals are to practice building with Claude and a
modern full-stack toolchain, and to experiment with how different creature
behaviours change population outcomes.

## Status

Pre-development. Design is complete; see `docs/`.

## Documentation

| File | Purpose |
|------|---------|
| [docs/spec.md](docs/spec.md) | Game rules, mechanics, full parameter list |
| [docs/architecture.md](docs/architecture.md) | Tech stack, structure, data flow, patterns |
| [docs/data-model.md](docs/data-model.md) | Database schema for stored simulation results |
| [docs/tasks.md](docs/tasks.md) | Development roadmap, broken into phases |
| [docs/decisions.md](docs/decisions.md) | Design decision log (ADR) with rationale |
| [docs/glossary.md](docs/glossary.md) | English ↔ Polish term mapping |

## Tech Stack (summary)

- **Frontend:** React + TypeScript, Canvas for board rendering
- **Backend:** Python + FastAPI
- **Persistence:** SQLAlchemy ORM + Alembic migrations — SQLite locally, PostgreSQL when hosted
- **Deployment:** Docker Compose

## Running locally

> To be filled in once the backend and frontend skeletons exist.

```
# backend
cd backend && uvicorn app.main:app --reload

# frontend
cd frontend && npm run dev
```

## Core idea in one paragraph

The board is a square grid with hard walls. Each tick, every Creature ages,
loses energy, looks around within its vision range, decides where to move, and
acts. Moving onto another Creature of the same sex triggers a fight (resolved
probabilistically by energy weight); onto the opposite sex triggers reproduction
(if both have enough energy). Fruits restore energy, poisons drain it. Offspring
inherit each gene from one parent or the other, with a chance of mutation. Over
many ticks, the genome distribution of the surviving population shifts — that
shift is the "evolution" the project is built to observe.
