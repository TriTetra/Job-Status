"""Company career boards by ATS. Each module exposes `fetch(board, http, known_urls) -> FetchResult`."""

from careeros.jobs.sources.ats import (
    ashby, eightfold, greenhouse, lever, personio, recruitee, smartrecruiters, workable, workday,
)
from careeros.jobs.sources.ats.base import Board, FetchResult, Fetcher, Posting, http_session

FETCHERS: dict[str, Fetcher] = {
    "greenhouse": greenhouse.fetch,
    "lever": lever.fetch,
    "ashby": ashby.fetch,
    "workday": workday.fetch,
    "personio": personio.fetch,
    "recruitee": recruitee.fetch,
    "workable": workable.fetch,
    "smartrecruiters": smartrecruiters.fetch,
    "eightfold": eightfold.fetch,
}

__all__ = ["FETCHERS", "Board", "FetchResult", "Posting", "http_session"]
