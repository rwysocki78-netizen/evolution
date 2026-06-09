from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.engine.params import SimParams as _SimParams

_d = _SimParams()  # single source of default values


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------

class ReproductionWeightIn(BaseModel):
    children: int = Field(ge=1)
    weight: float = Field(gt=0)


class SimParamsRequest(BaseModel):
    # Board
    board_size: int = _d.board_size

    # Energy
    initial_energy: float = _d.initial_energy
    max_energy: float = _d.max_energy
    energy_decay_per_tick: float = _d.energy_decay_per_tick
    fight_energy_cost: float = _d.fight_energy_cost
    reproduction_energy_cost: float = _d.reproduction_energy_cost
    reproduction_min_energy: float = _d.reproduction_min_energy

    # Life stage
    maturity_age: int = _d.maturity_age
    juvenile_max_energy_factor: float = _d.juvenile_max_energy_factor

    # World
    fruit_energy_value: float = _d.fruit_energy_value
    poison_energy_value: float = _d.poison_energy_value
    resistance_reduction_per_point: float = _d.resistance_reduction_per_point
    max_fruits_on_board: int = _d.max_fruits_on_board
    max_poisons_on_board: int = _d.max_poisons_on_board

    # Mutation
    mutation_rate: float = _d.mutation_rate
    mutation_magnitude: float = _d.mutation_magnitude

    # Genome initial ranges [min, max]
    initial_lifespan: list[int] = Field(
        default_factory=lambda: list(_d.initial_lifespan), min_length=2, max_length=2)
    initial_vision_range: list[int] = Field(
        default_factory=lambda: list(_d.initial_vision_range), min_length=2, max_length=2)
    initial_metabolism: list[float] = Field(
        default_factory=lambda: list(_d.initial_metabolism), min_length=2, max_length=2)
    initial_aggression: list[float] = Field(
        default_factory=lambda: list(_d.initial_aggression), min_length=2, max_length=2)
    initial_hunger_threshold: list[int] = Field(
        default_factory=lambda: list(_d.initial_hunger_threshold), min_length=2, max_length=2)
    initial_safe_threshold: list[int] = Field(
        default_factory=lambda: list(_d.initial_safe_threshold), min_length=2, max_length=2)
    initial_resistance: list[float] = Field(
        default_factory=lambda: list(_d.initial_resistance), min_length=2, max_length=2)

    # Reproduction
    reproduction_weights: list[ReproductionWeightIn] = Field(
        default_factory=lambda: [
            ReproductionWeightIn(children=w.children, weight=w.weight)
            for w in _d.reproduction_weights
        ]
    )

    # Population & simulation
    initial_population: int = _d.initial_population
    total_turns: int = _d.total_turns
    behavior_strategy: str = _d.behavior_strategy
    snapshot_enabled: bool = _d.snapshot_enabled
    snapshot_interval: int = _d.snapshot_interval
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
