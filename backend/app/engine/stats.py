from __future__ import annotations
from dataclasses import dataclass, field

from app.engine.creature import Creature, Sex
from app.engine.world import World


@dataclass
class TickStats:
    tick: int = 0

    # Population
    population_total: int = 0
    population_male: int = 0
    population_female: int = 0

    # Energy
    energy_avg: float = 0.0
    energy_min: float = 0.0
    energy_max: float = 0.0

    # Events (accumulated during the tick)
    births: int = 0
    deaths_starvation: int = 0
    deaths_age: int = 0
    deaths_fight: int = 0
    fights_total: int = 0
    reproductions_success: int = 0
    reproductions_failed_space: int = 0
    reproductions_failed_energy: int = 0

    # World
    fruits_count: int = 0
    poisons_count: int = 0

    # Genome averages
    avg_lifespan: float = 0.0
    avg_vision_range: float = 0.0
    avg_metabolism: float = 0.0
    avg_aggression: float = 0.0
    avg_hunger_threshold: float = 0.0
    avg_safe_threshold: float = 0.0
    avg_resistance: float = 0.0


def aggregate_population(stats: TickStats, alive: list[Creature], world: World) -> None:
    """Fill population, energy, world, and genome-average fields from living creatures."""
    stats.population_total = len(alive)
    stats.population_male = sum(1 for c in alive if c.sex == Sex.MALE)
    stats.population_female = stats.population_total - stats.population_male

    if alive:
        energies = [c.energy for c in alive]
        stats.energy_avg = sum(energies) / len(energies)
        stats.energy_min = min(energies)
        stats.energy_max = max(energies)

        stats.avg_lifespan = sum(c.genome.lifespan for c in alive) / len(alive)
        stats.avg_vision_range = sum(c.genome.vision_range for c in alive) / len(alive)
        stats.avg_metabolism = sum(c.genome.metabolism for c in alive) / len(alive)
        stats.avg_aggression = sum(c.genome.aggression for c in alive) / len(alive)
        stats.avg_hunger_threshold = sum(c.genome.hunger_threshold for c in alive) / len(alive)
        stats.avg_safe_threshold = sum(c.genome.safe_threshold for c in alive) / len(alive)
        stats.avg_resistance = sum(c.genome.resistance for c in alive) / len(alive)

    stats.fruits_count = len(world.fruits)
    stats.poisons_count = len(world.poisons)
