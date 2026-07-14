"""Extract funding/layoff signals from TechCrunch articles."""

import re
from datetime import datetime
from typing import Dict, List, Optional

from packages.db.connection import db
from packages.db.repositories import MarketSignalRepository

from .rss_client import TechCrunchClient

_FUNDING_RE = re.compile(
    r'raises?\s+\$?([\d,.]+)\s*(million|billion|[MB])\b', re.IGNORECASE
)
_LAYOFF_RE = re.compile(
    r'(?:lays?\s+off|cuts?\s+)([\d,]+)\s*(?:workers?|employees?|jobs?|people)?',
    re.IGNORECASE,
)
_SERIES_RE = re.compile(r'series\s+([A-Z])', re.IGNORECASE)


class TechCrunchSignalExtractor:
    def __init__(self):
        self.client = TechCrunchClient()

    def extract_signals(self, hours: int = 168) -> int:
        articles = self.client.get_recent_articles("main", hours=hours)
        print(f"  TechCrunch articles: {len(articles)}")

        signals_created = 0
        with db.session_scope() as session:
            repo = MarketSignalRepository(session)

            for article in articles:
                signal = self._analyze(article)
                if not signal:
                    continue
                try:
                    repo.add_signal(**signal)
                    signals_created += 1
                except Exception:
                    pass  # duplicate source_id → skip

        print(f"  Signals created: {signals_created}")
        return signals_created

    def _analyze(self, article: Dict) -> Optional[Dict]:
        title = article.get("title", "")
        summary = article.get("summary", "") or ""
        text = f"{title} {summary}"
        url = article.get("url", "")
        slug = url.rstrip("/").split("/")[-1][:80]
        occurred_at = article.get("published") or datetime.utcnow()

        # Funding
        m = _FUNDING_RE.search(text)
        if m:
            amount_str = m.group(1).replace(",", "")
            try:
                amount = float(amount_str)
                unit = m.group(2).lower()
                if unit in ("billion", "b"):
                    amount *= 1000
            except ValueError:
                amount = 0.0

            series = _SERIES_RE.search(text)
            round_type = f"series_{series.group(1).lower()}" if series else "unknown"

            return dict(
                signal_type="funding",
                source="techcrunch",
                title=title[:500],
                summary=summary[:500],
                url=url,
                occurred_at=occurred_at,
                source_id=f"tc_funding_{slug}",
                impact="high" if amount >= 50 else "medium",
                magnitude=amount,
                metadata_json={"amount_millions": amount, "round_type": round_type},
            )

        # Layoff
        m = _LAYOFF_RE.search(text)
        if m:
            count_str = m.group(1).replace(",", "")
            try:
                count = int(count_str)
            except ValueError:
                count = 0

            return dict(
                signal_type="layoff",
                source="techcrunch",
                title=title[:500],
                summary=summary[:500],
                url=url,
                occurred_at=occurred_at,
                source_id=f"tc_layoff_{slug}",
                impact="high" if count >= 100 else "medium",
                magnitude=float(count),
                metadata_json={"layoff_count": count},
            )

        return None
