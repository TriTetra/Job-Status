"""User-defined custom skills that extend the global skill_graph.yaml."""

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from careeros.db.base import Base, TimestampMixin


class UserCustomSkill(Base, TimestampMixin):
    """
    Skills a user adds that don't exist in the global skill ontology.
    Examples: Blender, Figma, Excel, domain-specific tools.
    """

    __tablename__ = "user_custom_skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    skill_name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "skill_name", name="uq_user_custom_skills"),
    )
