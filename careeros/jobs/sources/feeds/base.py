"""Shared types for job feeds: sites that list many companies' jobs (Hacker News, Arbeitnow,
Remotive, Himalayas, Jobicy).

Feed postings keep the feed's own page as the link: each feed's terms ask for a link back
and a credit, and that the apply button go to the job URL it gives.
"""

import html
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

import requests

from careeros.jobs.discovery import links


@dataclass
class FeedPosting:
    source: str                      # feed key, e.g. "hackernews"
    external_id: str
    url: str                         # the posting on the feed (link back)
    title: str
    company: str
    location: str = ""               # where it is, or who may apply ("Europe", "Germany, Poland")
    description: str = ""            # plain text
    apply_url: Optional[str] = None
    posted_at: Optional[datetime] = None
    remote: Optional[bool] = None
    employment_type: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None
    links: list[str] = field(default_factory=list)   # every link in the posting (board discovery)


FeedFetcher = Callable[["requests.Session"], list[FeedPosting]]


def html_links(markup: Optional[str]) -> list[str]:
    """Links in feed HTML (hrefs and bare URLs), entities decoded."""
    return links(html.unescape(markup or ""))


def epoch(seconds) -> Optional[datetime]:
    try:
        return datetime.fromtimestamp(int(seconds), tz=timezone.utc) if seconds not in (None, "") else None
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def yearly(low, high, currency, period) -> tuple[Optional[int], Optional[int], Optional[str]]:
    """Keep a salary only when it is stated per year."""
    if (period or "").lower() not in ("", "year", "yearly", "annual", "annually"):
        return None, None, None

    def num(v):
        try:
            return int(float(v)) if v not in (None, "", 0) else None
        except (TypeError, ValueError):
            return None
    lo, hi = num(low), num(high)
    return lo, hi, (currency or None) if (lo or hi) else None
