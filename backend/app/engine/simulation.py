"""
Bootstrap helpers: create an initial World and creature population from SimParams.
"""
from __future__ import annotations

import random

from app.engine.behavior.base import BehaviorStrategy
from app.engine.behavior.priority import PriorityBehavior
from app.engine.behavior.threshold import ThresholdBehavior
from app.engine.creature import Creature, Genome, Sex
from app.engine.params import SimParams
from app.engine.stats import TickStats
from app.engine.tick import tick
from app.engine.world import Position, World


def make_behavior(strategy: str) -> BehaviorStrategy:
    if strategy == "priority":
        return PriorityBehavior()
    return ThresholdBehavior()


def create_world(params: SimParams, rng: random.Random) -> World:
    world = World(width=params.board_size, height=params.board_size)
    all_pos = [Position(x, y) for x in range(params.board_size) for y in range(params.board_size)]
    rng.shuffle(all_pos)

    idx = 0
    for _ in range(params.max_fruits_on_board):
        if idx < len(all_pos):
            world.fruits.add(all_pos[idx])
            idx += 1
    for _ in range(params.max_poisons_on_board):
        if idx < len(all_pos):
            world.poisons.add(all_pos[idx])
            idx += 1
    return world


def create_creatures(params: SimParams, world: World, rng: random.Random) -> tuple[list[Creature], int]:
    all_pos = [Position(x, y) for x in range(params.board_size) for y in range(params.board_size)]
    empty = [p for p in all_pos if p not in world.fruits and p not in world.poisons]
    rng.shuffle(empty)

    creatures: list[Creature] = []
    next_id = 1
    for pos in empty[: params.initial_population]:
        genome = Genome(
            lifespan=rng.randint(*params.initial_lifespan),
            vision_range=rng.randint(*params.initial_vision_range),
            hunger_threshold=rng.randint(*params.initial_hunger_threshold),
            safe_threshold=rng.randint(*params.initial_safe_threshold),
            metabolism=rng.uniform(*params.initial_metabolism),
            aggression=rng.uniform(*params.initial_aggression),
            resistance=rng.uniform(*params.initial_resistance),
        )
        creature = Creature(
            id=next_id,
            position=pos,
            sex=Sex.MALE if rng.random() < 0.5 else Sex.FEMALE,
            genome=genome,
            energy=params.initial_energy,
        )
        creatures.append(creature)
        world.occupied[pos] = next_id
        next_id += 1
    return creatures, next_id


def run_simulation(params: SimParams) -> list[TickStats]:
    """
    Run a full simulation and return per-tick stats.

    The caller is responsible for persistence; this function is pure engine.
    """
    seed = params.seed if params.seed is not None else random.randrange(2**32)
    rng = random.Random(seed)
    behavior = make_behavior(params.behavior_strategy)

    world = create_world(params, rng)
    creatures, next_id = create_creatures(params, world, rng)

    all_stats: list[TickStats] = []

    for t in range(1, params.total_turns + 1):
        creatures, stats, next_id = tick(world, creatures, params, rng, behavior, next_id, tick_number=t)

        if params.snapshot_enabled and t % params.snapshot_interval == 0:
            all_stats.append(stats)

        if not creatures:
            break  # population extinct

    return all_stats
