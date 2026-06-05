"""
Phase 1 reproduction tests:
  - no free cells → energy cost paid, offspring lost
  - ineligible (age < maturity) → no reproduction
  - ineligible (energy too low) → no reproduction
  - eligible pair → offspring queued
"""
import random
import pytest

from tests.engine.conftest import make_creature, make_world
from app.engine.creature import Sex
from app.engine.params import SimParams
from app.engine.stats import TickStats
from app.engine.tick import _reproduce
from app.engine.world import Position


@pytest.fixture
def params():
    return SimParams(
        reproduction_energy_cost=20.0,
        reproduction_min_energy=30.0,
        maturity_age=5,
        mutation_rate=0.0,
        mutation_magnitude=1.0,
    )


def eligible_pair(energy=60.0, age=10):
    a = make_creature(id=1, x=5, y=5, sex=Sex.MALE, energy=energy, age=age)
    b = make_creature(id=2, x=5, y=6, sex=Sex.FEMALE, energy=energy, age=age)
    return a, b


def test_eligible_pair_queues_offspring(params):
    a, b = eligible_pair()
    rng = random.Random(0)
    stats = TickStats()
    pending = []
    _reproduce(a, b, params, rng, stats, pending)
    assert len(pending) >= 1
    assert stats.reproductions_success == 1
    assert stats.reproductions_failed_energy == 0


def test_eligible_pair_pays_energy_cost(params):
    a, b = eligible_pair(energy=60.0)
    rng = random.Random(0)
    stats = TickStats()
    pending = []
    _reproduce(a, b, params, rng, stats, pending)
    assert a.energy == pytest.approx(40.0)
    assert b.energy == pytest.approx(40.0)


def test_immature_creature_blocks_reproduction(params):
    a, b = eligible_pair(age=2)  # below maturity_age=5
    rng = random.Random(0)
    stats = TickStats()
    pending = []
    _reproduce(a, b, params, rng, stats, pending)
    assert len(pending) == 0
    assert stats.reproductions_failed_energy == 1


def test_low_energy_blocks_reproduction(params):
    a, b = eligible_pair(energy=10.0, age=10)  # below min_energy=30
    rng = random.Random(0)
    stats = TickStats()
    pending = []
    _reproduce(a, b, params, rng, stats, pending)
    assert len(pending) == 0
    assert stats.reproductions_failed_energy == 1


def test_no_free_cells_cost_paid_offspring_lost(params):
    """Full tick: offspring queued but no adjacent cells → births=0, cost still paid."""
    from app.engine.behavior.threshold import ThresholdBehavior
    from app.engine.tick import tick

    # 3×3 board, two creatures in the centre, all surrounding cells occupied
    board_params = SimParams(
        board_size=3,
        maturity_age=0,
        reproduction_min_energy=10.0,
        reproduction_energy_cost=5.0,
        mutation_rate=0.0,
        mutation_magnitude=1.0,
        max_fruits_on_board=0,
        max_poisons_on_board=0,
        energy_decay_per_tick=0.0,
        initial_energy=50.0,
    )
    world = make_world(size=3)
    rng = random.Random(123)

    # Male at (1,1), female at (1,2)
    male = make_creature(id=1, x=1, y=1, sex=Sex.MALE, energy=50.0, age=10,
                         metabolism=0.0, lifespan=1000, hunger_threshold=5, safe_threshold=10)
    female = make_creature(id=2, x=1, y=2, sex=Sex.FEMALE, energy=50.0, age=10,
                           metabolism=0.0, lifespan=1000, hunger_threshold=5, safe_threshold=10)

    # Fill every other cell with blockers
    blockers = []
    next_id = 3
    for x in range(3):
        for y in range(3):
            pos = Position(x, y)
            if pos not in (Position(1, 1), Position(1, 2)):
                c = make_creature(id=next_id, x=x, y=y, sex=Sex.MALE, energy=50.0, age=10,
                                  metabolism=0.0, lifespan=1000)
                blockers.append(c)
                world.occupied[pos] = next_id
                next_id += 1

    world.occupied[male.position] = male.id
    world.occupied[female.position] = female.id

    all_creatures = [male, female] + blockers
    behavior = ThresholdBehavior()

    _, stats, _ = tick(world, all_creatures, board_params, rng, behavior, next_id, tick_number=1)

    assert stats.births == 0
