"""Visa repository."""

from datetime import datetime
from typing import List, Optional

import sqlalchemy as sa

from ..models import Visa
from .base import BaseRepository


class VisaRepository(BaseRepository[Visa]):
    model = Visa

    def get_by_type(self, visa_type: str) -> Optional[Visa]:
        return self.get(visa_type=visa_type)

    def get_for_country(self, country_iso: str) -> List[Visa]:
        stmt = (
            sa.select(self.model)
            .where(self.model.country == country_iso.upper())
            .order_by(self.model.visa_type)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_all(self) -> List[Visa]:
        stmt = sa.select(self.model).order_by(self.model.visa_type)
        return list(self.session.execute(stmt).scalars().all())

    def update_eligibility(self, visa_type: str, eligibility: dict, user_id: str) -> Visa:
        visa = self.get_by_type(visa_type)
        if not visa:
            raise ValueError(f"Visa {visa_type} not found")
        visa.eligibility = eligibility
        visa.last_updated_by = user_id
        visa.last_updated_at = datetime.utcnow()
        return visa
