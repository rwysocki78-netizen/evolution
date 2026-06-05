from dataclasses import dataclass
from enum import Enum

from app.engine.world import Position


class Sex(Enum):
    MALE = "male"
    FEMALE = "female"


@dataclass
class Genome:
    lifespan: int
    vision_range: int
    hunger_threshold: int
    safe_threshold: int
    metabolism: float
    aggression: float
    resistance: float


@dataclass
class Creature:
    id: int
    position: Position
    sex: Sex
    genome: Genome
    energy: float
    age: int = 0
    alive: bool = True
