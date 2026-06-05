"""
Phase 1 poison resistance tests:
  - damage = round(POISON_ENERGY_VALUE * (1-p) ** resistance)
  - mutation of resistance is floored at 0
"""
import random
import pytest

from tests.engine.conftest import make_creature, make_world
from app.engine.world import Direction
from app.engine.params import SimParams
from app.engine.behavior.threshold import ThresholdBehavior
from app.engine.tick import tick
from app.engine.world import Position


def _poison_damage(poison_value: float, p: float, resistance: float) -> float:
    return round(poison_value * (1 - p) ** resistance)


@pytest.mark.parametrize("resistance,p", [
    (0.0, 0.1),
    (1.0, 0.1),
    (5.0, 0.1),
    (2.0, 0.3),
])
def test_poison_damage_formula(resistance, p):
    """Creature forced to STAY (all neighbours occupied) takes formula-correct poison damage."""
    params = SimParams(
        board_size=5,
        poison_energy_value=30.0,
        resistance_reduction_per_point=p,
        max_fruits_on_board=0,
        max_poisons_on_board=0,
        energy_decay_per_tick=0.0,
        maturity_age=100,      # prevent reproduction
        mutation_rate=0.0,
        mutation_magnitude=1.0,
    )
    # Wall in all 8 adjacent cells so the creature is forced to STAY
    world = make_world(size=5)
    creature = make_creature(id=1, x=2, y=2, energy=80.0, age=0,
                             metabolism=0.0, lifespan=1000,
                             hunger_threshold=5, safe_threshold=200,
                             resistance=resistance)
    world.poisons.add(creature.position)
    world.occupied[creature.position] = creature.id
    for d in Direction:
        if d != Direction.STAY:
            nb = creature.position.move(d)
            if world.in_bounds(nb):
                world.walls.add(nb)

    expected_damage = _poison_damage(30.0, p, resistance)

    rng = random.Random(0)
    behavior = ThresholdBehavior()
    alive, _, _ = tick(world, [creature], params, rng, behavior, next_id=99)

    target = next((c for c in alive if c.id == 1), None)
    if target:
        assert target.energy == pytest.approx(80.0 - expected_damage)
    else:
        assert expected_damage >= 80


def test_higher_resistance_reduces_damage():
    """More resistance → less poison damage."""
    p = 0.2
    damage_low = _poison_damage(30.0, p, resistance=0.0)
    damage_high = _poison_damage(30.0, p, resistance=5.0)
    assert damage_high < damage_low


def test_resistance_never_negative_after_mutation():
    """Covered by test_genetics; verified here via direct inherit call."""
    from app.engine.genetics import inherit
    from tests.engine.conftest import make_genome
    rng = random.Random(999)
    parent = make_genome(resistance=0.0)
    for _ in range(500):
        child = inherit(parent, parent, mutation_rate=1.0, mutation_magnitude=10.0, rng=rng)
        assert child.resistance >= 0.0
