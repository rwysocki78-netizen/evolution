from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ReproductionWeight:
    children: int
    weight: float


@dataclass
class SimParams:
    # Board
    board_size: int = 20

    # Energy
    initial_energy: float = 50.0
    max_energy: float = 100.0
    energy_decay_per_tick: float = 0.8
    fight_energy_cost: float = 10.0
    reproduction_energy_cost: float = 20.0
    reproduction_min_energy: float = 40.0

    # Life stage
    maturity_age: int = 5
    juvenile_max_energy_factor: float = 0.5

    # World objects
    fruit_energy_value: float = 22.0
    poison_energy_value: float = 30.0
    resistance_reduction_per_point: float = 0.1
    max_fruits_on_board: int = 48
    max_poisons_on_board: int = 5

    # Mutation
    mutation_rate: float = 0.05
    mutation_magnitude: float = 1.0

    # Initial gene ranges (min, max) used to seed the starting population
    initial_lifespan: tuple[int, int] = (80, 120)
    initial_vision_range: tuple[int, int] = (1, 3)
    initial_metabolism: tuple[float, float] = (0.8, 1.2)
    initial_aggression: tuple[float, float] = (0.3, 0.7)
    initial_hunger_threshold: tuple[int, int] = (20, 40)
    initial_safe_threshold: tuple[int, int] = (60, 80)
    initial_resistance: tuple[float, float] = (0.0, 2.0)

    # Reproduction
    reproduction_weights: list[ReproductionWeight] = field(
        default_factory=lambda: [
            ReproductionWeight(1, 0.50),
            ReproductionWeight(2, 0.30),
            ReproductionWeight(3, 0.15),
            ReproductionWeight(4, 0.05),
        ]
    )

    # Population & simulation
    initial_population: int = 50
    total_turns: int = 1000
    behavior_strategy: str = "priority"
    snapshot_enabled: bool = True
    snapshot_interval: int = 10
    seed: int | None = None
