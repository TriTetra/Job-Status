"""jobs.company_domain and jobs.company_logo: logos for companies outside companies.yaml

company_domain is the employer's website (from the board config, or found in a feed
posting's links and e-mail addresses); company_logo is a logo image URL a job feed
provides. Both feed the logo endpoint, so small companies get a logo too.

Revision ID: job_company_domain_020
Revises: telegram_links_019
Create Date: 2026-11-23
"""

import sqlalchemy as sa
from alembic import op

revision = "job_company_domain_020"
down_revision = "telegram_links_019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("company_domain", sa.String(256), nullable=True))
    op.add_column("jobs", sa.Column("company_logo", sa.String(1024), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "company_logo")
    op.drop_column("jobs", "company_domain")
