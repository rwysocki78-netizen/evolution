# Evolution — Design Specification

Version: 1.0 (v1 scope)
Status: Complete, ready for development

This document defines **what** the simulation does. For **how** it is built, see
[architecture.md](architecture.md). For the reasoning behind specific rules, see
[decisions.md](decisions.md).

---

## 1. World

- The board is a **square grid** of configurable size (`BOARD_SIZE` × `BOARD_SIZE`).
- Edges are **hard walls** — a Creature cannot move off the board.
- Each cell can hold at most one Creature, plus optionally one fruit or one poison.
- Time advances in **discrete ticks**.

### World objects

| Object | Effect on entering Creature | Respawn |
|--------|-----------------------------|---------|
| Fruit | `energy += FRUIT_ENERGY_VALUE` | Respawns in random empty cells up to `MAX_FRUITS_ON_BOARD` |
| Poison | `energy -= round(POISON_ENERGY_VALUE * (1 - RESISTANCE_REDUCTION_PER_POINT) ** resistance)` | Respawns in random empty cells up to `MAX_POISONS_ON_BOARD` |

Poison damage is reduced **multiplicatively** by the entering Creature's `resistance`
gene: each point of resistance cuts the *remaining* damage by
`RESISTANCE_REDUCTION_PER_POINT`. Damage asymptotes toward zero but never reaches
zero or negative, so poison is never beneficial and needs no cap. The result is
rounded to an integer (no floor in v1, so a sufficiently resistant Creature may take
0 damage from a single poison). See [decisions.md](decisions.md#adr-023).

---

## 2. Creature

### State

| Field | Type | Notes |
|-------|------|-------|
| `sex` | enum | `male` / `female` |
| `energy` | integer | Acts as health; 0 → death |
| `age` | integer | Ticks lived |
| `position` | {x, y} | Integer grid coordinates |
| `genome` | Genome | Heritable traits (below) |

### Genome (heritable)

| Gene | Type | Role |
|------|------|------|
| `lifespan` | integer | Max age before death by old age |
| `visionRange` | integer | How many cells the Creature can see in all 8 directions (default 1) |
| `hungerThreshold` | integer | Below this energy, prioritise eating |
| `safeThreshold` | integer | Above this energy, consider reproducing |
| `metabolism` | float | Multiplier on energy decay per tick |
| `aggression` | float | Modifies fight/flee weighting |
| `resistance` | float | Multiplicatively reduces poison damage; seeded near 0, mutation floored at 0 |

The genome is defined as an open map so new genes can be added without touching
inheritance logic. See [architecture.md](architecture.md#genome-extensibility).

### Energy ceiling & life stage

- Energy is capped by a global `MAX_ENERGY`. After **any** energy gain (eating
  fruit, winning a fight) energy is clamped to the current ceiling.
- A Creature is a **juvenile** while `age < MATURITY_AGE`. Its ceiling is reduced:

  ```
  currentMax = (age < MATURITY_AGE)
               ? MAX_ENERGY * JUVENILE_MAX_ENERGY_FACTOR   # default 0.5
               : MAX_ENERGY
  energy = min(energy, currentMax)
  ```

- Juveniles also cannot reproduce (see [§5](#5-reproduction)). The reduced reserve
  plus the reproduction lock make reaching maturity a selective filter.

See [decisions.md](decisions.md#adr-021) and [ADR-022](decisions.md#adr-022).

---

## 3. Tick sequence

Each tick processes Creatures in a **randomly shuffled order** (to avoid giving
any Creature a systematic turn-order advantage):

```
1. Age      — age += 1; if age >= lifespan → die (cause: old age)
2. Decay    — energy -= ENERGY_DECAY_PER_TICK * metabolism; if energy <= 0 → die (cause: starvation)
3. Perceive — build a vision snapshot within visionRange (8 directions)
4. Decide   — behaviour strategy chooses a direction
5. Move     — attempt to move one cell in that direction
6. Resolve collision on the target cell:
       same sex      → fight
       opposite sex  → reproduce (if both eligible)
7. Resolve cell contents — apply fruit or poison effect
8. Spawn pending offspring into free adjacent cells
9. Respawn fruits and poisons up to their configured maxima
```

> Offspring created in step 6 do not appear in the same tick — they are queued and
> placed in step 8 (next-tick appearance, in cells neighbouring the parents).

> In steps 6 (fight win) and 7 (fruit), energy is clamped to the Creature's current
> ceiling after the gain — `MAX_ENERGY`, or `MAX_ENERGY * JUVENILE_MAX_ENERGY_FACTOR`
> for juveniles. In step 7, poison applies the resistance-reduced damage formula
> (see [§1 World objects](#world-objects)).

---

## 4. Fight

Triggered when a Creature moves onto a cell occupied by a **same-sex** Creature.

**Winner is chosen probabilistically, weighted by energy:**

```
P(A wins) = energyA / (energyA + energyB)
```

**Outcome:**

```
winner.energy = max(1, winner.energy + loser.energy - FIGHT_ENERGY_COST)
loser → dies (cause: fight)
```

The winner always survives with at least 1 energy — the fight cost is applied but
never lethal to the victor. `aggression` may further weight the probability
(exact formula to be finalised in the behaviour module).

---

## 5. Reproduction

Triggered when a Creature moves onto a cell occupied by an **opposite-sex** Creature.

**Eligibility:** both parents must be mature (`age >= MATURITY_AGE`) **and** have
`energy >= REPRODUCTION_MIN_ENERGY`.

- If eligible: both pay `REPRODUCTION_ENERGY_COST`; a litter is produced.
- If not eligible: nothing happens, both Creatures remain.

**Litter size** is drawn from configurable weighted probabilities:

```
REPRODUCTION_WEIGHTS = [
  { children: 1, weight: 0.50 },
  { children: 2, weight: 0.30 },
  { children: 3, weight: 0.15 },
  { children: 4, weight: 0.05 }
]
```

**Placement:** offspring appear next tick in free cells adjacent to the parents.
If there are not enough free adjacent cells, the **energy cost is still paid** and
the un-placeable offspring are lost. (Overcrowding is a real selective pressure.)

---

## 6. Inheritance & mutation

For each gene, the offspring independently takes the value from one parent or the
other (50/50):

```
for each gene in genome:
    child.gene = random() < 0.5 ? parentA.gene : parentB.gene
    if random() < MUTATION_RATE:
        child.gene = mutate(child.gene, MUTATION_MAGNITUDE)
```

- Numeric genes shift by ±(random within `MUTATION_MAGNITUDE`).
- Without mutation, traits only average toward the mean and evolution stalls —
  mutation is the source of novelty.

Sex of offspring is assigned (50/50 male/female) — not inherited.

---

## 7. Death causes

Tracked separately for statistics:

- **Old age** — `age >= lifespan`
- **Starvation** — `energy <= 0`
- **Fight** — lost a same-sex encounter

---

## 8. Behaviour (pluggable)

Movement decisions are encapsulated behind a strategy interface so different
decision models can be swapped and compared (see
[architecture.md](architecture.md#behaviour-strategy-pattern)). v1 ships at least:

- **Threshold strategy** — decisions emerge from energy thresholds
  (`hungerThreshold`, `safeThreshold`).
- **Priority strategy** — a fixed ordered priority list (e.g. eat > reproduce > fight > wander).

A key planned experiment is comparing population outcomes under thresholds vs.
hard priorities.

---

## 9. Simulation lifecycle

```
SETUP      → configure all parameters and number of turns
RUNNING    → run / pause / step through ticks
RESULTS    → view statistics, results saved to DB, restart
```

A run ends when `TOTAL_TURNS` is reached, the population dies out, or the user
stops it manually.

---

## 10. Configurable parameters (complete)

### Board
- `BOARD_SIZE`

### Vision
- `VISION_RANGE` (default 1)

### Energy
- `INITIAL_ENERGY`
- `MAX_ENERGY`
- `ENERGY_DECAY_PER_TICK`
- `FIGHT_ENERGY_COST`
- `REPRODUCTION_ENERGY_COST`
- `REPRODUCTION_MIN_ENERGY`

### Life stage
- `MATURITY_AGE`
- `JUVENILE_MAX_ENERGY_FACTOR` (default 0.5)

### World objects
- `FRUIT_ENERGY_VALUE`
- `POISON_ENERGY_VALUE`
- `RESISTANCE_REDUCTION_PER_POINT` (`p` in the poison damage formula, 0..1)
- `MAX_FRUITS_ON_BOARD`
- `MAX_POISONS_ON_BOARD`

### Mutation
- `MUTATION_RATE`
- `MUTATION_MAGNITUDE`

### Genome initial ranges (min / max per gene, used to seed the starting population)
- `INITIAL_LIFESPAN`
- `INITIAL_VISION_RANGE`
- `INITIAL_METABOLISM`
- `INITIAL_AGGRESSION`
- `INITIAL_HUNGER_THRESHOLD`
- `INITIAL_SAFE_THRESHOLD`
- `INITIAL_RESISTANCE` (e.g. 0–2; mutation is floored at 0)

### Reproduction
- `REPRODUCTION_WEIGHTS`

### Population
- `INITIAL_POPULATION`

### Simulation
- `TOTAL_TURNS`
- `BEHAVIOR_STRATEGY`
- `SNAPSHOT_ENABLED`
- `SNAPSHOT_INTERVAL`

---

## 11. Statistics captured

Per tick (when snapshots are enabled, every `SNAPSHOT_INTERVAL` ticks):

- Population: total, male, female
- Energy: average, min, max
- Events: births; deaths by cause (starvation / age / fight); total fights;
  reproductions successful / failed-space / failed-energy
- World: fruits on board, poisons on board
- Genome averages: lifespan, visionRange, metabolism, aggression,
  hungerThreshold, safeThreshold, resistance (trait-drift tracking)

Per run: full parameter snapshot, timestamps, status, turns configured vs. run.

See [data-model.md](data-model.md) for the exact schema.

---

## 12. Explicitly out of scope for v1

- Individual creature / lineage tracking (no family trees)
- Diagonal-only or 4-direction movement (v1 is 8-direction)
- Continuous (non-grid) space
- Multiplayer / multiple concurrent simulations sharing a board
