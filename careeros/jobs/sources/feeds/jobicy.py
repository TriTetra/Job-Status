"""Jobicy remote jobs API, filtered to Europe and the UK. Terms: credit Jobicy with a link,
and the apply button goes to the job URL it gives.

https://jobicy.com/jobs-rss-feed
"""

from careeros.jobs.sources.ats.base import TIMEOUT, html_to_text, parse_time
from careeros.jobs.sources.feeds.base import FeedPosting, html_links, yearly

API = "https://jobicy.com/api/v2/remote-jobs"
GEOS = ("europe", "uk", "germany", "spain", "switzerland")


def fetch(http) -> list[FeedPosting]:
    seen: dict[str, FeedPosting] = {}
    for geo in GEOS:
        resp = http.get(API, params={"count": 100, "geo": geo}, timeout=TIMEOUT)
        if resp.status_code == 400:  # unknown geo slug: skip it, keep the rest
            continue
        resp.raise_for_status()
        for j in resp.json().get("jobs") or []:
            if j.get("url") and j["url"] not in seen:
                seen[j["url"]] = _posting(j)
    return list(seen.values())


def _posting(j: dict) -> FeedPosting:
    low, high, cur = yearly(j.get("salaryMin") or j.get("annualSalaryMin"), j.get("salaryMax") or j.get("annualSalaryMax"),
                            j.get("salaryCurrency"), j.get("salaryPeriod") or "yearly")
    kinds = j.get("jobType") or []
    return FeedPosting(
        source="jobicy",
        external_id=str(j.get("id") or j["url"])[-128:],
        url=j["url"],
        apply_url=j["url"],
        title=(j.get("jobTitle") or "").strip(),
        company=(j.get("companyName") or "").strip()[:200] or "Unknown",
        location=("Remote: " + j["jobGeo"]) if j.get("jobGeo") else "Remote",
        description=html_to_text(j.get("jobDescription")),
        posted_at=parse_time(j.get("pubDate")),
        remote=True,
        employment_type=", ".join(kinds)[:64] if isinstance(kinds, list) else (kinds or None),
        salary_min=low, salary_max=high, salary_currency=cur,
        links=html_links(j.get("jobDescription")),
    )
