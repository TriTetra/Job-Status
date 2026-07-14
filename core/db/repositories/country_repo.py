"""Country repository."""

from datetime import datetime
from typing import List, Optional

import sqlalchemy as sa

from ..models import Country
from .base import BaseRepository


class CountryRepository(BaseRepository[Country]):
    model = Country

    def get_by_iso(self, iso_code: str) -> Optional[Country]:
        return self.get(iso_code=iso_code.upper())

    def get_all(self) -> List[Country]:
        stmt = sa.select(self.model).order_by(self.model.name)
        return list(self.session.execute(stmt).scalars().all())

    def get_by_visa_type(self, visa_type: str) -> List[Country]:
        stmt = (
            sa.select(self.model)
            .where(self.model.primary_visa == visa_type)
            .order_by(self.model.name)
        )
        return list(self.session.execute(stmt).scalars().all())

    def search_by_name(self, query: str) -> List[Country]:
        stmt = (
            sa.select(self.model)
            .where(self.model.name.ilike(f"%{query}%"))
            .order_by(self.model.name)
        )
        return list(self.session.execute(stmt).scalars().all())

    def update_salary_range(
        self, iso_code: str, role: str, level: str, new_range: dict, user_id: str
    ) -> Country:
        country = self.get_by_iso(iso_code)
        if not country:
            raise ValueError(f"Country {iso_code} not found")
        salaries = dict(country.salary_ranges or {})
        salaries.setdefault(role, {})[level] = new_range
        country.salary_ranges = salaries
        country.last_updated_by = user_id
        country.last_updated_at = datetime.utcnow()
        return country

    def update_tech_hubs(self, iso_code: str, tech_hubs: list, user_id: str) -> Country:
        country = self.get_by_iso(iso_code)
        if not country:
            raise ValueError(f"Country {iso_code} not found")
        country.tech_hubs = tech_hubs
        country.last_updated_by = user_id
        country.last_updated_at = datetime.utcnow()
        return country
