"""Extract funding/layoff/hiring signals from TechCrunch articles."""

import logging
import re
from datetime import datetime
from typing import Dict, Optional

from core.db.connection import db
from core.db.repositories import MarketSignalRepository

from .rss_client import TechCrunchClient

logger = logging.getLogger(__name__)

# ── Funding patterns ──────────────────────────────────────────────────────────
# Covers: raises / secures / closes / lands / bags / gets / nets + $50M / $1.2B
_FUNDING_AMOUNT_RE = re.compile(
    r'\$\s*([\d,.]+)\s*(million|billion|[MB])\b',
    re.IGNORECASE,
)
# Alternative: "50 million", "1.2 billion" without $
_FUNDING_WORD_RE = re.compile(
    r'\b([\d,.]+)\s*[-\s]?(million|billion)\s+(?:dollar|usd|funding|investment|round)',
    re.IGNORECASE,
)
_SERIES_RE = re.compile(r'\bseries\s+([A-F])\b', re.IGNORECASE)
_ROUND_RE = re.compile(r'\b(seed|pre[-\s]?seed|series\s+[A-F]|growth|late[-\s]stage|ipo)\b', re.IGNORECASE)

_FUNDING_VERBS = re.compile(
    r'\b(raises?|secures?|closes?|lands?|bags?|nets?|gets?|receives?|announces?|completes?)\s+'
    r'(?:a\s+|an\s+)?(?:[\$\d]|[\d,.]+\s*[-\s]?million)',
    re.IGNORECASE,
)

# ── Layoff patterns ───────────────────────────────────────────────────────────
_LAYOFF_COUNT_RE = re.compile(
    r'\b(lays?\s+off|cutting|cut|eliminat(?:es?|ing)|reduc(?:es?|ing)|let(?:s?\s+go|ting\s+go)'
    r'|terminat(?:es?|ing)|slash(?:es?|ing))\s+'
    r'(?:about\s+|around\s+|approximately\s+|nearly\s+|more\s+than\s+|over\s+)?'
    r'([\d,]+)\s*(?:%|percent|workers?|employees?|jobs?|roles?|people|staff)?',
    re.IGNORECASE,
)
_LAYOFF_PCT_RE = re.compile(
    r'\b(\d+)\s*%\s*(?:of\s+(?:its\s+|the\s+)?(?:global\s+)?(?:work\s*force|staff|employees?|team))',
    re.IGNORECASE,
)
_LAYOFF_KEYWORDS = re.compile(
    r'\b(layoffs?|mass\s+layoffs?|workforce\s+reduction|job\s+cuts?|downsiz)\b',
    re.IGNORECASE,
)

# ── Acquisition patterns ──────────────────────────────────────────────────────
_ACQUIRE_RE = re.compile(
    r'\b(acquires?|acqui[-\s]?hires?|buys?|merges?\s+with|acquired\s+by)\b',
    re.IGNORECASE,
)

# ── Company extraction ────────────────────────────────────────────────────────
_COMPANY_FROM_TITLE = re.compile(r'^([A-Z][A-Za-z0-9\s\-\.\'&]+?)\s+(?:raises?|secures?|closes?|lays?\s+off|acquires?)', )


def _extract_amount(text: str) -> float:
    """Return funding amount in millions, 0 if not found."""
    m = _FUNDING_AMOUNT_RE.search(text)
    if not m:
        m = _FUNDING_WORD_RE.search(text)
    if not m:
        return 0.0
    try:
        amount = float(m.group(1).replace(",", ""))
        unit = m.group(2).lower()
        if unit in ("billion", "b"):
            amount *= 1000
        return amount
    except (ValueError, IndexError):
        return 0.0


def _extract_company(title: str) -> Optional[str]:
    m = _COMPANY_FROM_TITLE.match(title)
    return m.group(1).strip()[:100] if m else None


