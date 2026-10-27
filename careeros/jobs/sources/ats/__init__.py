"""Company career boards by ATS. Each module exposes `fetch(board, http, known_urls) -> FetchResult`."""

from careeros.jobs.sources.ats import ashby, greenhouse, lever, workday
from careeros.jobs.sources.ats.base import Board, FetchResult, Fetcher, Posting, http_session

FETCHERS: dict[str, Fetcher] = {
    "greenhouse": greenhouse.fetch,
    "lever": lever.fetch,
    "ashby": ashby.fetch,
    "workday": workday.fetch,
}

__all__ = ["FETCHERS", "Board", "FetchResult", "Posting", "http_session"]
