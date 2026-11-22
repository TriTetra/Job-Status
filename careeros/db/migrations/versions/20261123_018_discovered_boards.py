"""discovered_boards: company job boards found through job feeds

Revision ID: discovered_boards_018
Revises: applications_017
Create Date: 2026-11-23
"""

import sqlalchemy as sa
from alembic import op

revision = "discovered_boards_018"
down_revision = "applications_017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "discovered_boards",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("ats", sa.String(32), nullable=False),
        sa.Column("board", sa.String(256), nullable=False),
        sa.Column("host", sa.String(256), nullable=False, server_default=""),
        sa.Column("domain", sa.String(256), nullable=False, server_default=""),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("source_url", sa.String(2048), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("failures", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("ats", "board", name="uq_discovered_boards_ats_board"),
    )


def downgrade() -> None:
    op.drop_table("discovered_boards")
