"""Greenhouse job board API — one request returns every posting with its description.

https://developers.greenhouse.io/job-board.html
"""

from careeros.jobs.sources.ats.base import TIMEOUT, Board, FetchResult, Posting, html_to_text, parse_time

API = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"


def fetch(board: Board, http, known_urls: set[str], keep_title=None) -> FetchResult:
    resp = http.get(API.format(board=board.board), timeout=TIMEOUT)
    resp.raise_for_status()
    return FetchResult(postings=[_posting(j) for j in resp.json().get("jobs", [])])


def _posting(job: dict) -> Posting:
    departments = job.get("departments") or []
    return Posting(
        external_id=str(job["id"]),
        url=job["absolute_url"],
        apply_url=job["absolute_url"],
        title=(job.get("title") or "").strip(),
        location=((job.get("location") or {}).get("name") or "").strip(),
        description=html_to_text(job.get("content"), escaped=True),
        department=departments[0]["name"] if departments else None,
        posted_at=parse_time(job.get("first_published") or job.get("updated_at")),
    )
