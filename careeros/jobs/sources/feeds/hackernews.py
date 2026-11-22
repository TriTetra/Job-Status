"""Hacker News "Ask HN: Who is hiring?": every month hundreds of startups post their own
openings, one comment each, usually "Company | Role | Location | REMOTE | VISA | link".
Read through the public Algolia HN API.
"""

import html
import re
from typing import Optional

from careeros.jobs.discovery import board_from_url
from careeros.jobs.sources.ats.base import TIMEOUT, html_to_text, parse_time
from careeros.jobs.sources.feeds.base import FeedPosting, html_links

SEARCH = "https://hn.algolia.com/api/v1/search_by_date"
ITEM = "https://hn.algolia.com/api/v1/items/{id}"
_ROLE = re.compile(r"\b(engineer|engineering|developer|scientist|researcher|ML|AI|LLM|data|devops|SRE|architect|"
                   r"lead|head of|founding|backend|frontend|full[\s-]?stack|platform|infrastructure|security|"
                   r"analyst|designer|manager|product)\b", re.I)
_PLACE = re.compile(r"\b(remote|onsite|on-site|hybrid|visa|full[\s-]?time|part[\s-]?time|contract|intern)\b", re.I)


def latest_thread(http) -> Optional[dict]:
    resp = http.get(SEARCH, params={"tags": "story,author_whoishiring", "hitsPerPage": 10}, timeout=TIMEOUT)
    resp.raise_for_status()
    for hit in resp.json().get("hits", []):
        if (hit.get("title") or "").lower().startswith("ask hn: who is hiring"):
            return hit
    return None


def fetch(http) -> list[FeedPosting]:
    thread = latest_thread(http)
    if not thread:
        return []
    resp = http.get(ITEM.format(id=thread["objectID"]), timeout=TIMEOUT)
    resp.raise_for_status()
    out = []
    for c in resp.json().get("children") or []:
        p = parse_comment(c)
        if p:
            out.append(p)
    return out


def _segments(first_line: str) -> list[str]:
    return [s.strip() for s in first_line.split("|") if s.strip()]


def parse_comment(c: dict) -> Optional[FeedPosting]:
    raw = c.get("text") or ""
    if not raw or c.get("author") in (None, "") or not c.get("id"):
        return None
    first_html = re.split(r"<p>|\n", raw, maxsplit=1)[0]
    head = html.unescape(re.sub(r"<[^>]+>", "", first_html)).strip()
    parts = _segments(head)
    if len(parts) < 2:
        return None  # not the "Company | Role | ..." format
    company = re.sub(r"\s*\(.*?\)\s*$", "", parts[0]).strip()[:200]
    rest = parts[1:]
    role = next((p for p in rest if _ROLE.search(p) and not _PLACE.fullmatch(p.strip())), rest[0])
    where = [p for p in rest if p is not role and not re.search(r"https?://", p)]
    urls = html_links(raw)
    # Prefer the company's job board link, else the first link that isn't HN itself
    apply = next((u for u in urls if board_from_url(u)), None) or next((u for u in urls if "ycombinator.com" not in u), None)
    url = f"https://news.ycombinator.com/item?id={c['id']}"
    return FeedPosting(
        source="hackernews",
        external_id=str(c["id"]),
        url=url,
        apply_url=apply or url,
        title=role[:300],
        company=company or "Unknown",
        location=" | ".join(where)[:256],
        description=html_to_text(raw),
        posted_at=parse_time(c.get("created_at")),
        remote=True if re.search(r"\bremote\b", head, re.I) and not re.search(r"\bno remote\b", head, re.I) else None,
        links=urls,
    )
