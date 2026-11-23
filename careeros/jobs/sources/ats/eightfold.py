"""Eightfold career sites (used by large employers, e.g. Vodafone): the public search the
career site itself calls, which the site's robots.txt allows (/api/pcsx).

The list has no descriptions, so (like Workday) only new postings with a relevant
title are read in detail, a capped number per run. A board can be limited to
locations (`search` in companies.yaml), e.g. ["Turkey"].
"""

from careeros.jobs.sources.ats.base import TIMEOUT, Board, FetchResult, Posting, html_to_text

PAGE = 10           # the API returns at most 10 per page
MAX_PAGES = 30
MAX_DETAILS = 60    # detail requests per board per run


def _ts(value):
    from careeros.jobs.sources.feeds.base import epoch
    return epoch(value)


def fetch(board: Board, http, known_urls: set[str], keep_title=None) -> FetchResult:
    base = f"https://{board.host}"
    listed: dict[str, dict] = {}
    complete = True
    for location in board.search or ("",):
        start = 0
        for _ in range(MAX_PAGES):
            resp = http.get(f"{base}/api/pcsx/search", timeout=TIMEOUT,
                            params={"domain": board.board, "query": "", "location": location, "start": start, "num": PAGE})
            resp.raise_for_status()
            data = resp.json().get("data") or {}
            page = data.get("positions") or []
            for p in page:
                listed.setdefault(str(p["id"]), p)
            start += len(page)
            if not page or start >= int(data.get("count") or 0):
                break
        else:
            complete = False

    seen, postings, details = set(), [], 0
    for pid, item in listed.items():
        url = base + (item.get("positionUrl") or f"/careers/job/{pid}")
        seen.add(url)
        if url in known_urls or (keep_title and not keep_title(item.get("name") or "")):
            continue
        if details >= MAX_DETAILS:
            complete = False
            continue
        details += 1
        resp = http.get(f"{base}/api/pcsx/position_details", timeout=TIMEOUT,
                        params={"position_id": pid, "domain": board.board, "hl": "en"})
        resp.raise_for_status()
        postings.append(_posting(url, {**item, **(resp.json().get("data") or {})}))
    return FetchResult(postings=postings, complete=complete, seen_urls=seen)


def _posting(url: str, d: dict) -> Posting:
    where = d.get("workLocationOption") or ""
    return Posting(
        external_id=str(d["id"]),
        url=url,
        apply_url=url,
        title=(d.get("name") or "").strip(),
        location=" • ".join(d.get("locations") or [d.get("location") or ""]),
        description=html_to_text(d.get("jobDescription")),
        department=d.get("department") or None,
        posted_at=_ts(d.get("postedTs") or d.get("creationTs")),
        remote=True if where == "remote" else (False if where == "onsite" else None),
    )
