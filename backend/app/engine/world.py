from dataclasses import dataclass, field
from enum import Enum
from typing import NamedTuple


class Direction(Enum):
    N = (0, -1)
    NE = (1, -1)
    E = (1, 0)
    SE = (1, 1)
    S = (0, 1)
    SW = (-1, 1)
    W = (-1, 0)
    NW = (-1, -1)
    STAY = (0, 0)


class Position(NamedTuple):
    x: int
    y: int

    def move(self, direction: Direction) -> "Position":
        dx, dy = direction.value
        return Position(self.x + dx, self.y + dy)


@dataclass
class PerceivedCreature:
    position: Position
    sex: str
    energy: float


@dataclass
class VisionData:
    fruits: list[Position] = field(default_factory=list)
    poisons: list[Position] = field(default_factory=list)
    creatures: list[PerceivedCreature] = field(default_factory=list)
    empty_directions: list[Direction] = field(default_factory=list)


@dataclass
class World:
    width: int
    height: int
    walls: set[Position] = field(default_factory=set)
    fruits: set[Position] = field(default_factory=set)
    poisons: set[Position] = field(default_factory=set)
    # occupancy filled by tick.py
    occupied: dict[Position, int] = field(default_factory=dict)  # position → creature id

    def in_bounds(self, pos: Position) -> bool:
        return 0 <= pos.x < self.width and 0 <= pos.y < self.height

    def is_passable(self, pos: Position) -> bool:
        return self.in_bounds(pos) and pos not in self.walls

    def is_free(self, pos: Position) -> bool:
        return self.is_passable(pos) and pos not in self.occupied
