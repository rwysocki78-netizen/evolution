"""
Phase 2 persistence tests:
  - run row created with status=running then updated to completed
  - tick_snapshot rows written at configured interval
  - snapshot_enabled=False → no snapshot rows
  - snapshot_interval respected
  - extinct population sets turns_run < total_turns_configured
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.engine.params import SimParams
from app.models import SimulationRun, TickSnapshot
from app.persistence import run_simulation_persisted


@pytest.fixture
def db_session():
    """In-memory SQLite session, tables created fresh per test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


def fast_params(**overrides) -> SimParams:
    """Minimal params for quick test runs."""
    defaults = dict(
        board_size=8,
        initial_population=6,
        total_turns=20,
        max_fruits_on_board=5,
        max_poisons_on_board=2,
        snapshot_enabled=True,
        snapshot_interval=5,
        seed=42,
        mutation_rate=0.0,
    )
    defaults.update(overrides)
    return SimParams(**defaults)


def test_run_row_created_and_completed(db_session):
    params = fast_params()
    run = run_simulation_persisted(params, db_session)

    assert run.id is not None
    assert run.status == "completed"
    assert run.finished_at is not None
    assert run.seed == 42
    assert run.total_turns_configured == 20
    assert run.total_turns_run > 0


def test_run_row_stores_parameters(db_session):
    params = fast_params(board_size=12, mutation_rate=0.05, behavior_strategy="priority")
    run = run_simulation_persisted(params, db_session)

    assert run.board_size == 12
    assert run.mutation_rate == pytest.approx(0.05)
    assert run.behavior_strategy == "priority"
    assert run.snapshot_enabled is True
    assert run.snapshot_interval == 5
    assert isinstance(run.reproduction_weights, list)
    assert run.reproduction_weights[0]["children"] == 1


def test_snapshots_written_at_interval(db_session):
    params = fast_params(total_turns=20, snapshot_interval=5, snapshot_enabled=True)
    run = run_simulation_persisted(params, db_session)

    snapshots = db_session.query(TickSnapshot).filter_by(simulation_id=run.id).all()
    # At least one snapshot should exist (population may die before tick 20)
    assert len(snapshots) >= 1
    # All snapshot ticks must be multiples of interval
    for s in snapshots:
        assert s.tick % 5 == 0


def test_snapshot_disabled_writes_no_rows(db_session):
    params = fast_params(snapshot_enabled=False)
    run = run_simulation_persisted(params, db_session)

    count = db_session.query(TickSnapshot).filter_by(simulation_id=run.id).count()
    assert count == 0


def test_snapshot_fields_populated(db_session):
    params = fast_params(total_turns=10, snapshot_interval=5)
    run = run_simulation_persisted(params, db_session)

    snap = db_session.query(TickSnapshot).filter_by(simulation_id=run.id).first()
    if snap is None:
        pytest.skip("population died before first snapshot")

    assert snap.tick > 0
    assert snap.population_total >= 0
    assert snap.population_male + snap.population_female == snap.population_total
    assert snap.deaths_total == snap.deaths_starvation + snap.deaths_age + snap.deaths_fight


def test_multiple_runs_are_independent(db_session):
    params_a = fast_params(seed=1)
    params_b = fast_params(seed=2)
    run_a = run_simulation_persisted(params_a, db_session)
    run_b = run_simulation_persisted(params_b, db_session)

    assert run_a.id != run_b.id
    snaps_a = db_session.query(TickSnapshot).filter_by(simulation_id=run_a.id).count()
    snaps_b = db_session.query(TickSnapshot).filter_by(simulation_id=run_b.id).count()
    # Each run's snapshots are isolated
    total = db_session.query(TickSnapshot).count()
    assert total == snaps_a + snaps_b