class TechCrunchSignalExtractor:
    def __init__(self):
        self.client = TechCrunchClient()

    def extract_signals(self, hours: int = 168) -> int:
        """Scan multiple TC feeds and extract funding/layoff/acquisition signals."""
        signals_created = 0

        feeds_to_scan = ["main", "startups", "ai"]
        seen_slugs: set = set()

        with db.session_scope() as session:
            repo = MarketSignalRepository(session)

            for feed_name in feeds_to_scan:
                articles = self.client.get_recent_articles(feed_name, hours=hours)
                logger.info("[%s] %d articles", feed_name, len(articles))

                for article in articles:
                    url = article.get("url", "")
                    slug = url.rstrip("/").split("/")[-1][:80]
                    if slug in seen_slugs:
                        continue
                    seen_slugs.add(slug)

                    signal = self._analyze(article, slug)
                    if not signal:
                        continue
                    try:
                        repo.add_signal(**signal)
                        signals_created += 1
                    except Exception:
                        pass  # duplicate source_id → skip

        logger.info("TechCrunch signals created: %d", signals_created)
        return signals_created

    def _analyze(self, article: Dict, slug: str) -> Optional[Dict]:
        title = article.get("title", "")
        summary = (article.get("summary") or "")
        # Strip HTML from summary
        summary_clean = re.sub(r"<[^>]+>", " ", summary)
        text = f"{title} {summary_clean}"
        url = article.get("url", "")
        occurred_at = article.get("published") or datetime.utcnow()
        company = _extract_company(title)
        companies = [company] if company else []

        # ── Funding ──────────────────────────────────────────────────────
        has_funding_verb = bool(_FUNDING_VERBS.search(text))
        amount = _extract_amount(text)

        if has_funding_verb or (amount > 0):
            if amount == 0:
                # verb present but no amount — still a funding signal
                amount = 0.0

            series_m = _SERIES_RE.search(text)
            round_m = _ROUND_RE.search(text)
            round_type = (
                series_m.group(0).lower().replace(" ", "_")
                if series_m
                else (round_m.group(0).lower().replace(" ", "_") if round_m else "unknown")
            )

            amount_label = f"${amount:.0f}M " if amount else ""
            return dict(
                signal_type="funding",
                source="techcrunch",
                title=title[:500],
                summary=summary_clean[:500],
                url=url,
                occurred_at=occurred_at,
                source_id=f"tc_funding_{slug}",
                impact="high" if amount >= 50 else "medium",
                companies_affected=companies,
                magnitude=amount,
                metadata_json={
                    "amount_millions": amount,
                    "round_type": round_type,
                    "amount_label": amount_label,
                },
            )

        # ── Layoff ────────────────────────────────────────────────────────
        is_layoff = bool(
            _LAYOFF_COUNT_RE.search(text)
            or _LAYOFF_PCT_RE.search(text)
            or _LAYOFF_KEYWORDS.search(text)
        )

        if is_layoff:
            count = 0
            m = _LAYOFF_COUNT_RE.search(text)
            if m:
                try:
                    count = int(m.group(2).replace(",", ""))
                except (ValueError, IndexError):
                    pass

            return dict(
                signal_type="layoff",
                source="techcrunch",
                title=title[:500],
                summary=summary_clean[:500],
                url=url,
                occurred_at=occurred_at,
                source_id=f"tc_layoff_{slug}",
                impact="high" if count >= 100 else "medium",
                companies_affected=companies,
                magnitude=float(count),
                metadata_json={"layoff_count": count},
            )

        # ── Acquisition ───────────────────────────────────────────────────
        if _ACQUIRE_RE.search(text):
            return dict(
                signal_type="acquisition",
                source="techcrunch",
                title=title[:500],
                summary=summary_clean[:500],
                url=url,
                occurred_at=occurred_at,
                source_id=f"tc_acq_{slug}",
                impact="medium",
                companies_affected=companies,
                magnitude=0.0,
                metadata_json={},
            )

        return None
