"""
Phase 1 genetics tests:
  - child gene comes from one parent or the other (never neither)
  - mutation rate and magnitude behave as configured
"""
import random
import pytest
from tests.engine.conftest import make_genome
from app.engine.genetics import inherit


def test_child_gene_from_one_parent():
    """Every gene must come from parent A or parent B — no blending."""
    rng = random.Random(0)
    pa = make_genome(lifespan=80, vision_range=1, metabolism=0.8, aggression=0.2, resistance=0.5,
                     hunger_threshold=20, safe_threshold=60)
    pb = make_genome(lifespan=120, vision_range=3, metabolism=1.4, aggression=0.9, resistance=1.5,
                     hunger_threshold=40, safe_threshold=90)

    for _ in range(200):
        child = inherit(pa, pb, mutation_rate=0.0, mutation_magnitude=1.0, rng=rng)
        assert child.lifespan in (pa.lifespan, pb.lifespan)
        assert child.vision_range in (pa.vision_range, pb.vision_range)
        assert child.metabolism in (pa.metabolism, pb.metabolism)
        assert child.aggression in (pa.aggression, pb.aggression)
        assert child.resistance in (pa.resistance, pb.resistance)
        assert child.hunger_threshold in (pa.hunger_threshold, pb.hunger_threshold)
        assert child.safe_threshold in (pa.safe_threshold, pb.safe_threshold)


def test_gene_distribution_is_roughly_50_50():
    """With no mutation, each parent contributes ~50% of genes."""
    rng = random.Random(1)
    pa = make_genome(lifespan=50)
    pb = make_genome(lifespan=150)

    from_a = sum(
        1 for _ in range(1000)
        if inherit(pa, pb, 0.0, 1.0, rng).lifespan == 50
    )
    # Expect between 40% and 60% from each parent
    assert 400 <= from_a <= 600


def test_mutation_changes_value():
    """With mutation_rate=1.0 every gene mutates."""
    rng = random.Random(2)
    parent = make_genome(lifespan=100, vision_range=2, metabolism=1.0,
                         aggression=0.5, resistance=1.0,
                         hunger_threshold=30, safe_threshold=70)

    changed = 0
    for _ in range(50):
        child = inherit(parent, parent, mutation_rate=1.0, mutation_magnitude=5.0, rng=rng)
        if child.lifespan != parent.lifespan:
            changed += 1
    assert changed > 0, "lifespan should mutate when mutation_rate=1.0"


def test_resistance_mutation_floored_at_zero():
    """resistance must never go below 0 after mutation."""
    rng = random.Random(3)
    parent = make_genome(resistance=0.0)
    for _ in range(500):
        child = inherit(parent, parent, mutation_rate=1.0, mutation_magnitude=10.0, rng=rng)
        assert child.resistance >= 0.0


def test_vision_range_mutation_floored_at_one():
    """vision_range must be at least 1 after mutation."""
    rng = random.Random(4)
    parent = make_genome(vision_range=1)
    for _ in range(500):
        child = inherit(parent, parent, mutation_rate=1.0, mutation_magnitude=10.0, rng=rng)
        assert child.vision_range >= 1
