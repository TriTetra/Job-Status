"""add market_skills registry (hybrid skill detection)

Revision ID: market_skills_001
Revises: goals_registry_001
Create Date: 2026-08-08 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "market_skills_001"
down_revision = "goals_registry_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_skills",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("source", sa.String(50), nullable=False, server_default="seed_match"),
        sa.Column("mention_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("metadata_json", JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index("ix_market_skills_name", "market_skills", ["name"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_market_skills_name", table_name="market_skills")
    op.drop_table("market_skills")
