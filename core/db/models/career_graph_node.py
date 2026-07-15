"""CareerGraphNode model — nodes in a user's personal career knowledge graph."""

from typing import Optional
from sqlalchemy import String, Float, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class CareerGraphNode(Base, TimestampMixin):
    __tablename__ = "career_graph_nodes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    node_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(256), nullable=False)
    canonical_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    edges: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    node_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("idx_career_graph_nodes_user_type", "user_id", "node_type"),
        Index("idx_career_graph_nodes_canonical", "canonical_id"),
    )
