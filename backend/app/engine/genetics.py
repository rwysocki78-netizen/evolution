from __future__ import annotations
import random
from dataclasses import dataclass, fields

from app.engine.creature import Genome


@dataclass
class GeneDef:
    name: str
    gene_type: type  # int or float
    floor: float | None = None  # lower bound on mutated value


GENE_DEFS: list[GeneDef] = [
    GeneDef("lifespan", int, floor=1),
    GeneDef("vision_range", int, floor=1),
    GeneDef("hunger_threshold", int, floor=1),
    GeneDef("safe_threshold", int, floor=1),
    GeneDef("metabolism", float, floor=0.01),
    GeneDef("aggression", float, floor=0.0),
    GeneDef("resistance", float, floor=0.0),
]

_GENE_MAP: dict[str, GeneDef] = {g.name: g for g in GENE_DEFS}


def _mutate(gene_def: GeneDef, value: float | int, magnitude: float, rng: random.Random) -> float | int:
    if gene_def.gene_type is int:
        mag = max(1, round(magnitude))
        result: float | int = value + rng.randint(-mag, mag)
    else:
        result = value + rng.uniform(-magnitude, magnitude)

    if gene_def.floor is not None:
        result = max(gene_def.floor, result)

    if gene_def.gene_type is int:
        return int(round(result))
    return float(result)


def inherit(
    parent_a: Genome,
    parent_b: Genome,
    mutation_rate: float,
    mutation_magnitude: float,
    rng: random.Random,
) -> Genome:
    kwargs: dict = {}
    for f in fields(Genome):
        parent = parent_a if rng.random() < 0.5 else parent_b
        value = getattr(parent, f.name)
        if rng.random() < mutation_rate:
            value = _mutate(_GENE_MAP[f.name], value, mutation_magnitude, rng)
        kwargs[f.name] = value
    return Genome(**kwargs)
