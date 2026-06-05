"""
In-memory store for active simulation sessions.

Each entry holds the live engine state needed to advance or inspect a
running simulation between API calls. The store is process-local; a server
restart clears it (acceptable for v1 — completed runs are in the DB).
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from app.engine.behavior.base import BehaviorStrategy
from app.engine.creature import Creature
from app.engine.params import SimParams
from app.engine.world import World


@dataclass
class SimSession:
    run_id: int
    world: World
    creatures: list[Creature]
    next_id: int
    rng: random.Random
    behavior: BehaviorStrategy
    params: SimParams
    current_tick: int = 0
    status: str = "running"  # running | completed | stopped


_sessions: dict[int, SimSession] = {}


def put(session: SimSession) -> None:
    _sessions[session.run_id] = session


def get(run_id: int) -> SimSession | None:
    return _sessions.get(run_id)


def remove(run_id: int) -> None:
    _sessions.pop(run_id, None)
