"""Skill registry — hybrid Layer-1 match + Layer-2 learning (promote)."""

from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Dict, List, Optional

import sqlalchemy as sa

from core.db.models.market_skill import MarketSkill

SIMILARITY_THRESHOLD = 0.85


def _fuzzy_lookup(
    rows: Dict[str, MarketSkill], key: str
) -> Optional[MarketSkill]:
    best, best_score = None, 0.0
    for k, row in rows.items():
        score = SequenceMatcher(None, k, key).ratio()
        if score > best_score:
            best_score, best = score, row
    return best if best_score >= SIMILARITY_THRESHOLD else None


def record_mentions(
    session,
    raw_names: List[str],
    source: str = "llm_discovered",
) -> List[str]:
    """
    Upsert mention counts for each skill name:
    - Known skills (exact or fuzzy match) → increment count
    - Unknown skills → insert (promote to registry)

    Returns canonical names for signal aggregation.
    """
    rows: Dict[str, MarketSkill] = {
        r.name.lower(): r
        for r in session.execute(sa.select(MarketSkill)).scalars().all()
    }
    canonical: List[str] = []
    now = datetime.now(timezone.utc)

    for raw in dict.fromkeys(raw_names):  # dedupe, order-preserving
        name = (raw or "").strip()
        if not name or len(name) < 2:
            continue
        key = name.lower()

        row = rows.get(key) or _fuzzy_lookup(rows, key)
        if row is not None:
            row.mention_count += 1
            row.last_seen_at = now
            canonical.append(row.name)
        else:
            new = MarketSkill(
                name=name,
                source=source,
                mention_count=1,
                first_seen_at=now,
                last_seen_at=now,
            )
            session.add(new)
            rows[key] = new
            canonical.append(name)

    session.flush()
    return canonical
