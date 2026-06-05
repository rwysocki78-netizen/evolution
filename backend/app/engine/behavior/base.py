from typing import Protocol, TYPE_CHECKING
import random

if TYPE_CHECKING:
    from app.engine.creature import Creature
    from app.engine.world import Direction, VisionData


class BehaviorStrategy(Protocol):
    name: str

    def decide_move(
        self,
        creature: "Creature",
        vision: "VisionData",
        rng: random.Random,
    ) -> "Direction": ...
