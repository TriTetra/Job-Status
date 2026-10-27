"""Salary range repository."""

from datetime import datetime
from typing import List, Optional

import sqlalchemy as sa

from careeros.knowledge.models.salary_range import SalaryRange
from careeros.db.repository import BaseRepository


class SalaryRangeRepository(BaseRepository[SalaryRange]):
    model = SalaryRange

    def get_salary(
        self,
        role_family: str,
        country: Optional[str] = None,
        region: Optional[str] = None,
        level: Optional[str] = None,
    ) -> List[SalaryRange]:
        stmt = sa.select(self.model).where(self.model.role_family == role_family)
        if country:
            stmt = stmt.where(self.model.country == country.upper())
        if region:
            stmt = stmt.where(self.model.region == region)
        if level:
            stmt = stmt.where(self.model.level == level)
        stmt = stmt.order_by(self.model.country, self.model.region, self.model.level)
        return list(self.session.execute(stmt).scalars().all())

    def get_by_id(self, record_id: int) -> Optional[SalaryRange]:
        return self.get(id=record_id)

    def update_salary(
        self, record_id: int, new_min: int, new_max: int, user_id: str
    ) -> SalaryRange:
        salary = self.get_by_id(record_id)
        if not salary:
            raise ValueError(f"Salary range {record_id} not found")
        salary.min_salary = new_min
        salary.max_salary = new_max
        salary.median_salary = (new_min + new_max) // 2
        salary.last_updated_by = user_id
        salary.last_updated_at = datetime.utcnow()
        return salary

    def get_role_summary(self, role_family: str) -> dict:
        salaries = self.get_salary(role_family)
        if not salaries:
            return {"role": role_family, "count": 0}
        by_loc: dict = {}
        for s in salaries:
            key = s.country or s.region or "global"
            by_loc.setdefault(key, []).append(s)
        return {
            "role": role_family,
            "total_records": len(salaries),
            "countries": len([k for k in by_loc if len(k) == 2]),
            "regions": len([k for k in by_loc if len(k) > 2]),
            "by_location": {
                k: {"count": len(v), "min": min(s.min_salary for s in v), "max": max(s.max_salary for s in v)}
                for k, v in by_loc.items()
            },
        }

    def get_all_roles(self) -> List[str]:
        stmt = (
            sa.select(self.model.role_family)
            .distinct()
            .order_by(self.model.role_family)
        )
        return list(self.session.execute(stmt).scalars().all())
