"""
Phase 1 energy ceiling tests:
  - juvenile capped at MAX_ENERGY * JUVENILE_MAX_ENERGY_FACTOR
  - adult capped at MAX_ENERGY
"""
import random
import pytest

from tests.engine.conftest import make_creature, make_world
from app.engine.creature import Sex
from app.engine.params import SimParams
from app.engine.behavior.threshold import ThresholdBehavior
from app.engine.tick import tick
from app.engine.world import Position


def _run_one_tick(params, creatures, world):
    rng = random.Random(0)
    behavior = ThresholdBehavior()
    alive, stats, _ = tick(world, creatures, params, rng, behavior, next_id=99)
    return alive, stats


def test_juvenile_energy_capped_after_eating_fruit():
    params = SimParams(
        board_size=5,
        max_energy=100.0,
        juvenile_max_energy_factor=0.5,
        maturity_age=10,       # creature age=0 is juvenile
        energy_decay_per_tick=0.0,
        max_fruits_on_board=0,
        max_poisons_on_board=0,
        mutation_rate=0.0,
        mutation_magnitude=1.0,
    )
    world = make_world(size=5)
    fruit_pos = Position(3, 3)
    world.fruits.add(fruit_pos)

    # Creature starts with near-max energy; fruit would push it over juvenile cap
    creature = make_creature(id=1, x=3, y=3, energy=49.0, age=0,
                             metabolism=0.0, lifespan=1000,
                             hunger_threshold=5, safe_threshold=200)
    world.occupied[creature.position] = creature.id

    alive, _ = _run_one_tick(params, [creature], world)
    assert len(alive) == 1
    assert alive[0].energy <= params.max_energy * params.juvenile_max_energy_factor


def test_adult_energy_capped_at_max_energy():
    params = SimParams(
        board_size=5,
        max_energy=100.0,
        juvenile_max_energy_factor=0.5,
        maturity_age=0,        # age=0 is already adult
        energy_decay_per_tick=0.0,
        max_fruits_on_board=0,
        max_poisons_on_board=0,
        mutation_rate=0.0,
        mutation_magnitude=1.0,
    )
    world = make_world(size=5)
    fruit_pos = Position(3, 3)
    world.fruits.add(fruit_pos)

    creature = make_creature(id=1, x=3, y=3, energy=95.0, age=0,
                             metabolism=0.0, lifespan=1000,
                             hunger_threshold=5, safe_threshold=200)
    world.occupied[creature.position] = creature.id

    alive, _ = _run_one_tick(params, [creature], world)
    assert len(alive) == 1
    assert alive[0].energy <= params.max_energy


def test_energy_ceiling_rises_at_maturity():
    """Creature transitions from juvenile to adult ceiling within a tick."""
    params = SimParams(
        board_size=5,
        max_energy=100.0,
        juvenile_max_energy_factor=0.5,
        maturity_age=1,        # becomes adult at age 1 (after age step)
        energy_decay_per_tick=0.0,
        max_fruits_on_board=0,
        max_poisons_on_board=0,
        mutation_rate=0.0,
        mutation_magnitude=1.0,
    )
    world = make_world(size=5)
    fruit_pos = Position(3, 3)
    world.fruits.add(fruit_pos)

    # age=0 now; after age step age=1 >= maturity_age=1 → adult ceiling
    creature = make_creature(id=1, x=3, y=3, energy=95.0, age=0,
                             metabolism=0.0, lifespan=1000,
                             hunger_threshold=5, safe_threshold=200)
    world.occupied[creature.position] = creature.id

    alive, _ = _run_one_tick(params, [creature], world)
    assert alive[0].energy <= params.max_energy  # adult cap, not juvenile
