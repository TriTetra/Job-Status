"""Market signal repository — queries for trends and summaries."""

from datetime import datetime, timedelta
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy import func

from careeros.market.models.market_signal import MarketSignal
from careeros.db.repository import BaseRepository


class MarketSignalRepository(BaseRepository[MarketSignal]):
    model = MarketSignal

    def add_signal(
        self,
        signal_type: str,
        source: str,
        title: str,
        occurred_at: datetime,
        source_id: Optional[str] = None,
        impact: str = "medium",
        summary: Optional[str] = None,
        url: Optional[str] = None,
        companies_affected: Optional[List[str]] = None,
        skills_affected: Optional[List[str]] = None,
        countries_affected: Optional[List[str]] = None,
        magnitude: Optional[float] = None,
        metadata_json: Optional[dict] = None,
    ) -> MarketSignal:
        if source_id:
            existing = self.get(source_id=source_id)
            if existing:
                return existing
        return self.create(
            signal_type=signal_type,
            source=source,
            title=title,
            occurred_at=occurred_at,
            source_id=source_id,
            impact=impact,
            summary=summary,
            url=url,
            companies_affected=companies_affected or [],
            skills_affected=skills_affected or [],
            countries_affected=countries_affected or [],
            magnitude=magnitude,
            metadata_json=metadata_json or {},
        )

    def get_recent(self, days: int = 7, limit: int = 50) -> List[MarketSignal]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        stmt = (
            sa.select(self.model)
            .where(self.model.occurred_at >= cutoff)
            .order_by(self.model.occurred_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_by_type(self, signal_type: str, days: int = 30, limit: int = 20) -> List[MarketSignal]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        stmt = (
            sa.select(self.model)
            .where(self.model.signal_type == signal_type)
            .where(self.model.occurred_at >= cutoff)
            .order_by(self.model.occurred_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_for_company(self, company_name: str, days: int = 90) -> List[MarketSignal]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        stmt = (
            sa.select(self.model)
            .where(self.model.companies_affected.contains([company_name]))
            .where(self.model.occurred_at >= cutoff)
            .order_by(self.model.occurred_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_for_skill(self, skill_name: str, days: int = 90) -> List[MarketSignal]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        stmt = (
            sa.select(self.model)
            .where(self.model.skills_affected.contains([skill_name]))
            .where(self.model.occurred_at >= cutoff)
            .order_by(self.model.occurred_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_skill_trend(self, skill_name: str, days: int = 30) -> dict:
        now = datetime.utcnow()
        recent_cutoff = now - timedelta(days=days)
        previous_cutoff = now - timedelta(days=days * 2)

        def _sum_magnitude(cutoff_start, cutoff_end=None):
            stmt = (
                sa.select(func.coalesce(func.sum(self.model.magnitude), 0))
                .select_from(self.model)
                .where(
                    sa.and_(
                        self.model.skills_affected.contains([skill_name]),
                        self.model.signal_type == "skill_demand",
                        self.model.occurred_at >= cutoff_start,
                        *([self.model.occurred_at < cutoff_end] if cutoff_end else []),
                    )
                )
            )
            return float(self.session.execute(stmt).scalar() or 0)

        recent_count = _sum_magnitude(recent_cutoff)
        previous_count = _sum_magnitude(previous_cutoff, recent_cutoff)

        if previous_count > 0:
            change_pct = ((recent_count - previous_count) / previous_count) * 100
            direction = "up" if change_pct > 5 else ("down" if change_pct < -5 else "stable")
        elif recent_count > 0:
            # Geçmiş dönem yok — yeni görüldü, % gösterme
            change_pct = 0.0
            direction = "stable"
        else:
            change_pct = 0.0
            direction = "stable"

        return {
            "skill": skill_name,
            "current_count": int(recent_count),
            "previous_count": int(previous_count),
            "change_percent": round(change_pct, 1),
            "direction": direction,
        }

    def get_market_summary(self, days: int = 7) -> dict:
        cutoff = datetime.utcnow() - timedelta(days=days)

        type_counts = {}
        for signal_type in ["funding", "layoff", "hiring_spike", "skill_demand", "hiring_volume"]:
            count = self.session.execute(
                sa.select(func.count())
                .select_from(self.model)
                .where(
                    sa.and_(
                        self.model.signal_type == signal_type,
                        self.model.occurred_at >= cutoff,
                    )
                )
            ).scalar() or 0
            type_counts[signal_type] = count

        company_mentions = self.session.execute(
            sa.select(
                func.unnest(self.model.companies_affected).label("company"),
                func.count().label("cnt"),
            )
            .where(self.model.occurred_at >= cutoff)
            .group_by(sa.text("company"))
            .order_by(sa.text("cnt DESC"))
            .limit(10)
        ).all()

        skill_mentions = self.session.execute(
            sa.select(
                func.unnest(self.model.skills_affected).label("skill"),
                func.count().label("cnt"),
            )
            .where(self.model.occurred_at >= cutoff)
            .group_by(sa.text("skill"))
            .order_by(sa.text("cnt DESC"))
            .limit(10)
        ).all()

        return {
            "period_days": days,
            "signal_counts": type_counts,
            "top_companies": [{"name": r.company, "count": r.cnt} for r in company_mentions],
            "top_skills": [{"skill": r.skill, "count": r.cnt} for r in skill_mentions],
        }
