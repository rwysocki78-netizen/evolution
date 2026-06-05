from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------

class ReproductionWeightIn(BaseModel):
    children: int = Field(ge=1)
    weight: float = Field(gt=0)


class SimParamsRequest(BaseModel):
    # Board
    board_size: int = 20

    # Energy
    initial_energy: float = 50.0
    max_energy: float = 100.0
    energy_decay_per_tick: float = 1.0
    fight_energy_cost: float = 10.0
    reproduction_energy_cost: float = 20.0
    reproduction_min_energy: float = 40.0

    # Life stage
    maturity_age: int = 5
    juvenile_max_energy_factor: float = 0.5

    # World
    fruit_energy_value: float = 20.0
    poison_energy_value: float = 30.0
    resistance_reduction_per_point: float = 0.1
    max_fruits_on_board: int = 20
    max_poisons_on_board: int = 10

    # Mutation
    mutation_rate: float = 0.05
    mutation_magnitude: float = 1.0

    # Genome initial ranges [min, max]
    initial_lifespan: list[int] = Field(default=[80, 120], min_length=2, max_length=2)
    initial_vision_range: list[int] = Field(default=[1, 3], min_length=2, max_length=2)
    initial_metabolism: list[float] = Field(default=[0.8, 1.2], min_length=2, max_length=2)
    initial_aggression: list[float] = Field(default=[0.3, 0.7], min_length=2, max_length=2)
    initial_hunger_threshold: list[int] = Field(default=[20, 40], min_length=2, max_length=2)
    initial_safe_threshold: list[int] = Field(default=[60, 80], min_length=2, max_length=2)
    initial_resistance: list[float] = Field(default=[0.0, 2.0], min_length=2, max_length=2)

    # Reproduction
    reproduction_weights: list[ReproductionWeightIn] = Field(
        default=[
            ReproductionWeightIn(children=1, weight=0.50),
            ReproductionWeightIn(children=2, weight=0.30),
            ReproductionWeightIn(children=3, weight=0.15),
            ReproductionWeightIn(children=4, weight=0.05),
        ]
    )

    # Population & simulation
    initial_population: int = 50
    total_turns: int = 1000
    behavior_strategy: str = "threshold"
    snapshot_enabled: bool = True
    snapshot_interval: int = 10
    seed: int | None = None


class RunRequest(BaseModel):
    ticks: int | None = Field(default=None, description="Ticks to advance; None = run to completion")


# ---------------------------------------------------------------------------
# Response bodies
# ---------------------------------------------------------------------------

class SimulationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    status: str
    seed: int
    started_at: datetime
    finished_at: datetime | None
    total_turns_configured: int
    total_turns_run: int
    behavior_strategy: str
    board_size: int
    initial_population: int
    snapshot_enabled: bool
    snapshot_interval: int


class PositionOut(BaseModel):
    x: int
    y: int


class CreatureOut(BaseModel):
    id: int
    x: int
    y: int
    sex: str
    energy: float
    age: int


class BoardStateResponse(BaseModel):
    simulation_id: int
    tick: int
    board_size: int
    status: str
    creatures: list[CreatureOut]
    fruits: list[PositionOut]
    poisons: list[PositionOut]


class TickResponse(BaseModel):
    """Returned by /step and /run."""
    state: BoardStateResponse
    completed: bool
    turns_run: int


class TickSnapshotResponse(BaseModel):
    model_config = {"from_attributes": True}

    tick: int
    population_total: int
    population_male: int
    population_female: int
    avg_energy: float
    min_energy: float
    max_energy: float
    births: int
    deaths_total: int
    deaths_starvation: int
    deaths_age: int
    deaths_fight: int
    fights_total: int
    reproductions_successful: int
    reproductions_failed_space: int
    reproductions_failed_energy: int
    fruits_on_board: int
    poisons_on_board: int
    avg_lifespan: float
    avg_vision_range: float
    avg_metabolism: float
    avg_aggression: float
    avg_hunger_threshold: float
    avg_safe_threshold: float
    avg_resistance: float
