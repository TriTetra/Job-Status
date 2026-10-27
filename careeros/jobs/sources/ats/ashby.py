"""Ashby job board API — one request, descriptions and compensation included.

https://developers.ashbyhq.com/docs/public-job-posting-api
"""

from careeros.jobs.sources.ats.base import TIMEOUT, Board, FetchResult, Posting, parse_time

API = "https://api.ashbyhq.com/posting-api/job-board/{board}?includeCompensation=true"


def fetch(board: Board, http, known_urls: set[str], keep_title=None) -> FetchResult:
    resp = http.get(API.format(board=board.board), timeout=TIMEOUT)
    resp.raise_for_status()
    jobs = [j for j in resp.json().get("jobs", []) if j.get("isListed", True)]
    return FetchResult(postings=[_posting(j) for j in jobs])


def _salary(job: dict) -> tuple:
    for part in (job.get("compensation") or {}).get("summaryComponents") or []:
        if part.get("compensationType") == "Salary" and part.get("interval", "1 YEAR") == "1 YEAR":
            return part.get("minValue"), part.get("maxValue"), part.get("currencyCode")
    return None, None, None


def _posting(job: dict) -> Posting:
    low, high, currency = _salary(job)
    locations = [job.get("location") or ""] + [
        s.get("location", "") for s in job.get("secondaryLocations") or [] if isinstance(s, dict)
    ]
    return Posting(
        external_id=job["id"],
        url=job["jobUrl"],
        apply_url=job.get("applyUrl") or job["jobUrl"],
        title=(job.get("title") or "").strip(),
        location=" • ".join(loc for loc in locations if loc),
        description=(job.get("descriptionPlain") or "").strip(),
        department=job.get("team") or job.get("department"),
        employment_type=job.get("employmentType"),
        posted_at=parse_time(job.get("publishedAt")),
        remote=job.get("isRemote"),
        salary_min=int(low) if low else None,
        salary_max=int(high) if high else None,
        salary_currency=currency,
    )
