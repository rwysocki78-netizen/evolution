# Evolution — Data Model

Version: 1.0
Status: Complete, ready for development

The database stores the result of **every** simulation run plus optional per-tick
statistics. No individual creatures are tracked (out of scope for v1 — see
[spec.md](spec.md#12-explicitly-out-of-scope-for-v1)).

Two tables: `simulation_run` (one row per run) and `tick_snapshot` (many rows per
run, one per sampled tick).

---

## Table: `simulation_run`

One row per simulation. Stores a full snapshot of the parameters so a run is
self-describing and reproducible.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | |
| `started_at` | DATETIME | |
| `finished_at` | DATETIME | Null while running |
| `status` | ENUM | `running` / `completed` / `stopped` |
| `seed` | INTEGER | RNG seed for reproducibility |
| `total_turns_configured` | INTEGER | |
| `total_turns_run` | INTEGER | May be < configured if population died out or stopped |
| `behavior_strategy` | VARCHAR | e.g. `threshold`, `priority` |
| `initial_population` | INTEGER | |
| **Board** | | |
| `board_size` | INTEGER | |
| **Vision** | | |
| `vision_range` | INTEGER | Default vision range |
| **Energy** | | |
| `initial_energy` | INTEGER | |
| `max_energy` | INTEGER | Global energy ceiling |
| `energy_decay_per_tick` | FLOAT | |
| `fight_energy_cost` | INTEGER | |
| `reproduction_energy_cost` | INTEGER | |
| `reproduction_min_energy` | INTEGER | |
| **Life stage** | | |
| `maturity_age` | INTEGER | Min age to reproduce |
| `juvenile_max_energy_factor` | FLOAT | Juvenile ceiling = `max_energy * factor` |
| **World** | | |
| `fruit_energy_value` | INTEGER | |
| `poison_energy_value` | INTEGER | |
| `resistance_reduction_per_point` | FLOAT | `p` in poison damage formula, 0..1 |
| `max_fruits` | INTEGER | |
| `max_poisons` | INTEGER | |
| **Mutation** | | |
| `mutation_rate` | FLOAT | |
| `mutation_magnitude` | FLOAT | |
| **Genome initial ranges** | | min/max used to seed starting population |
| `lifespan_min` | INTEGER | |
| `lifespan_max` | INTEGER | |
| `vision_range_min` | INTEGER | |
| `vision_range_max` | INTEGER | |
| `metabolism_min` | FLOAT | |
| `metabolism_max` | FLOAT | |
| `aggression_min` | FLOAT | |
| `aggression_max` | FLOAT | |
| `hunger_threshold_min` | INTEGER | |
| `hunger_threshold_max` | INTEGER | |
| `safe_threshold_min` | INTEGER | |
| `safe_threshold_max` | INTEGER | |
| `resistance_min` | FLOAT | e.g. 0 |
| `resistance_max` | FLOAT | e.g. 2 |
| **Reproduction** | | |
| `reproduction_weights` | JSON | Array of `{children, weight}` |
| **Snapshots** | | |
| `snapshot_enabled` | BOOLEAN | |
| `snapshot_interval` | INTEGER | Sample every N ticks; ignored if disabled |

---

## Table: `tick_snapshot`

One row per sampled tick. Written every `snapshot_interval` ticks when
`snapshot_enabled` is true.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | |
| `simulation_id` | INTEGER FK → `simulation_run.id` | Indexed |
| `tick` | INTEGER | |
| **Population** | | |
| `population_total` | INTEGER | |
| `population_male` | INTEGER | |
| `population_female` | INTEGER | |
| **Energy** | | |
| `avg_energy` | FLOAT | |
| `min_energy` | INTEGER | |
| `max_energy` | INTEGER | |
| **Events this tick** | | |
| `births` | INTEGER | |
| `deaths_total` | INTEGER | |
| `deaths_starvation` | INTEGER | |
| `deaths_age` | INTEGER | |
| `deaths_fight` | INTEGER | |
| `fights_total` | INTEGER | |
| `reproductions_successful` | INTEGER | |
| `reproductions_failed_space` | INTEGER | No free adjacent cell |
| `reproductions_failed_energy` | INTEGER | Below min energy |
| **World** | | |
| `fruits_on_board` | INTEGER | |
| `poisons_on_board` | INTEGER | |
| **Genome averages (trait drift)** | | |
| `avg_lifespan` | FLOAT | |
| `avg_vision_range` | FLOAT | |
| `avg_metabolism` | FLOAT | |
| `avg_aggression` | FLOAT | |
| `avg_hunger_threshold` | FLOAT | |
| `avg_safe_threshold` | FLOAT | |
| `avg_resistance` | FLOAT | |

---

## Relationships

```
simulation_run (1) ──< (many) tick_snapshot
```

`tick_snapshot.simulation_id` is a foreign key with an index, since the common
query is "all snapshots for run X, ordered by tick".

---

## Notes & future-proofing

- **Genome averages are denormalised** into `tick_snapshot` rather than computed
  from raw creature data, because individual creatures are not stored. If lineage
  tracking is added later, a `creature` table would join to `simulation_run` and
  carry `parent_a_id`, `parent_b_id`, `birth_tick`, `death_tick`, `death_cause`,
  and a birth-time genome snapshot.
- **`reproduction_weights` as JSON** keeps the variable-length weight list out of
  the flat columns. SQLite stores JSON as text; PostgreSQL has a native JSON type —
  SQLAlchemy handles both.
- Adding a new gene means adding `avg_<gene>` to `tick_snapshot` (and the seed
  range columns to `simulation_run`). This is a deliberate, explicit migration via
  Alembic rather than a generic blob, to keep stats easily queryable for charts.
