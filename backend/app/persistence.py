"""
Bridges the simulation engine to the database.

Responsibilities:
  - Create a simulation_run row when a run starts.
  - Write tick_snapshot rows at the configured interval.
  - Update status / finished_at / total_turns_run on completion.
"""
from __future__ import annotations

import random
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.engine.params import SimParams
from app.engine.simulation import create_creatures, create_world, make_behavior
from app.engine.stats import TickStats
from app.engine.tick import tick
from app.models.simulation_run import SimulationRun
from app.models.tick_snapshot import TickSnapshot


def _run_row(params: SimParams, seed: int) -> SimulationRun:
    rw = params.reproduction_weights
    return SimulationRun(
        seed=seed,
        status="running",
        total_turns_configured=params.total_turns,
        total_turns_run=0,
        behavior_strategy=params.behavior_strategy,
        initial_population=params.initial_population,
        board_size=params.board_size,
        vision_range=params.initial_vision_range[0],  # default range from initial range lo
        initial_energy=params.initial_energy,
        max_energy=params.max_energy,
        energy_decay_per_tick=params.energy_decay_per_tick,
        fight_energy_cost=params.fight_energy_cost,
        reproduction_energy_cost=params.reproduction_energy_cost,
        reproduction_min_energy=params.reproduction_min_energy,
        maturity_age=params.maturity_age,
        juvenile_max_energy_factor=params.juvenile_max_energy_factor,
        fruit_energy_value=params.fruit_energy_value,
        poison_energy_value=params.poison_energy_value,
        resistance_reduction_per_point=params.resistance_reduction_per_point,
        max_fruits=params.max_fruits_on_board,
        max_poisons=params.max_poisons_on_board,
        mutation_rate=params.mutation_rate,
        mutation_magnitude=params.mutation_magnitude,
        lifespan_min=params.initial_lifespan[0],
        lifespan_max=params.initial_lifespan[1],
        vision_range_min=params.initial_vision_range[0],
        vision_range_max=params.initial_vision_range[1],
        metabolism_min=params.initial_metabolism[0],
        metabolism_max=params.initial_metabolism[1],
        aggression_min=params.initial_aggression[0],
        aggression_max=params.initial_aggression[1],
        hunger_threshold_min=params.initial_hunger_threshold[0],
        hunger_threshold_max=params.initial_hunger_threshold[1],
        safe_threshold_min=params.initial_safe_threshold[0],
        safe_threshold_max=params.initial_safe_threshold[1],
        resistance_min=params.initial_resistance[0],
        resistance_max=params.initial_resistance[1],
        reproduction_weights=[{"children": w.children, "weight": w.weight} for w in rw],
        snapshot_enabled=params.snapshot_enabled,
        snapshot_interval=params.snapshot_interval,
    )


def _snapshot_row(run_id: int, stats: TickStats) -> TickSnapshot:
    deaths_total = stats.deaths_starvation + stats.deaths_age + stats.deaths_fight
    return TickSnapshot(
        simulation_id=run_id,
        tick=stats.tick,
        population_total=stats.population_total,
        population_male=stats.population_male,
        population_female=stats.population_female,
        avg_energy=stats.energy_avg,
        min_energy=stats.energy_min,
        max_energy=stats.energy_max,
        births=stats.births,
        deaths_total=deaths_total,
        deaths_starvation=stats.deaths_starvation,
        deaths_age=stats.deaths_age,
        deaths_fight=stats.deaths_fight,
        fights_total=stats.fights_total,
        reproductions_successful=stats.reproductions_success,
        reproductions_failed_space=stats.reproductions_failed_space,
        reproductions_failed_energy=stats.reproductions_failed_energy,
        fruits_on_board=stats.fruits_count,
        poisons_on_board=stats.poisons_count,
        avg_lifespan=stats.avg_lifespan,
        avg_vision_range=stats.avg_vision_range,
        avg_metabolism=stats.avg_metabolism,
        avg_aggression=stats.avg_aggression,
        avg_hunger_threshold=stats.avg_hunger_threshold,
        avg_safe_threshold=stats.avg_safe_threshold,
        avg_resistance=stats.avg_resistance,
    )


def run_simulation_persisted(params: SimParams, db: Session) -> SimulationRun:
    """
    Run a full simulation, persisting the run row and tick snapshots.

    Returns the completed SimulationRun ORM object.
    """
    seed = params.seed if params.seed is not None else random.randrange(2**32)
    rng = random.Random(seed)
    behavior = make_behavior(params.behavior_strategy)

    # Create and persist the run row immediately
    run = _run_row(params, seed)
    db.add(run)
    db.flush()  # get run.id without committing

    world = create_world(params, rng)
    creatures, next_id = create_creatures(params, world, rng)

    turns_run = 0
    final_status = "completed"

    for t in range(1, params.total_turns + 1):
        creatures, stats, next_id = tick(world, creatures, params, rng, behavior, next_id, tick_number=t)
        turns_run = t

        if params.snapshot_enabled and t % params.snapshot_interval == 0:
            db.add(_snapshot_row(run.id, stats))

        if not creatures:
            break  # population extinct

    run.total_turns_run = turns_run
    run.status = final_status
    run.finished_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(run)
    return run


def stop_simulation(run: SimulationRun, turns_run: int, db: Session) -> None:
    """Mark a run as stopped (called by the API stop endpoint)."""
    run.status = "stopped"
    run.total_turns_run = turns_run
    run.finished_at = datetime.now(timezone.utc)
    db.commit()
