"""
Phase 3 API tests — full endpoint contracts via FastAPI test client.
Uses an in-memory SQLite DB and clears the session store between tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import session_store
from app.db import Base, get_db
from app.main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_sessions():
    """Isolate session store between tests."""
    session_store._sessions.clear()
    yield
    session_store._sessions.clear()


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()


def minimal_params(**overrides):
    defaults = {
        "board_size": 8,
        "initial_population": 6,
        "total_turns": 30,
        "max_fruits_on_board": 4,
        "max_poisons_on_board": 2,
        "snapshot_enabled": True,
        "snapshot_interval": 5,
        "seed": 42,
        "mutation_rate": 0.0,
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# POST /simulations
# ---------------------------------------------------------------------------

def test_create_simulation_returns_201(client):
    r = client.post("/simulations", json=minimal_params())
    assert r.status_code == 201
    body = r.json()
    assert body["id"] > 0
    assert body["status"] == "running"
    assert body["seed"] == 42


def test_create_assigns_seed_when_none(client):
    r = client.post("/simulations", json=minimal_params(seed=None))
    assert r.status_code == 201
    assert r.json()["seed"] is not None


def test_create_stores_params(client):
    r = client.post("/simulations", json=minimal_params(board_size=12, behavior_strategy="priority"))
    body = r.json()
    assert body["board_size"] == 12
    assert body["behavior_strategy"] == "priority"


# ---------------------------------------------------------------------------
# POST /simulations/{id}/step
# ---------------------------------------------------------------------------

def test_step_advances_one_tick(client):
    run_id = client.post("/simulations", json=minimal_params()).json()["id"]
    r = client.post(f"/simulations/{run_id}/step")
    assert r.status_code == 200
    body = r.json()
    assert body["turns_run"] == 1
    assert "state" in body
    assert body["state"]["tick"] == 1


def test_step_returns_board_state(client):
    run_id = client.post("/simulations", json=minimal_params()).json()["id"]
    r = client.post(f"/simulations/{run_id}/step")
    state = r.json()["state"]
    assert "creatures" in state
    assert "fruits" in state
    assert "poisons" in state
    assert state["board_size"] == 8


def test_step_unknown_run_returns_404(client):
    r = client.post("/simulations/9999/step")
    assert r.status_code == 404


def test_step_stopped_run_returns_409(client):
    run_id = client.post("/simulations", json=minimal_params()).json()["id"]
    client.post(f"/simulations/{run_id}/stop")
    r = client.post(f"/simulations/{run_id}/step")
    assert r.status_code == 409


# ---------------------------------------------------------------------------
# POST /simulations/{id}/run
# ---------------------------------------------------------------------------

def test_run_n_ticks(client):
    run_id = client.post("/simulations", json=minimal_params()).json()["id"]
    r = client.post(f"/simulations/{run_id}/run", json={"ticks": 5})
    assert r.status_code == 200
    assert r.json()["turns_run"] == 5


def test_run_to_completion(client):
    # Short run to ensure it completes quickly
    params = minimal_params(total_turns=10, initial_population=4, board_size=6)
    run_id = client.post("/simulations", json=params).json()["id"]
    r = client.post(f"/simulations/{run_id}/run", json={})
    body = r.json()
    assert r.status_code == 200
    assert body["completed"] is True


def test_run_unknown_returns_404(client):
    r = client.post("/simulations/9999/run", json={"ticks": 5})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# POST /simulations/{id}/stop
# ---------------------------------------------------------------------------

def test_stop_sets_status_stopped(client):
    run_id = client.post("/simulations", json=minimal_params()).json()["id"]
    client.post(f"/simulations/{run_id}/step")
    r = client.post(f"/simulations/{run_id}/stop")
    assert r.status_code == 200
    assert r.json()["status"] == "stopped"


def test_stop_already_stopped_returns_409(client):
    run_id = client.post("/simulations", json=minimal_params()).json()["id"]
    client.post(f"/simulations/{run_id}/stop")
    r = client.post(f"/simulations/{run_id}/stop")
    assert r.status_code == 409


# ---------------------------------------------------------------------------
# GET /simulations/{id}/state
# ---------------------------------------------------------------------------

def test_get_state_returns_board(client):
    run_id = client.post("/simulations", json=minimal_params()).json()["id"]
    client.post(f"/simulations/{run_id}/step")
    r = client.get(f"/simulations/{run_id}/state")
    assert r.status_code == 200
    state = r.json()
    assert state["simulation_id"] == run_id
    assert state["tick"] == 1


def test_get_state_unknown_returns_404(client):
    r = client.get("/simulations/9999/state")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# GET /simulations
# ---------------------------------------------------------------------------

def test_list_simulations(client):
    client.post("/simulations", json=minimal_params())
    client.post("/simulations", json=minimal_params())
    r = client.get("/simulations")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_list_empty(client):
    r = client.get("/simulations")
    assert r.status_code == 200
    assert r.json() == []


# ---------------------------------------------------------------------------
# GET /simulations/{id}
# ---------------------------------------------------------------------------

def test_get_simulation_metadata(client):
    run_id = client.post("/simulations", json=minimal_params()).json()["id"]
    r = client.get(f"/simulations/{run_id}")
    assert r.status_code == 200
    assert r.json()["id"] == run_id


def test_get_simulation_unknown_returns_404(client):
    r = client.get("/simulations/9999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# GET /simulations/{id}/stats
# ---------------------------------------------------------------------------

def test_stats_empty_before_interval(client):
    run_id = client.post("/simulations", json=minimal_params(snapshot_interval=10)).json()["id"]
    # Only run 3 ticks — no snapshot yet
    for _ in range(3):
        client.post(f"/simulations/{run_id}/step")
    r = client.get(f"/simulations/{run_id}/stats")
    assert r.status_code == 200
    assert r.json() == []


def test_stats_written_at_interval(client):
    run_id = client.post("/simulations", json=minimal_params(snapshot_interval=5)).json()["id"]
    client.post(f"/simulations/{run_id}/run", json={"ticks": 10})
    r = client.get(f"/simulations/{run_id}/stats")
    assert r.status_code == 200
    snaps = r.json()
    assert len(snaps) >= 1
    for s in snaps:
        assert s["tick"] % 5 == 0


def test_stats_unknown_run_returns_404(client):
    r = client.get("/simulations/9999/stats")
    assert r.status_code == 404
