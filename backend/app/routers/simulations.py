from __future__ import annotations

import random
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import session_store
from app.db import get_db
from app.engine.params import ReproductionWeight, SimParams
from app.engine.simulation import create_creatures, create_world, make_behavior
from app.engine.tick import tick
from app.models import SimulationRun, TickSnapshot
from app.models.tick_snapshot import TickSnapshot
from app.schemas.simulations import (
    BoardStateResponse,
    CreatureOut,
    PositionOut,
    RunRequest,
    SimParamsRequest,
    SimulationResponse,
    TickResponse,
    TickSnapshotResponse,
)
from app.session_store import SimSession

router = APIRouter(prefix="/simulations", tags=["simulations"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_sim_params(req: SimParamsRequest) -> SimParams:
    return SimParams(
        board_size=req.board_size,
        initial_energy=req.initial_energy,
        max_energy=req.max_energy,
        energy_decay_per_tick=req.energy_decay_per_tick,
        fight_energy_cost=req.fight_energy_cost,
        reproduction_energy_cost=req.reproduction_energy_cost,
        reproduction_min_energy=req.reproduction_min_energy,
        maturity_age=req.maturity_age,
        juvenile_max_energy_factor=req.juvenile_max_energy_factor,
        fruit_energy_value=req.fruit_energy_value,
        poison_energy_value=req.poison_energy_value,
        resistance_reduction_per_point=req.resistance_reduction_per_point,
        max_fruits_on_board=req.max_fruits_on_board,
        max_poisons_on_board=req.max_poisons_on_board,
        mutation_rate=req.mutation_rate,
        mutation_magnitude=req.mutation_magnitude,
        initial_lifespan=(req.initial_lifespan[0], req.initial_lifespan[1]),
        initial_vision_range=(req.initial_vision_range[0], req.initial_vision_range[1]),
        initial_metabolism=(req.initial_metabolism[0], req.initial_metabolism[1]),
        initial_aggression=(req.initial_aggression[0], req.initial_aggression[1]),
        initial_hunger_threshold=(req.initial_hunger_threshold[0], req.initial_hunger_threshold[1]),
        initial_safe_threshold=(req.initial_safe_threshold[0], req.initial_safe_threshold[1]),
        initial_resistance=(req.initial_resistance[0], req.initial_resistance[1]),
        reproduction_weights=[ReproductionWeight(w.children, w.weight) for w in req.reproduction_weights],
        initial_population=req.initial_population,
        total_turns=req.total_turns,
        behavior_strategy=req.behavior_strategy,
        snapshot_enabled=req.snapshot_enabled,
        snapshot_interval=req.snapshot_interval,
        seed=req.seed,
    )


def _board_state(session: SimSession, run_id: int) -> BoardStateResponse:
    return BoardStateResponse(
        simulation_id=run_id,
        tick=session.current_tick,
        board_size=session.params.board_size,
        status=session.status,
        creatures=[
            CreatureOut(
                id=c.id,
                x=c.position.x,
                y=c.position.y,
                sex=c.sex.value,
                energy=c.energy,
                age=c.age,
            )
            for c in session.creatures
        ],
        fruits=[PositionOut(x=p.x, y=p.y) for p in session.world.fruits],
        poisons=[PositionOut(x=p.x, y=p.y) for p in session.world.poisons],
    )


def _snapshot_row(run_id: int, stats) -> TickSnapshot:
    from app.engine.stats import TickStats
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


def _advance(session: SimSession, run_id: int, db: Session, ticks: int | None) -> None:
    """Advance up to `ticks` steps (None = to completion). Mutates session in place."""
    params = session.params
    remaining = ticks  # None means unlimited

    while True:
        if session.current_tick >= params.total_turns:
            session.status = "completed"
            break
        if not session.creatures:
            session.status = "completed"
            break
        if remaining is not None and remaining <= 0:
            break

        session.current_tick += 1
        session.creatures, stats, session.next_id = tick(
            session.world,
            session.creatures,
            params,
            session.rng,
            session.behavior,
            session.next_id,
            tick_number=session.current_tick,
        )

        if params.snapshot_enabled and session.current_tick % params.snapshot_interval == 0:
            db.add(_snapshot_row(run_id, stats))

        if remaining is not None:
            remaining -= 1

        if not session.creatures:
            session.status = "completed"
            break

    if session.status == "completed":
        _finish_run(run_id, session, db)


def _finish_run(run_id: int, session: SimSession, db: Session) -> None:
    run = db.get(SimulationRun, run_id)
    if run:
        run.status = session.status
        run.total_turns_run = session.current_tick
        run.finished_at = datetime.now(timezone.utc)
        db.commit()


def _require_session(run_id: int) -> SimSession:
    session = session_store.get(run_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active session for simulation {run_id}. "
                   "The server may have restarted, or the run has already finished.",
        )
    return session


def _require_running(session: SimSession) -> None:
    if session.status != "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Simulation is {session.status}, not running.",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("", status_code=status.HTTP_201_CREATED, response_model=SimulationResponse)
def create_simulation(body: SimParamsRequest, db: Session = Depends(get_db)) -> SimulationResponse:
    """Create and initialise a new simulation run. Returns run metadata."""
    params = _to_sim_params(body)
    seed = params.seed if params.seed is not None else random.randrange(2**32)
    params = SimParams(**{**params.__dict__, "seed": seed})

    rng = random.Random(seed)
    behavior = make_behavior(params.behavior_strategy)
    world = create_world(params, rng)
    creatures, next_id = create_creatures(params, world, rng)

    rw = params.reproduction_weights
    run = SimulationRun(
        seed=seed,
        status="running",
        total_turns_configured=params.total_turns,
        total_turns_run=0,
        behavior_strategy=params.behavior_strategy,
        initial_population=params.initial_population,
        board_size=params.board_size,
        vision_range=params.initial_vision_range[0],
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
    db.add(run)
    db.commit()
    db.refresh(run)

    session_store.put(SimSession(
        run_id=run.id,
        world=world,
        creatures=creatures,
        next_id=next_id,
        rng=rng,
        behavior=behavior,
        params=params,
        current_tick=0,
        status="running",
    ))

    return SimulationResponse.model_validate(run)


@router.post("/{run_id}/step", response_model=TickResponse)
def step(run_id: int, db: Session = Depends(get_db)) -> TickResponse:
    """Advance the simulation by exactly one tick."""
    session = _require_session(run_id)
    _require_running(session)
    _advance(session, run_id, db, ticks=1)
    db.commit()
    return TickResponse(
        state=_board_state(session, run_id),
        completed=session.status != "running",
        turns_run=session.current_tick,
    )


@router.post("/{run_id}/run", response_model=TickResponse)
def run(run_id: int, body: RunRequest = RunRequest(), db: Session = Depends(get_db)) -> TickResponse:
    """Advance the simulation by N ticks (or to completion if ticks is None)."""
    session = _require_session(run_id)
    _require_running(session)
    _advance(session, run_id, db, ticks=body.ticks)
    db.commit()
    return TickResponse(
        state=_board_state(session, run_id),
        completed=session.status != "running",
        turns_run=session.current_tick,
    )


@router.post("/{run_id}/stop", status_code=status.HTTP_200_OK, response_model=SimulationResponse)
def stop(run_id: int, db: Session = Depends(get_db)) -> SimulationResponse:
    """Stop a running simulation."""
    session = _require_session(run_id)
    _require_running(session)
    session.status = "stopped"
    run = db.get(SimulationRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    run.status = "stopped"
    run.total_turns_run = session.current_tick
    run.finished_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(run)
    return SimulationResponse.model_validate(run)


@router.get("/{run_id}/state", response_model=BoardStateResponse)
def get_state(run_id: int) -> BoardStateResponse:
    """Get the current board state (live from memory)."""
    session = _require_session(run_id)
    return _board_state(session, run_id)


@router.get("", response_model=list[SimulationResponse])
def list_simulations(db: Session = Depends(get_db)) -> list[SimulationResponse]:
    """List all simulation runs (history)."""
    runs = db.query(SimulationRun).order_by(SimulationRun.started_at.desc()).all()
    return [SimulationResponse.model_validate(r) for r in runs]


@router.get("/{run_id}", response_model=SimulationResponse)
def get_simulation(run_id: int, db: Session = Depends(get_db)) -> SimulationResponse:
    """Get metadata for a specific run."""
    run = db.get(SimulationRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return SimulationResponse.model_validate(run)


@router.get("/{run_id}/stats", response_model=list[TickSnapshotResponse])
def get_stats(run_id: int, db: Session = Depends(get_db)) -> list[TickSnapshotResponse]:
    """Get per-tick snapshot time series for a run."""
    run = db.get(SimulationRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Simulation not found")
    snapshots = (
        db.query(TickSnapshot)
        .filter_by(simulation_id=run_id)
        .order_by(TickSnapshot.tick)
        .all()
    )
    return [TickSnapshotResponse.model_validate(s) for s in snapshots]
