"""Lever postings API — one request, descriptions included.

https://github.com/lever/postings-api
"""

from careeros.jobs.sources.ats.base import TIMEOUT, Board, FetchResult, Posting, html_to_text, parse_time

API = "https://api.lever.co/v0/postings/{board}?mode=json"


def fetch(board: Board, http, known_urls: set[str], keep_title=None) -> FetchResult:
    resp = http.get(API.format(board=board.board), timeout=TIMEOUT)
    resp.raise_for_status()
    return FetchResult(postings=[_posting(j) for j in resp.json()])


def _description(job: dict) -> str:
    parts = [job.get("descriptionPlain") or ""]
    for section in job.get("lists") or []:
        parts.append(f"{section.get('text', '')}:\n{html_to_text(section.get('content'))}")
    parts.append(job.get("additionalPlain") or "")
    return "\n\n".join(p.strip() for p in parts if p and p.strip())


def _posting(job: dict) -> Posting:
    categories = job.get("categories") or {}
    salary = job.get("salaryRange") or {}
    workplace = (job.get("workplaceType") or "").lower()
    return Posting(
        external_id=job["id"],
        url=job["hostedUrl"],
        apply_url=job.get("applyUrl") or job["hostedUrl"],
        title=(job.get("text") or "").strip(),
        location=(categories.get("location") or "").strip(),
        description=_description(job),
        department=categories.get("team") or categories.get("department"),
        employment_type=categories.get("commitment"),
        posted_at=parse_time(job.get("createdAt")),
        remote=True if workplace == "remote" else (False if workplace in ("onsite", "on-site") else None),
        salary_min=salary.get("min"),
        salary_max=salary.get("max"),
        salary_currency=salary.get("currency"),
    )
