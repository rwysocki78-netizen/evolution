from __future__ import annotations
import random
from dataclasses import fields
from typing import Callable

from app.engine.creature import Genome

# Gene registry: name → (type, mutate_fn)
# mutate_fn receives (value, rng) and returns a new value
GeneRegistry: dict[str, tuple[type, Callable]] = {}


def _register():
    def int_mutate(rate: float, magnitude: int):
        def fn(v: int, rng: random.Random) -> int:
            return max(1, v + rng.randint(-magnitude, magnitude))
        return fn

    def float_mutate(rate: float, magnitude: float, floor: float = 0.0):
        def fn(v: float, rng: random.Random) -> float:
            return max(floor, v + rng.uniform(-magnitude, magnitude))
        return fn

    GeneRegistry["lifespan"] = (int, int_mutate(0.05, 5))
    GeneRegistry["vision_range"] = (int, int_mutate(0.05, 1))
    GeneRegistry["hunger_threshold"] = (int, int_mutate(0.05, 5))
    GeneRegistry["safe_threshold"] = (int, int_mutate(0.05, 5))
    GeneRegistry["metabolism"] = (float, float_mutate(0.05, 0.05))
    GeneRegistry["aggression"] = (float, float_mutate(0.05, 0.05))
    GeneRegistry["resistance"] = (float, float_mutate(0.05, 0.1, floor=0.0))


_register()


def inherit(parent_a: Genome, parent_b: Genome, mutation_rate: float, rng: random.Random) -> Genome:
    kwargs: dict = {}
    for f in fields(Genome):
        parent = parent_a if rng.random() < 0.5 else parent_b
        value = getattr(parent, f.name)
        if rng.random() < mutation_rate:
            _, mutate_fn = GeneRegistry[f.name]
            value = mutate_fn(value, rng)
        kwargs[f.name] = value
    return Genome(**kwargs)
