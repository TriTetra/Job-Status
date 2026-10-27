"""Shared types for company career-board clients (Greenhouse, Lever, Ashby, Workday)."""

import html
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENT = "CareerOS/1.0 (private job search; reads public job boards)"
TIMEOUT = (10, 60)  # connect, read — big boards return several MB


@dataclass(frozen=True)
class Board:
    """One company's public job board, from infra/config/companies.yaml."""

    key: str                       # stable id, e.g. "stripe"
    name: str                      # display name, e.g. "Stripe"
    ats: str                       # greenhouse | lever | ashby | workday
    board: str = ""                # board token / slug (greenhouse, lever, ashby)
    host: str = ""                 # workday: nvidia.wd5.myworkdayjobs.com
    tenant: str = ""               # workday: nvidia
    site: str = ""                 # workday: NVIDIAExternalCareerSite
    search: tuple[str, ...] = ()   # workday: server-side search terms (empty = everything)


@dataclass
class Posting:
    """A job as the company publishes it, before CareerOS adds anything."""

    external_id: str
    url: str                       # public posting page on the company's board
    title: str
    location: str = ""
    description: str = ""          # plain text
    apply_url: Optional[str] = None
    department: Optional[str] = None
    employment_type: Optional[str] = None
    posted_at: Optional[datetime] = None
    remote: Optional[bool] = None  # None = the board doesn't say; text decides
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None


@dataclass
class FetchResult:
    postings: list[Posting] = field(default_factory=list)
    # False when the board was only partly read (page cap, detail cap): unseen
    # postings must not be treated as closed
    complete: bool = True
    # Workday lists without descriptions; these postings exist but weren't fetched in detail
    seen_urls: set[str] = field(default_factory=set)


# fetch(board, http, known_urls, keep_title) — known_urls are already stored and
# keep_title is the title filter; both only let Workday skip detail requests
Fetcher = Callable[[Board, "requests.Session", set[str], Optional[Callable[[str], bool]]], FetchResult]


def http_session() -> requests.Session:
    retry = Retry(total=3, backoff_factor=1.5, status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=("GET", "POST"), respect_retry_after_header=True)
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s


_BLANK_LINES = re.compile(r"\n\s*\n+")


def html_to_text(markup: Optional[str], escaped: bool = False) -> str:
    if not markup:
        return ""
    if escaped:  # Greenhouse double-encodes: &lt;p&gt;
        markup = html.unescape(markup)
    text = BeautifulSoup(markup, "html.parser").get_text("\n")
    return _BLANK_LINES.sub("\n\n", text.replace("\xa0", " ")).strip()


def parse_time(value) -> Optional[datetime]:
    """ISO-8601 string or epoch milliseconds → aware datetime."""
    if value in (None, ""):
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, OverflowError, OSError):
        return None
