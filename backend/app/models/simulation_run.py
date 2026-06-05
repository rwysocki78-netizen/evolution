from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class SimulationRun(Base):
    __tablename__ = "simulation_run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("running", "completed", "stopped", name="run_status"), default="running"
    )
    seed: Mapped[int] = mapped_column(Integer)
    total_turns_configured: Mapped[int] = mapped_column(Integer)
    total_turns_run: Mapped[int] = mapped_column(Integer, default=0)
    behavior_strategy: Mapped[str] = mapped_column(String(64))

    # Population
    initial_population: Mapped[int] = mapped_column(Integer)

    # Board
    board_size: Mapped[int] = mapped_column(Integer)

    # Vision
    vision_range: Mapped[int] = mapped_column(Integer)

    # Energy
    initial_energy: Mapped[float] = mapped_column(Float)
    max_energy: Mapped[float] = mapped_column(Float)
    energy_decay_per_tick: Mapped[float] = mapped_column(Float)
    fight_energy_cost: Mapped[float] = mapped_column(Float)
    reproduction_energy_cost: Mapped[float] = mapped_column(Float)
    reproduction_min_energy: Mapped[float] = mapped_column(Float)

    # Life stage
    maturity_age: Mapped[int] = mapped_column(Integer)
    juvenile_max_energy_factor: Mapped[float] = mapped_column(Float)

    # World objects
    fruit_energy_value: Mapped[float] = mapped_column(Float)
    poison_energy_value: Mapped[float] = mapped_column(Float)
    resistance_reduction_per_point: Mapped[float] = mapped_column(Float)
    max_fruits: Mapped[int] = mapped_column(Integer)
    max_poisons: Mapped[int] = mapped_column(Integer)

    # Mutation
    mutation_rate: Mapped[float] = mapped_column(Float)
    mutation_magnitude: Mapped[float] = mapped_column(Float)

    # Genome initial ranges
    lifespan_min: Mapped[int] = mapped_column(Integer)
    lifespan_max: Mapped[int] = mapped_column(Integer)
    vision_range_min: Mapped[int] = mapped_column(Integer)
    vision_range_max: Mapped[int] = mapped_column(Integer)
    metabolism_min: Mapped[float] = mapped_column(Float)
    metabolism_max: Mapped[float] = mapped_column(Float)
    aggression_min: Mapped[float] = mapped_column(Float)
    aggression_max: Mapped[float] = mapped_column(Float)
    hunger_threshold_min: Mapped[int] = mapped_column(Integer)
    hunger_threshold_max: Mapped[int] = mapped_column(Integer)
    safe_threshold_min: Mapped[int] = mapped_column(Integer)
    safe_threshold_max: Mapped[int] = mapped_column(Integer)
    resistance_min: Mapped[float] = mapped_column(Float)
    resistance_max: Mapped[float] = mapped_column(Float)

    # Reproduction weights (JSON array of {children, weight})
    reproduction_weights: Mapped[list] = mapped_column(JSON)

    # Snapshot config
    snapshot_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    snapshot_interval: Mapped[int] = mapped_column(Integer, default=10)

    # Relationship
    snapshots: Mapped[list["TickSnapshot"]] = relationship(  # noqa: F821
        "TickSnapshot", back_populates="run", cascade="all, delete-orphan"
    )
