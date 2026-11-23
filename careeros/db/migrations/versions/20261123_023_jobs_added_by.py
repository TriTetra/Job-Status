"""jobs.added_by: a job a person added themselves (link or pasted text) is theirs alone

Revision ID: jobs_added_by_023
Revises: apply_kits_022
Create Date: 2026-11-23
"""

import sqlalchemy as sa
from alembic import op

revision = "jobs_added_by_023"
down_revision = "apply_kits_022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("added_by", sa.String(128),
                                    sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True))
    op.create_index("idx_jobs_added_by", "jobs", ["added_by"], postgresql_where=sa.text("added_by IS NOT NULL"))


def downgrade() -> None:
    op.drop_index("idx_jobs_added_by", table_name="jobs")
    op.drop_column("jobs", "added_by")
