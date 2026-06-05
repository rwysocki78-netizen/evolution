"""
Full tick sequence (spec §3):

  1. Age      — age += 1; if age >= lifespan → die (old age)
  2. Decay    — energy -= ENERGY_DECAY_PER_TICK * metabolism; if energy <= 0 → die (starvation)
  3. Perceive — build vision snapshot
  4. Decide   — behaviour strategy chooses a direction
  5. Move     — attempt to move; resolve collision on target cell
  6. Cell     — apply fruit / poison
  7. Spawn    — place pending offspring into free adjacent cells
  8. Respawn  — refill fruits and poisons up to configured maxima

Creatures are processed in a randomly shuffled order each tick.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from app.engine.behavior.base import BehaviorStrategy
from app.engine.creature import Creature, DeathCause, Genome, Sex
from app.engine.genetics import inherit
from app.engine.params import SimParams
from app.engine.stats import TickStats, aggregate_population
from app.engine.vision import build_vision
from app.engine.world import Direction, Position, World


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _energy_ceiling(creature: Creature, params: SimParams) -> float:
    if creature.age < params.maturity_age:
        return params.max_energy * params.juvenile_max_energy_factor
    return params.max_energy


def _clamp_energy(creature: Creature, params: SimParams) -> None:
    ceiling = _energy_ceiling(creature, params)
    if creature.energy > ceiling:
        creature.energy = ceiling


def _kill(creature: Creature, cause: DeathCause, world: World, stats: TickStats) -> None:
    creature.alive = False
    world.occupied.pop(creature.position, None)
    if cause == DeathCause.OLD_AGE:
        stats.deaths_age += 1
    elif cause == DeathCause.STARVATION:
        stats.deaths_starvation += 1
    elif cause == DeathCause.FIGHT:
        stats.deaths_fight += 1


def _move_creature(creature: Creature, new_pos: Position, world: World) -> None:
    world.occupied.pop(creature.position, None)
    creature.position = new_pos
    world.occupied[new_pos] = creature.id


def _draw_litter_size(params: SimParams, rng: random.Random) -> int:
    weights = params.reproduction_weights
    r = rng.random()
    cumulative = 0.0
    for w in weights:
        cumulative += w.weight
        if r < cumulative:
            return w.children
    return weights[-1].children


def _adjacent_free_cells(pos: Position, world: World) -> list[Position]:
    cells: list[Position] = []
    for d in Direction:
        if d == Direction.STAY:
            continue
        candidate = pos.move(d)
        if world.is_free(candidate):
            cells.append(candidate)
    return cells


def _fight(
    mover: Creature,
    resident: Creature,
    world: World,
    params: SimParams,
    rng: random.Random,
    stats: TickStats,
) -> None:
    """Mover and resident are same-sex. Mover has NOT moved yet."""
    stats.fights_total += 1

    p_mover_wins = mover.energy / (mover.energy + resident.energy)
    mover_wins = rng.random() < p_mover_wins

    if mover_wins:
        mover.energy = max(1.0, mover.energy + resident.energy - params.fight_energy_cost)
        _clamp_energy(mover, params)
        _kill(resident, DeathCause.FIGHT, world, stats)
        _move_creature(mover, resident.position, world)
    else:
        resident.energy = max(1.0, resident.energy + mover.energy - params.fight_energy_cost)
        _clamp_energy(resident, params)
        _kill(mover, DeathCause.FIGHT, world, stats)


def _reproduce(
    mover: Creature,
    resident: Creature,
    params: SimParams,
    rng: random.Random,
    stats: TickStats,
    pending: list[tuple[Genome, Position, Position]],
) -> None:
    """Mover and resident are opposite-sex. Check eligibility and queue offspring."""
    mature_a = mover.age >= params.maturity_age
    mature_b = resident.age >= params.maturity_age
    energy_ok_a = mover.energy >= params.reproduction_min_energy
    energy_ok_b = resident.energy >= params.reproduction_min_energy

    if not (mature_a and mature_b and energy_ok_a and energy_ok_b):
        stats.reproductions_failed_energy += 1
        return

    mover.energy -= params.reproduction_energy_cost
    resident.energy -= params.reproduction_energy_cost

    litter = _draw_litter_size(params, rng)
    for _ in range(litter):
        genome = inherit(mover.genome, resident.genome, params.mutation_rate, params.mutation_magnitude, rng)
        pending.append((genome, mover.position, resident.position))

    stats.reproductions_success += 1


def _respawn(world: World, params: SimParams, rng: random.Random) -> None:
    need_fruit = max(0, params.max_fruits_on_board - len(world.fruits))
    need_poison = max(0, params.max_poisons_on_board - len(world.poisons))
    if need_fruit == 0 and need_poison == 0:
        return

    candidates = [
        Position(x, y)
        for x in range(world.width)
        for y in range(world.height)
        if Position(x, y) not in world.walls
        and Position(x, y) not in world.occupied
        and Position(x, y) not in world.fruits
        and Position(x, y) not in world.poisons
    ]
    rng.shuffle(candidates)

    idx = 0
    for _ in range(need_fruit):
        if idx >= len(candidates):
            break
        world.fruits.add(candidates[idx])
        idx += 1
    for _ in range(need_poison):
        if idx >= len(candidates):
            break
        world.poisons.add(candidates[idx])
        idx += 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def tick(
    world: World,
    creatures: list[Creature],
    params: SimParams,
    rng: random.Random,
    behavior: BehaviorStrategy,
    next_id: int,
    tick_number: int = 0,
) -> tuple[list[Creature], TickStats, int]:
    """
    Advance the simulation by one tick.

    Mutates *world* in place. Returns (alive_creatures, stats, next_id).
    """
    stats = TickStats(tick=tick_number)
    pending: list[tuple[Genome, Position, Position]] = []

    # Build id → creature map (alive only)
    creatures_by_id: dict[int, Creature] = {c.id: c for c in creatures if c.alive}

    order = [c for c in creatures if c.alive]
    rng.shuffle(order)

    for creature in order:
        if not creature.alive:
            continue

        # --- 1. Age ---
        creature.age += 1
        if creature.age >= creature.genome.lifespan:
            _kill(creature, DeathCause.OLD_AGE, world, stats)
            continue

        # --- 2. Decay ---
        creature.energy -= params.energy_decay_per_tick * creature.genome.metabolism
        if creature.energy <= 0:
            _kill(creature, DeathCause.STARVATION, world, stats)
            continue

        # --- 3. Perceive ---
        vision = build_vision(creature, world, creatures_by_id)

        # --- 4. Decide ---
        direction = behavior.decide_move(creature, vision, rng)

        # --- 5. Move + collision ---
        if direction != Direction.STAY:
            target = creature.position.move(direction)
            if world.is_passable(target):
                if target in world.occupied:
                    other_id = world.occupied[target]
                    other = creatures_by_id.get(other_id)
                    if other is None or not other.alive:
                        # Vacated cell — just move in
                        _move_creature(creature, target, world)
                    elif creature.sex == other.sex:
                        _fight(creature, other, world, params, rng, stats)
                    else:
                        _reproduce(creature, other, params, rng, stats, pending)
                else:
                    _move_creature(creature, target, world)

        if not creature.alive:
            continue

        # --- 6. Cell contents ---
        pos = creature.position
        if pos in world.fruits:
            creature.energy += params.fruit_energy_value
            _clamp_energy(creature, params)
            world.fruits.discard(pos)
        elif pos in world.poisons:
            p = params.resistance_reduction_per_point
            damage = round(params.poison_energy_value * (1 - p) ** creature.genome.resistance)
            creature.energy -= damage
            world.poisons.discard(pos)
            if creature.energy <= 0:
                _kill(creature, DeathCause.STARVATION, world, stats)
                continue

    # --- 7. Spawn pending offspring ---
    for genome, pos_a, pos_b in pending:
        # Collect unique free adjacent cells from both parent positions
        seen_cells: set[Position] = set()
        free_cells: list[Position] = []
        for p in _adjacent_free_cells(pos_a, world) + _adjacent_free_cells(pos_b, world):
            if p not in seen_cells:
                seen_cells.add(p)
                free_cells.append(p)

        if free_cells:
            spawn_pos = rng.choice(free_cells)
            child = Creature(
                id=next_id,
                position=spawn_pos,
                sex=rng.choice([Sex.MALE, Sex.FEMALE]),
                genome=genome,
                energy=params.initial_energy,
                age=0,
            )
            next_id += 1
            creatures.append(child)
            creatures_by_id[child.id] = child
            world.occupied[spawn_pos] = child.id
            stats.births += 1
        else:
            stats.reproductions_failed_space += 1

    # --- 8. Respawn fruits and poisons ---
    _respawn(world, params, rng)

    # --- Aggregate end-of-tick stats ---
    alive = [c for c in creatures if c.alive]
    aggregate_population(stats, alive, world)

    return alive, stats, next_id
