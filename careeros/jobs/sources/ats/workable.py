"""Workable public job widget: one request with details (used by many EU scale-ups).

apply.workable.com/<account>  ->  /api/v1/widget/accounts/<account>?details=true
"""

from careeros.jobs.sources.ats.base import TIMEOUT, Board, FetchResult, Posting, html_to_text, parse_time


def fetch(board: Board, http, known_urls: set[str], keep_title=None) -> FetchResult:
    resp = http.get(f"https://apply.workable.com/api/v1/widget/accounts/{board.board}?details=true", timeout=TIMEOUT)
    resp.raise_for_status()
    # The same job is listed once per location: merge them into one posting
    merged: dict[str, Posting] = {}
    for j in resp.json().get("jobs", []):
        if not j.get("shortcode"):
            continue
        p = _posting(j)
        if p.external_id in merged:
            first = merged[p.external_id]
            places = [x for x in dict.fromkeys(first.location.split(" • ") + p.location.split(" • ")) if x]
            first.location = " • ".join(places)
        else:
            merged[p.external_id] = p
    return FetchResult(postings=list(merged.values()))


def _location(j: dict) -> str:
    out = []
    for loc in j.get("locations") or [{"city": j.get("city"), "country": j.get("country")}]:
        if isinstance(loc, dict):
            out.append(", ".join(x for x in (loc.get("city"), loc.get("country")) if x))
    return " • ".join(dict.fromkeys(x for x in out if x))


def _posting(j: dict) -> Posting:
    url = j.get("url") or f"https://apply.workable.com/j/{j['shortcode']}"
    return Posting(
        external_id=j["shortcode"],
        url=url,
        apply_url=j.get("application_url") or url,
        title=(j.get("title") or "").strip(),
        location=_location(j),
        description=html_to_text(j.get("description")),
        department=j.get("department") or None,
        employment_type=j.get("employment_type") or None,
        posted_at=parse_time(j.get("published_on") or j.get("created_at")),
        remote=True if j.get("telecommuting") else None,
    )
