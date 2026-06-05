from __future__ import annotations

from app.engine.creature import Creature
from app.engine.world import Direction, PerceivedCreature, Position, VisionData, World

_MOVE_DIRS = [d for d in Direction if d != Direction.STAY]


def build_vision(
    creature: Creature,
    world: World,
    creatures_by_id: dict[int, Creature],
) -> VisionData:
    fruits: list[Position] = []
    poisons: list[Position] = []
    perceived: list[PerceivedCreature] = []

    seen: set[Position] = set()

    for direction in _MOVE_DIRS:
        pos = creature.position
        for _ in range(creature.genome.vision_range):
            pos = pos.move(direction)
            if not world.in_bounds(pos):
                break  # wall blocks further vision in this direction
            if pos in seen:
                continue
            seen.add(pos)
            if pos in world.fruits:
                fruits.append(pos)
            if pos in world.poisons:
                poisons.append(pos)
            if pos in world.occupied:
                other = creatures_by_id.get(world.occupied[pos])
                if other and other.alive:
                    perceived.append(PerceivedCreature(pos, other.sex.value, other.energy))

    # Empty adjacent directions: 1-step passable cells not occupied
    empty_dirs = [
        d for d in _MOVE_DIRS
        if world.is_free(creature.position.move(d))
    ]

    return VisionData(
        fruits=fruits,
        poisons=poisons,
        creatures=perceived,
        empty_directions=empty_dirs,
    )
