"""Company logos for the board companies, fetched once and kept in memory.

Only companies in infra/config/companies.yaml (known domains) can be asked for, so
this is not an open proxy. The image comes from Google's favicon service at
128 px; anything that isn't a real icon (unknown domain, error) is "no logo" and
the web shows a monogram instead.
"""

import logging
import threading
import time
from typing import Optional

import requests

from careeros.jobs.boards import load_boards

logger = logging.getLogger(__name__)

SOURCE = "https://www.google.com/s2/favicons"
SIZE = 128
MAX_BYTES = 200_000
MISS_TTL = 6 * 3600  # retry a failed logo after a while

_cache: dict[str, tuple[Optional[bytes], str, float]] = {}
_lock = threading.Lock()


def domain_for(key: str) -> Optional[str]:
    board = next((b for b in load_boards().boards if b.key == key), None)
    return board.domain if board and board.domain else None


def logo(key: str, http=requests) -> Optional[tuple[bytes, str]]:
    """(image bytes, content type) for a board company, or None."""
    with _lock:
        hit = _cache.get(key)
    if hit and (hit[0] is not None or time.monotonic() - hit[2] < MISS_TTL):
        return (hit[0], hit[1]) if hit[0] is not None else None

    domain = domain_for(key)
    data, ctype = None, ""
    if domain:
        try:
            resp = http.get(SOURCE, params={"domain": domain, "sz": SIZE}, timeout=8)
            ctype = resp.headers.get("content-type", "")
            if resp.status_code == 200 and ctype.startswith("image/") and 0 < len(resp.content) <= MAX_BYTES:
                data = resp.content
        except requests.RequestException as e:
            logger.info("Logo fetch failed for %s: %s", key, e)
    with _lock:
        _cache[key] = (data, ctype, time.monotonic())
    return (data, ctype) if data else None
