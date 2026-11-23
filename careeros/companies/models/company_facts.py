"""Public facts about an employer, each section with its source and when it was read
(careeros/companies/facts.py): Wikidata, Companies House, Hacker News discussion."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from careeros.db.base import Base, TimestampMixin


class CompanyFacts(Base, TimestampMixin):
    __tablename__ = "company_facts"

    key: Mapped[str] = mapped_column(String(200), primary_key=True)        # normalized company name
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    wikidata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)          # {} = looked, nothing found
    companies_house: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    people: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)            # Hacker News summary
    read_at: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)      # section → ISO time
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
