"""SmartRecruiters public postings API. The list has no descriptions, so (like Workday)
only new postings with a relevant title are read in detail, a capped number per run.
Optional country filter: `search: [tr]` in companies.yaml.

https://developers.smartrecruiters.com/docs/posting-api
"""

from careeros.jobs.sources.ats.base import TIMEOUT, Board, FetchResult, Posting, html_to_text, parse_time

API = "https://api.smartrecruiters.com/v1/companies/{company}/postings"
PAGE = 100
MAX_PAGES = 10
MAX_DETAILS = 60  # detail requests per board per run


def public_url(company: str, posting_id: str) -> str:
    return f"https://jobs.smartrecruiters.com/{company}/{posting_id}"


def fetch(board: Board, http, known_urls: set[str], keep_title=None) -> FetchResult:
    """`search` in companies.yaml lists country codes (["tr"]): only that country's postings are read,
    so a large employer can be followed in one country (the API's own `country` filter)."""
    listed, complete, ids = [], True, set()
    for country in board.search or (None,):
        got = 0
        for page in range(MAX_PAGES):
            params = {"limit": PAGE, "offset": page * PAGE}
            if country:
                params["country"] = country.lower()
            resp = http.get(API.format(company=board.board), params=params, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            content = data.get("content") or []
            got += len(content)
            listed += [c for c in content if c.get("id") not in ids]
            ids.update(c.get("id") for c in content)
            if not content or got >= int(data.get("totalFound") or 0):
                break
        else:
            complete = False

    seen, postings, details = set(), [], 0
    for item in listed:
        url = public_url(board.board, str(item["id"]))
        seen.add(url)
        if url in known_urls or (keep_title and not keep_title(item.get("name") or "")):
            continue
        if details >= MAX_DETAILS:
            complete = False
            continue
        details += 1
        detail = http.get(item.get("ref") or f"{API.format(company=board.board)}/{item['id']}", timeout=TIMEOUT)
        detail.raise_for_status()
        postings.append(_posting(board, detail.json()))
    return FetchResult(postings=postings, complete=complete, seen_urls=seen)


def _posting(board: Board, d: dict) -> Posting:
    loc = d.get("location") or {}
    sections = (d.get("jobAd") or {}).get("sections") or {}
    parts = [f"{s.get('title', '')}\n{html_to_text(s.get('text'))}".strip()
             for s in sections.values() if isinstance(s, dict) and s.get("text")]
    url = public_url(board.board, str(d["id"]))
    return Posting(
        external_id=str(d["id"]),
        url=url,
        apply_url=d.get("applyUrl") or url,
        title=(d.get("name") or "").strip(),
        location=", ".join(x for x in (loc.get("city"), (loc.get("country") or "").upper()) if x),
        description="\n\n".join(parts),
        department=(d.get("department") or {}).get("label"),
        employment_type=(d.get("typeOfEmployment") or {}).get("label"),
        posted_at=parse_time(d.get("releasedDate")),
        remote=True if loc.get("remote") else None,
    )
