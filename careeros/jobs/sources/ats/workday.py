"""Workday career sites — the JSON endpoints behind *.myworkdayjobs.com pages.

Unofficial but public. The list endpoint pages 20 at a time and has no
descriptions, so each new posting costs one detail request. To stay polite and
bounded: optional server-side search terms, a page cap, and a detail cap per run
(the rest is picked up on the next run). Postings already stored are not re-fetched.
"""

import logging

from careeros.jobs.sources.ats.base import TIMEOUT, Board, FetchResult, Posting, html_to_text, parse_time

logger = logging.getLogger(__name__)

PAGE_SIZE = 20          # Workday rejects larger pages
MAX_PAGES = 50          # per search term → at most 1000 listings
MAX_DETAILS = 150       # new postings fetched in full per board per run


def _base(board: Board) -> str:
    return f"https://{board.host}/wday/cxs/{board.tenant}/{board.site}"


def public_url(board: Board, external_path: str) -> str:
    return f"https://{board.host}/{board.site}{external_path}"


def _list(board: Board, http, search: str) -> tuple[list[dict], bool]:
    listings, complete = [], True
    for page in range(MAX_PAGES):
        resp = http.post(
            f"{_base(board)}/jobs",
            json={"appliedFacets": {}, "limit": PAGE_SIZE, "offset": page * PAGE_SIZE, "searchText": search},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("jobPostings") or []
        listings.extend(batch)
        if len(batch) < PAGE_SIZE or len(listings) >= (data.get("total") or 0):
            break
    else:
        complete = False
    return listings, complete


def fetch(board: Board, http, known_urls: set[str], keep_title=None) -> FetchResult:
    result = FetchResult()
    listings: dict[str, dict] = {}
    for term in board.search or ("",):
        batch, complete = _list(board, http, term)
        result.complete &= complete
        for item in batch:
            if item.get("externalPath"):
                # With search terms only a subset is listed, but the same subset every
                # run, so a posting that drops out of it is still closed (or no longer relevant)
                listings.setdefault(item["externalPath"], item)

    fetched = 0
    for path, item in listings.items():
        url = public_url(board, path)
        result.seen_urls.add(url)
        if url in known_urls:
            continue
        if keep_title and not keep_title(item.get("title") or ""):
            continue  # the list has titles: don't pay a detail request for a posting we'd drop
        if fetched >= MAX_DETAILS:
            result.complete = False
            continue
        try:
            resp = http.get(f"{_base(board)}{path}", timeout=TIMEOUT)
            resp.raise_for_status()
            result.postings.append(_posting(board, item, resp.json().get("jobPostingInfo") or {}))
            fetched += 1
        except Exception as e:  # one broken posting shouldn't sink the board
            logger.warning("[workday:%s] detail failed for %s: %s", board.key, path, e)
    return result


def _posting(board: Board, item: dict, info: dict) -> Posting:
    url = public_url(board, item["externalPath"])
    remote_type = (info.get("remoteType") or "").lower()
    return Posting(
        external_id=info.get("jobReqId") or (item.get("bulletFields") or [item["externalPath"]])[0],
        url=url,
        apply_url=info.get("externalUrl") or url,
        title=(info.get("title") or item.get("title") or "").strip(),
        location=(info.get("location") or item.get("locationsText") or "").strip(),
        description=html_to_text(info.get("jobDescription")),
        employment_type=info.get("timeType"),
        posted_at=parse_time(info.get("startDate")),
        remote=True if "remote" in remote_type else None,
    )
