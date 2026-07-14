"""Company Memory — wrapper around the existing company_memory DB table."""

from datetime import datetime
from typing import Any, Dict, List, Optional

import sqlalchemy as sa

from core.db.connection import db
from core.db.models import CompanyMemory as CompanyMemoryModel
from core.db.repositories import CompanyMemoryRepository, CompanyRepository

from .base import BaseMemory, MemoryFact


class CompanyMemory(BaseMemory):
    """
    Wraps company_memory table for unified memory interface.

    Delegates storage to the existing DB schema; no in-memory buffer.
    """

    def __init__(self, user_id: str = "default"):
        super().__init__(user_id)

    def add_fact(
        self,
        fact_type: str,
        content: str,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        source: str = "unknown",
        expires_after_days: Optional[int] = None,
    ) -> MemoryFact:
        meta = metadata or {}
        company_name = meta.get("company_name")
        if not company_name:
            raise ValueError("metadata must include 'company_name'")

        with db.session_scope() as session:
            # Ensure the company row exists (FK requirement)
            CompanyRepository(session).get_or_create(company_name)
            repo = CompanyMemoryRepository(session)
            repo.add_fact(
                user_id=self.user_id,
                company_name=company_name,
                fact_type=fact_type,
                fact_data={"content": content, "confidence": confidence, "metadata": meta},
                confidence=confidence,
                source=source,
            )

        return MemoryFact(
            fact_type=fact_type,
            content=content,
            confidence=confidence,
            metadata=meta,
            source=source,
        )

    def get_facts(
        self,
        fact_type: Optional[str] = None,
        limit: int = 100,
        include_expired: bool = False,
    ) -> List[MemoryFact]:
        with db.session_scope() as session:
            stmt = (
                sa.select(CompanyMemoryModel)
                .where(CompanyMemoryModel.user_id == self.user_id)
                .order_by(CompanyMemoryModel.occurred_at.desc())
                .limit(limit)
            )
            if fact_type:
                stmt = stmt.where(CompanyMemoryModel.fact_type == fact_type)
            db_facts = list(session.execute(stmt).scalars().all())

        return [self._to_fact(r) for r in db_facts]

    def get_facts_for_company(self, company_name: str) -> List[MemoryFact]:
        with db.session_scope() as session:
            repo = CompanyMemoryRepository(session)
            db_facts = repo.get_facts_for_company(self.user_id, company_name)
        return [self._to_fact(r) for r in db_facts]

    def clear(self):
        with db.session_scope() as session:
            session.execute(
                sa.delete(CompanyMemoryModel).where(
                    CompanyMemoryModel.user_id == self.user_id
                )
            )

    @staticmethod
    def _to_fact(db_fact: CompanyMemoryModel) -> MemoryFact:
        fact_data = db_fact.fact_data or {}
        return MemoryFact(
            fact_type=db_fact.fact_type,
            content=fact_data.get("content", ""),
            confidence=db_fact.confidence,
            metadata=fact_data.get("metadata", {}),
            created_at=db_fact.occurred_at,
            source=db_fact.source or "unknown",
        )
