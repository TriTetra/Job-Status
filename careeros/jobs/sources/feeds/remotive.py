"""Remotive remote jobs API. Terms: credit Remotive, link back to its posting, at most
4 requests a day (the feed sync runs twice a day, one request each).

https://remotive.com/api-documentation
"""

from careeros.jobs.sources.ats.base import TIMEOUT, html_to_text, parse_time
from careeros.jobs.sources.feeds.base import FeedPosting, html_links

API = "https://remotive.com/api/remote-jobs"


def fetch(http) -> list[FeedPosting]:
    resp = http.get(API, timeout=TIMEOUT)
    resp.raise_for_status()
    return [_posting(j) for j in resp.json().get("jobs") or [] if j.get("url") and j.get("id")]


def _posting(j: dict) -> FeedPosting:
    return FeedPosting(
        source="remotive",
        external_id=str(j["id"]),
        url=j["url"],
        apply_url=j["url"],
        title=(j.get("title") or "").strip(),
        company=(j.get("company_name") or "").strip()[:200] or "Unknown",
        location=(j.get("candidate_required_location") or "").strip(),
        description=html_to_text(j.get("description")),
        posted_at=parse_time(j.get("publication_date")),
        remote=True,
        employment_type=(j.get("job_type") or None),
        links=html_links(j.get("description")),
    )
