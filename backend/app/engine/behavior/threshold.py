from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.engine.creature import Creature
    from app.engine.world import Direction, VisionData


class ThresholdBehavior:
    name = "threshold"

    def decide_move(self, creature: "Creature", vision: "VisionData") -> "Direction":
        raise NotImplementedError
