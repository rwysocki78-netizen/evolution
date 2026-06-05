"""Shared fixtures for engine tests."""
import random
import pytest

from app.engine.creature import Creature, Genome, Sex
from app.engine.params import SimParams
from app.engine.world import Position, World


@pytest.fixture
def params() -> SimParams:
    return SimParams(
        board_size=10,
        initial_energy=50.0,
        max_energy=100.0,
        energy_decay_per_tick=1.0,
        fight_energy_cost=10.0,
        reproduction_energy_cost=20.0,
        reproduction_min_energy=30.0,
        maturity_age=3,
        juvenile_max_energy_factor=0.5,
        fruit_energy_value=20.0,
        poison_energy_value=30.0,
        resistance_reduction_per_point=0.1,
        max_fruits_on_board=5,
        max_poisons_on_board=3,
        mutation_rate=0.0,   # disabled by default for deterministic tests
        mutation_magnitude=1.0,
        initial_population=4,
        total_turns=10,
    )


@pytest.fixture
def rng() -> random.Random:
    return random.Random(42)


def make_genome(**overrides) -> Genome:
    defaults = dict(
        lifespan=100,
        vision_range=2,
        hunger_threshold=30,
        safe_threshold=70,
        metabolism=1.0,
        aggression=0.3,
        resistance=0.0,
    )
    defaults.update(overrides)
    return Genome(**defaults)


def make_creature(
    id: int = 1,
    x: int = 5,
    y: int = 5,
    sex: Sex = Sex.MALE,
    energy: float = 50.0,
    age: int = 0,
    **genome_overrides,
) -> Creature:
    return Creature(
        id=id,
        position=Position(x, y),
        sex=sex,
        genome=make_genome(**genome_overrides),
        energy=energy,
        age=age,
    )


def make_world(size: int = 10) -> World:
    return World(width=size, height=size)
