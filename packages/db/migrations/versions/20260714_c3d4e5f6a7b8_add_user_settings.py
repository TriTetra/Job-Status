"""add_user_settings

Creates user_settings and user_custom_skills tables.
user_settings stores per-user profile, skills, preferences, and scoring weights —
everything that was previously hardcoded in config.yaml and opportunity_scorer.py.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-14 15:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None

_DEFAULT_WEIGHTS = '{"fit": 0.30, "acceptance": 0.25, "career_value": 0.25, "market_demand": 0.20}'


def upgrade() -> None:
    op.create_table(
        "user_settings",
        sa.Column("user_id", sa.String(100), primary_key=True),
        sa.Column("profile", JSONB, nullable=False, server_default="{}"),
        sa.Column("skills", JSONB, nullable=False, server_default="[]"),
        sa.Column("preferences", JSONB, nullable=False, server_default="{}"),
        sa.Column("weights", JSONB, nullable=False, server_default=_DEFAULT_WEIGHTS),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )

    op.create_table(
        "user_custom_skills",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(100), nullable=False, index=True),
        sa.Column("skill_name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "skill_name", name="uq_user_custom_skills"),
    )

    # Seed default user from config.yaml values so existing scripts keep working
    op.execute(f"""
        INSERT INTO user_settings (user_id, profile, skills, preferences, weights)
        VALUES (
            'default',
            '{{"name": "Default User", "years_experience": 2}}',
            '[]',
            '{{"remote": true, "work_visa_required": false}}',
            '{_DEFAULT_WEIGHTS}'
        )
        ON CONFLICT (user_id) DO NOTHING
    """)


def downgrade() -> None:
    op.drop_table("user_custom_skills")
    op.drop_table("user_settings")
