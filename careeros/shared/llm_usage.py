"""LLM spend: the llm_calls log and the daily budgets enforced from it.

One row per call attempt the gateway made or refused — task, model, user,
tokens, cost, latency, status. Prompts and outputs are never stored.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from careeros.db.base import Base
from careeros.shared.llm import CallRecord, LLMBudgetExceeded


class LLMCall(Base):
    __tablename__ = "llm_calls"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    task: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)  # ok | error | budget
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cost_estimated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_llm_calls_created", "created_at"),
        Index("idx_llm_calls_user_created", "user_id", "created_at"),
    )


def start_of_day(now: Optional[datetime] = None) -> datetime:
    """Budgets reset at 00:00 UTC."""
    now = now or datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def spent_since(session, since: datetime, user_id: Optional[str] = None) -> float:
    q = session.query(func.coalesce(func.sum(LLMCall.cost_usd), 0.0)).filter(LLMCall.created_at >= since)
    if user_id is not None:
        q = q.filter(LLMCall.user_id == user_id)
    return float(q.scalar())


class DbUsageGuard:
    """Daily budgets (USD, <= 0 = unlimited): all users together, each user, and a
    ceiling for bulk tasks so background extraction can't starve interactive use."""

    def __init__(self, daily_usd: float, user_daily_usd: float, bulk_share: float) -> None:
        self.daily_usd = daily_usd
        self.user_daily_usd = user_daily_usd
        self.bulk_share = bulk_share

    def check(self, task: str, tier: str, user_id: Optional[str]) -> None:
        if self.daily_usd <= 0 and (self.user_daily_usd <= 0 or user_id is None):
            return
        from careeros.db.connection import db

        since = start_of_day()
        with db.session_scope() as s:
            if self.daily_usd > 0:
                spent = spent_since(s, since)
                limit = self.daily_usd * (self.bulk_share if tier == "bulk" else 1.0)
                if spent >= limit:
                    raise LLMBudgetExceeded(
                        f"Daily LLM budget reached for {tier} tasks (${spent:.4f} of ${limit:.4f}); resets 00:00 UTC"
                    )
            if user_id is not None and self.user_daily_usd > 0:
                mine = spent_since(s, since, user_id)
                if mine >= self.user_daily_usd:
                    raise LLMBudgetExceeded(
                        f"Your daily LLM budget is used up (${mine:.4f} of ${self.user_daily_usd:.4f}); resets 00:00 UTC"
                    )

    def record(self, call: CallRecord) -> None:
        from careeros.db.connection import db

        with db.session_scope() as s:
            s.add(LLMCall(
                task=call.task[:32], model=call.model[:128], user_id=call.user_id, status=call.status,
                prompt_tokens=call.prompt_tokens, completion_tokens=call.completion_tokens,
                cost_usd=call.cost_usd, cost_estimated=call.cost_estimated,
                latency_ms=call.latency_ms, error=call.error,
            ))


def usage_report(session, days: int = 7) -> list[dict]:
    """Per day and task: calls, failures, refusals, tokens, cost — newest first."""
    since = start_of_day() - timedelta(days=days - 1)
    day = func.date_trunc("day", LLMCall.created_at)
    rows = (
        session.query(
            day.label("day"), LLMCall.task,
            func.count().label("calls"),
            func.count().filter(LLMCall.status == "error").label("errors"),
            func.count().filter(LLMCall.status == "budget").label("refused"),
            func.sum(LLMCall.prompt_tokens + LLMCall.completion_tokens).label("tokens"),
            func.sum(LLMCall.cost_usd).label("cost"),
        )
        .filter(LLMCall.created_at >= since)
        .group_by(day, LLMCall.task)
        .order_by(day.desc(), LLMCall.task)
        .all()
    )
    return [
        {"day": r.day.date().isoformat(), "task": r.task, "calls": r.calls, "errors": r.errors,
         "refused": r.refused, "tokens": int(r.tokens or 0), "cost_usd": round(float(r.cost or 0), 4)}
        for r in rows
    ]


def budget_status(session, user_id: Optional[str] = None) -> dict:
    """Today's spend against the configured budgets (USD)."""
    from careeros.shared.config import get_settings

    settings, since = get_settings(), start_of_day()
    out = {
        "resets_at": (since + timedelta(days=1)).isoformat(),
        "spent_today_usd": round(spent_since(session, since), 4),
        "daily_budget_usd": settings.llm_daily_budget_usd if settings.llm_daily_budget_usd > 0 else None,
        "bulk_share": settings.llm_bulk_budget_share,
        "user_daily_budget_usd": settings.llm_user_daily_budget_usd if settings.llm_user_daily_budget_usd > 0 else None,
    }
    if user_id is not None:
        out["your_spent_today_usd"] = round(spent_since(session, since, user_id), 4)
    return out
