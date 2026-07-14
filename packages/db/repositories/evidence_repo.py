"""Evidence repository — skill proof records."""

from typing import Dict, List

from sqlalchemy import func, select

from ..models.evidence import Evidence
from .base import BaseRepository


class EvidenceRepository(BaseRepository[Evidence]):
    model = Evidence

    def add_evidence(
        self,
        skill_name: str,
        project_name: str,
        github_url: str | None = None,
        author_commits: int = 0,
        stars: int = 0,
        confidence: float = 0.0,
        evaluation_scores: dict | None = None,
        evidence_type: str = "github_project",
        user_id: str = "default",
    ) -> Evidence:
        return self.create(
            user_id=user_id,
            skill_name=skill_name,
            project_name=project_name,
            github_url=github_url,
            author_commits=author_commits,
            stars=stars,
            confidence=confidence,
            evaluation_scores=evaluation_scores or {},
            evidence_type=evidence_type,
        )

    def get_for_skill(self, skill_name: str, user_id: str = "default") -> List[Evidence]:
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.skill_name == skill_name)
            .order_by(self.model.confidence.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def calculate_skill_confidence(self, skill_name: str, user_id: str = "default") -> float:
        """Commit-weighted average confidence across all evidence for a skill."""
        rows = self.get_for_skill(skill_name, user_id=user_id)
        if not rows:
            return 0.0
        total_weight = sum(max(1, r.author_commits) for r in rows)
        weighted = sum(r.confidence * max(1, r.author_commits) for r in rows)
        return weighted / total_weight

    def skill_summary(self, user_id: str = "default") -> Dict[str, dict]:
        """Aggregate stats per skill — useful for reports / debug."""
        stmt = (
            select(
                self.model.skill_name,
                func.count().label("evidence_count"),
                func.avg(self.model.confidence).label("avg_confidence"),
                func.sum(self.model.author_commits).label("total_commits"),
                func.sum(self.model.stars).label("total_stars"),
            )
            .where(self.model.user_id == user_id)
            .group_by(self.model.skill_name)
            .order_by(func.avg(self.model.confidence).desc())
        )
        return {
            row.skill_name: {
                "evidence_count": row.evidence_count,
                "avg_confidence": float(row.avg_confidence or 0),
                "total_commits": row.total_commits or 0,
                "total_stars": row.total_stars or 0,
            }
            for row in self.session.execute(stmt).all()
        }
