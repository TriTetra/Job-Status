"""Arbeitnow job board API: Germany-focused, many startups and mid-sized companies, 300 per page.

https://www.arbeitnow.com/blog/job-board-api  (free; asks for a link back)
"""

from careeros.jobs.sources.ats.base import TIMEOUT, html_to_text
from careeros.jobs.sources.feeds.base import FeedPosting, epoch, html_links

API = "https://www.arbeitnow.com/api/job-board-api"
PAGES = 3  # newest first; ~900 postings is a few days' worth


def fetch(http) -> list[FeedPosting]:
    out = []
    for page in range(1, PAGES + 1):
        resp = http.get(API, params={"page": page}, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        out += [_posting(j) for j in data.get("data") or [] if j.get("url") and j.get("slug")]
        if not (data.get("links") or {}).get("next"):
            break
    return out


def _posting(j: dict) -> FeedPosting:
    types = j.get("job_types") or []
    return FeedPosting(
        source="arbeitnow",
        external_id=j["slug"][:128],
        url=j["url"],
        apply_url=j["url"],
        title=(j.get("title") or "").strip(),
        company=(j.get("company_name") or "").strip()[:200] or "Unknown",
        location=(j.get("location") or "").strip(),
        description=html_to_text(j.get("description")),
        posted_at=epoch(j.get("created_at")),
        remote=True if j.get("remote") else None,
        employment_type=", ".join(types)[:64] or None,
        links=html_links(j.get("description")),
    )
