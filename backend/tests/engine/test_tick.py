"""
Phase 1 tick sequence tests:
  - death by old age
  - death by starvation
  - walls block movement
  - deterministic given a fixed seed
"""
import random
import pytest

from tests.engine.conftest import make_creature, make_world
from app.engine.behavior.threshold import ThresholdBehavior
from app.engine.creature import Sex
from app.engine.params import SimParams
from app.engine.tick import tick
from app.engine.world import Position


def base_params(**overrides) -> SimParams:
    defaults = dict(
        board_size=10,
        energy_decay_per_tick=0.0,
        max_fruits_on_board=0,
        max_poisons_on_board=0,
        maturity_age=100,      # prevent reproduction noise
        mutation_rate=0.0,
        mutation_magnitude=1.0,
    )
    defaults.update(overrides)
    return SimParams(**defaults)


def run_tick(params, creatures, world=None):
    if world is None:
        world = make_world(params.board_size)
        for c in creatures:
            world.occupied[c.position] = c.id
    rng = random.Random(0)
    return tick(world, creatures, params, rng, ThresholdBehavior(), next_id=99)


def test_death_by_old_age():
    params = base_params()
    creature = make_creature(id=1, x=5, y=5, age=99, lifespan=100)  # dies at age 100
    alive, stats, _ = run_tick(params, [creature])
    assert len(alive) == 0
    assert stats.deaths_age == 1


def test_death_by_starvation():
    params = base_params(energy_decay_per_tick=100.0)  # drains completely
    creature = make_creature(id=1, x=5, y=5, energy=10.0, metabolism=1.0)
    alive, stats, _ = run_tick(params, [creature])
    assert len(alive) == 0
    assert stats.deaths_starvation == 1


def test_walls_block_movement():
    """A creature next to a wall cannot move into it."""
    params = base_params()
    # Board is 10×10; edges are impassable (out of bounds, treated as walls)
    creature = make_creature(id=1, x=0, y=0, energy=50.0, age=0,
                             hunger_threshold=200)  # always hungry → seeks food
    world = make_world(10)
    world.occupied[creature.position] = creature.id

    # Place a fruit at (-1, 0) — outside board, creature cannot reach it
    # Instead verify creature stays within bounds after one tick
    alive, stats, _ = tick(
        world, [creature], params, random.Random(7), ThresholdBehavior(), next_id=99
    )
    if alive:
        pos = alive[0].position
        assert 0 <= pos.x < 10
        assert 0 <= pos.y < 10


def test_deterministic_given_fixed_seed():
    """Two runs with the same seed must produce identical results."""
    from app.engine.simulation import create_world, create_creatures, make_behavior

    params = SimParams(
        board_size=10,
        initial_population=10,
        total_turns=20,
        mutation_rate=0.05,
        max_fruits_on_board=5,
        max_poisons_on_board=3,
        seed=12345,
    )

    def run(seed):
        rng = random.Random(seed)
        behavior = make_behavior(params.behavior_strategy)
        world = create_world(params, rng)
        creatures, next_id = create_creatures(params, world, rng)
        stats_list = []
        for t in range(1, params.total_turns + 1):
            creatures, stats, next_id = tick(world, creatures, params, rng, behavior, next_id, t)
            stats_list.append(stats)
            if not creatures:
                break
        return stats_list

    results_a = run(12345)
    results_b = run(12345)

    assert len(results_a) == len(results_b)
    for sa, sb in zip(results_a, results_b):
        assert sa.population_total == sb.population_total
        assert sa.births == sb.births
        assert sa.deaths_fight == sb.deaths_fight


def test_births_increase_population():
    """A male and female close together can produce offspring."""
    params = SimParams(
        board_size=10,
        maturity_age=0,
        reproduction_min_energy=10.0,
        reproduction_energy_cost=5.0,
        energy_decay_per_tick=0.0,
        max_fruits_on_board=0,
        max_poisons_on_board=0,
        mutation_rate=0.0,
        mutation_magnitude=1.0,
        initial_energy=50.0,
    )
    world = make_world(10)
    male = make_creature(id=1, x=5, y=5, sex=Sex.MALE, energy=50.0, age=0,
                         metabolism=0.0, lifespan=1000,
                         hunger_threshold=5, safe_threshold=10)
    female = make_creature(id=2, x=5, y=6, sex=Sex.FEMALE, energy=50.0, age=0,
                           metabolism=0.0, lifespan=1000,
                           hunger_threshold=5, safe_threshold=10)
    world.occupied[male.position] = male.id
    world.occupied[female.position] = female.id

    rng = random.Random(42)
    behavior = ThresholdBehavior()
    alive, stats, _ = tick(world, [male, female], params, rng, behavior, next_id=3)

    # Over multiple ticks, at least one birth should occur
    total_births = stats.births
    for t in range(2, 20):
        alive, stats, _ = tick(world, alive, params, rng, behavior, next_id=3 + total_births)
        total_births += stats.births
        if total_births > 0:
            break

    assert total_births > 0
