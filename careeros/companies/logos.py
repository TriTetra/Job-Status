"""Company logos, fetched once and kept in memory.

Only companies CareerOS already knows can be asked for, so this is not an open proxy:
  - a board company (companies.yaml or discovered) by its key → its website's icon;
  - any stored job by its URL → the board's logo, else the employer website found in
    the posting, else the logo image the job feed provides (only from the feeds' own
    image hosts).
Website icons come from Google's favicon service at 128 px; anything that isn't a real
image is "no logo" and the web shows a monogram instead.
"""

import logging
import threading
import time
from collections import Counter
from typing import Callable, Optional
from urllib.parse import urlparse

import requests

from careeros.jobs.boards import all_boards

logger = logging.getLogger(__name__)

SOURCE = "https://www.google.com/s2/favicons"
SIZE = 128
MAX_BYTES = 200_000
MISS_TTL = 6 * 3600  # retry a failed logo after a while
# Image hosts of the job feeds that hand out company logos
FEED_LOGO_HOSTS = ("cdn-images.himalayas.app", "himalayas.app", "jobicy.com", "remotive.com", "remotive.io")

_cache: dict[str, tuple[Optional[bytes], str, float]] = {}
_lock = threading.Lock()


def _cached(cache_key: str, fetch: Callable[[], tuple[Optional[bytes], str]]) -> Optional[tuple[bytes, str]]:
    with _lock:
        hit = _cache.get(cache_key)
    if hit and (hit[0] is not None or time.monotonic() - hit[2] < MISS_TTL):
        return (hit[0], hit[1]) if hit[0] is not None else None
    data, ctype = fetch()
    with _lock:
        _cache[cache_key] = (data, ctype, time.monotonic())
    return (data, ctype) if data else None


def _get_image(http, url: str, params: Optional[dict] = None) -> tuple[Optional[bytes], str]:
    try:
        resp = http.get(url, params=params, timeout=8)
        ctype = resp.headers.get("content-type", "")
        if resp.status_code == 200 and ctype.startswith("image/") and 0 < len(resp.content) <= MAX_BYTES:
            return resp.content, ctype
    except requests.RequestException as e:
        logger.info("Logo fetch failed for %s: %s", urlparse(url).hostname, e)
    return None, ""


def _favicon(domain: str, http=requests) -> Optional[tuple[bytes, str]]:
    return _cached(f"d:{domain}", lambda: _get_image(http, SOURCE, {"domain": domain, "sz": SIZE}))


def logo_for_domain(domain: str, http=requests) -> Optional[tuple[bytes, str]]:
    """An employer directory entry's logo: only domains listed in a directory (never any domain asked for)."""
    from careeros.companies.employers import domains

    d = (domain or "").strip().lower().removeprefix("www.")
    if d not in domains("tr"):
        return None
    return _favicon(d, http)


def domain_for(key: str, session=None) -> Optional[str]:
    """A board company's website: from its config, else the one its postings point to most."""
    board = next((b for b in all_boards(session) if b.key == key), None)
    if board is None:
        return None
    if board.domain:
        return board.domain
    if session is None:
        return None
    from careeros.jobs.models.job import Job

    found = Counter(d for (d,) in session.query(Job.company_domain)
                    .filter(Job.company_key == key, Job.company_domain.isnot(None)).limit(200).all() if d)
    return found.most_common(1)[0][0] if found else None


def logo(key: str, http=requests, session=None) -> Optional[tuple[bytes, str]]:
    """(image bytes, content type) for a board company, or None."""
    domain = domain_for(key, session)
    return _favicon(domain, http) if domain else None


def logo_for_job(session, url: str, http=requests) -> Optional[tuple[bytes, str]]:
    """The logo of the company behind a stored job (board → website → feed logo)."""
    from careeros.jobs.models.job import Job

    job = session.get(Job, url)
    if job is None:
        return None
    if job.company_key:
        found = logo(job.company_key, http, session)
        if found:
            return found
    if job.company_domain:
        found = _favicon(job.company_domain, http)
        if found:
            return found
    host = (urlparse(job.company_logo or "").hostname or "").lower()
    if job.company_logo and job.company_logo.startswith("https://") and host in FEED_LOGO_HOSTS:
        return _cached(f"u:{job.company_logo}", lambda: _get_image(http, job.company_logo))
    return None
