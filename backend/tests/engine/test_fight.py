"""
Phase 1 fight tests:
  - win probability matches energy ratio over many trials
  - winner survives with at least 1 energy
  - loser dies
"""
import random
import pytest

from tests.engine.conftest import make_creature, make_world
from app.engine.stats import TickStats
from app.engine.tick import _fight
from app.engine.params import SimParams
from app.engine.world import Position


@pytest.fixture
def params():
    return SimParams(fight_energy_cost=10.0)


def test_fight_win_probability_matches_energy_ratio(params):
    """P(A wins) ≈ energyA / (energyA + energyB) over many trials."""
    rng = random.Random(99)
    energy_a, energy_b = 30.0, 70.0
    expected_p = energy_a / (energy_a + energy_b)

    a_wins = 0
    trials = 5000
    for _ in range(trials):
        world = make_world()
        a = make_creature(id=1, x=3, y=3, energy=energy_a)
        b = make_creature(id=2, x=4, y=3, energy=energy_b)
        world.occupied[a.position] = a.id
        world.occupied[b.position] = b.id

        stats = TickStats()
        _fight(a, b, world, params, rng, stats)
        if a.alive:
            a_wins += 1

    observed_p = a_wins / trials
    assert abs(observed_p - expected_p) < 0.03, f"Expected ~{expected_p:.2f}, got {observed_p:.2f}"


def test_winner_survives_with_at_least_1(params):
    """Winner always has energy >= 1, even with large fight cost."""
    params = SimParams(fight_energy_cost=10000.0)  # absurdly high cost
    rng = random.Random(7)

    for _ in range(200):
        world = make_world()
        a = make_creature(id=1, x=3, y=3, energy=2.0)
        b = make_creature(id=2, x=4, y=3, energy=3.0)
        world.occupied[a.position] = a.id
        world.occupied[b.position] = b.id

        stats = TickStats()
        _fight(a, b, world, params, rng, stats)

        winner = a if a.alive else b
        assert winner.energy >= 1.0


def test_loser_dies(params):
    """Exactly one creature dies per fight."""
    rng = random.Random(11)

    for _ in range(100):
        world = make_world()
        a = make_creature(id=1, x=3, y=3, energy=50.0)
        b = make_creature(id=2, x=4, y=3, energy=50.0)
        world.occupied[a.position] = a.id
        world.occupied[b.position] = b.id

        stats = TickStats()
        _fight(a, b, world, params, rng, stats)

        alive_count = sum(1 for c in (a, b) if c.alive)
        assert alive_count == 1
        assert stats.fights_total == 1
        assert stats.deaths_fight == 1


def test_winner_moves_to_loser_position(params):
    """When mover wins, it ends up on the resident's cell."""
    # Force mover to always win by giving it overwhelming energy
    rng = random.Random(5)

    wins = 0
    for _ in range(100):
        world = make_world()
        a = make_creature(id=1, x=3, y=3, energy=9999.0)
        b = make_creature(id=2, x=4, y=3, energy=1.0)
        world.occupied[a.position] = a.id
        world.occupied[b.position] = b.id

        stats = TickStats()
        _fight(a, b, world, params, rng, stats)
        if a.alive:
            assert a.position == Position(4, 3)
            wins += 1

    assert wins > 80  # mover should win the vast majority
