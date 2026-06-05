from __future__ import annotations
import random

from app.engine.creature import Creature
from app.engine.world import Direction, Position, VisionData


def _nearest(positions: list[Position], src: Position) -> Position | None:
    if not positions:
        return None
    return min(positions, key=lambda p: abs(p.x - src.x) + abs(p.y - src.y))


def _direction_toward(src: Position, target: Position) -> Direction:
    sx = 0 if target.x == src.x else (1 if target.x > src.x else -1)
    sy = 0 if target.y == src.y else (1 if target.y > src.y else -1)
    for d in Direction:
        if d.value == (sx, sy):
            return d
    return Direction.STAY


class ThresholdBehavior:
    name = "threshold"

    def decide_move(self, creature: Creature, vision: VisionData, rng: random.Random) -> Direction:
        energy = creature.energy
        hungry = energy < creature.genome.hunger_threshold
        satiated = energy > creature.genome.safe_threshold
        aggressive = creature.genome.aggression > 0.5

        if hungry:
            target = _nearest(vision.fruits, creature.position)
            if target:
                return _direction_toward(creature.position, target)
            # Flee poison when hungry; pick any empty direction
            if vision.empty_directions:
                return rng.choice(vision.empty_directions)
            return Direction.STAY

        if satiated:
            opp = [c for c in vision.creatures if c.sex != creature.sex.value]
            if opp:
                target = _nearest([c.position for c in opp], creature.position)
                assert target is not None
                return _direction_toward(creature.position, target)
            if vision.empty_directions:
                return rng.choice(vision.empty_directions)
            return Direction.STAY

        # Neutral energy band
        if aggressive:
            same = [c for c in vision.creatures if c.sex == creature.sex.value]
            if same:
                target = _nearest([c.position for c in same], creature.position)
                assert target is not None
                return _direction_toward(creature.position, target)

        if vision.empty_directions:
            return rng.choice(vision.empty_directions)
        return Direction.STAY
