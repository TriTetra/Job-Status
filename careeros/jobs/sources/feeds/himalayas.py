"""Himalayas remote jobs API. Its feed has 100k+ jobs, so it is searched for the fields
CareerOS targets, both plainly and for jobs open to people in Turkey; each job lists
the countries a remote hire may live in.

https://himalayas.app/jobs/api  (search: /jobs/api/search?q=, 20 per page)
"""

from careeros.jobs.sources.ats.base import TIMEOUT, html_to_text
from careeros.jobs.sources.feeds.base import FeedPosting, epoch, html_links, remote_where, yearly

SEARCH = "https://himalayas.app/jobs/api/search"
QUERIES = ("machine learning", "AI engineer", "LLM", "data scientist", "MLOps")
# Also search jobs open to people living in these countries (the plain search is US-heavy)
COUNTRIES = ("Turkey",)
PAGES = 2


def fetch(http) -> list[FeedPosting]:
    seen: dict[str, FeedPosting] = {}
    for q in QUERIES:
        for country in (None, *COUNTRIES):
            _search(http, seen, q, country)
    return list(seen.values())


def _search(http, seen: dict[str, FeedPosting], q: str, country) -> None:
    for page in range(1, PAGES + 1):
        params = {"q": q, "page": page, **({"country": country} if country else {})}
        resp = http.get(SEARCH, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        jobs = resp.json().get("jobs") or []
        for j in jobs:
            url = j.get("guid") or j.get("applicationLink")
            if url and url not in seen:
                seen[url] = _posting(j, url)
        if len(jobs) < 20:
            break


def _posting(j: dict, url: str) -> FeedPosting:
    location, description = remote_where(j.get("locationRestrictions") or [], html_to_text(j.get("description")))
    low, high, cur = yearly(j.get("minSalary"), j.get("maxSalary"), j.get("currency"), j.get("salaryPeriod"))
    return FeedPosting(
        source="himalayas",
        external_id=url[-128:],
        url=url,
        apply_url=j.get("applicationLink") or url,
        title=(j.get("title") or "").strip(),
        company=(j.get("companyName") or "").strip()[:200] or "Unknown",
        location=location,
        description=description,
        posted_at=epoch(j.get("pubDate")),
        remote=True,
        employment_type=j.get("employmentType") or None,
        salary_min=low, salary_max=high, salary_currency=cur,
        links=html_links(j.get("description")),
        logo_url=j.get("companyLogo") or None,
    )
