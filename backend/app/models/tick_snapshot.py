from sqlalchemy import Float, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class TickSnapshot(Base):
    __tablename__ = "tick_snapshot"
    __table_args__ = (Index("ix_tick_snapshot_simulation_id", "simulation_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    simulation_id: Mapped[int] = mapped_column(Integer, ForeignKey("simulation_run.id"), nullable=False)
    tick: Mapped[int] = mapped_column(Integer, nullable=False)

    # Population
    population_total: Mapped[int] = mapped_column(Integer)
    population_male: Mapped[int] = mapped_column(Integer)
    population_female: Mapped[int] = mapped_column(Integer)

    # Energy
    avg_energy: Mapped[float] = mapped_column(Float)
    min_energy: Mapped[float] = mapped_column(Float)
    max_energy: Mapped[float] = mapped_column(Float)

    # Events
    births: Mapped[int] = mapped_column(Integer)
    deaths_total: Mapped[int] = mapped_column(Integer)
    deaths_starvation: Mapped[int] = mapped_column(Integer)
    deaths_age: Mapped[int] = mapped_column(Integer)
    deaths_fight: Mapped[int] = mapped_column(Integer)
    fights_total: Mapped[int] = mapped_column(Integer)
    reproductions_successful: Mapped[int] = mapped_column(Integer)
    reproductions_failed_space: Mapped[int] = mapped_column(Integer)
    reproductions_failed_energy: Mapped[int] = mapped_column(Integer)

    # World
    fruits_on_board: Mapped[int] = mapped_column(Integer)
    poisons_on_board: Mapped[int] = mapped_column(Integer)

    # Genome averages
    avg_lifespan: Mapped[float] = mapped_column(Float)
    avg_vision_range: Mapped[float] = mapped_column(Float)
    avg_metabolism: Mapped[float] = mapped_column(Float)
    avg_aggression: Mapped[float] = mapped_column(Float)
    avg_hunger_threshold: Mapped[float] = mapped_column(Float)
    avg_safe_threshold: Mapped[float] = mapped_column(Float)
    avg_resistance: Mapped[float] = mapped_column(Float)

    # Relationship
    run: Mapped["SimulationRun"] = relationship("SimulationRun", back_populates="snapshots")  # noqa: F821
