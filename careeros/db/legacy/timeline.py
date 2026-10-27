"""Timeline models for temporal entity tracking."""

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from careeros.db.base import Base


class TimelineSnapshot(Base):
    """Entity state at a point in time."""

    __tablename__ = "timeline_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(500), nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    snapshot_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default="now()"
    )

    __table_args__ = (
        Index("idx_timeline_entity", "entity_type", "entity_id"),
        Index("idx_timeline_time", "snapshot_at"),
    )


class TimelineChange(Base):
    """Field-level change log — one row per changed field per snapshot."""

    __tablename__ = "timeline_changes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(500), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    change_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default="now()"
    )

    __table_args__ = (
        Index("idx_changes_entity", "entity_type", "entity_id"),
        Index("idx_changes_time", "changed_at"),
        Index("idx_changes_field", "field_name"),
    )
