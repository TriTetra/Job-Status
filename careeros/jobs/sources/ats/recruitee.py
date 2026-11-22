"""Recruitee careers API: one request, descriptions included (common with Dutch and EU startups).

https://docs.recruitee.com/reference/offers
"""

from careeros.jobs.sources.ats.base import TIMEOUT, Board, FetchResult, Posting, html_to_text, parse_time


def fetch(board: Board, http, known_urls: set[str], keep_title=None) -> FetchResult:
    resp = http.get(f"https://{board.board}.recruitee.com/api/offers/", timeout=TIMEOUT)
    resp.raise_for_status()
    offers = [o for o in resp.json().get("offers", []) if o.get("status", "published") == "published"]
    return FetchResult(postings=[_posting(o) for o in offers])


def _location(o: dict) -> str:
    names = [loc.get("name", "") for loc in o.get("locations") or [] if isinstance(loc, dict)]
    return " • ".join(n for n in names if n) or (o.get("location") or "")


def _int(v):
    try:
        return int(float(v)) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _posting(o: dict) -> Posting:
    salary = o.get("salary") or {}
    remote = True if o.get("remote") else (False if o.get("on_site") and not o.get("hybrid") else None)
    yearly = (salary.get("period") or "").lower() in ("", "year", "yearly", "annual")
    published = (o.get("published_at") or o.get("created_at") or "").replace(" UTC", "+00:00")
    text = [html_to_text(o.get("description")), html_to_text(o.get("requirements"))]
    return Posting(
        external_id=str(o["id"]),
        url=o["careers_url"],
        apply_url=o.get("careers_apply_url") or o["careers_url"],
        title=(o.get("title") or "").strip(),
        location=_location(o),
        description="\n\n".join(t for t in text if t),
        department=o.get("department"),
        employment_type=o.get("employment_type_code"),
        posted_at=parse_time(published),
        remote=remote,
        salary_min=_int(salary.get("min")) if yearly else None,
        salary_max=_int(salary.get("max")) if yearly else None,
        salary_currency=salary.get("currency") if yearly else None,
    )
