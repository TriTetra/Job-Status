"""Adzuna job search API: one search engine over many countries' job sites (GB, DE, NL, PL, AT,
ES, CH, FR, IT…). Searched for the roles and countries Aplio's users target.

Terms (developer.adzuna.com/docs/terms_of_service): permitted for personal job search and for
publishing Adzuna listings; every displayed listing carries an "Adzuna" label (≥116×23 px)
linked to Adzuna's local site, and the job links to Adzuna's redirect URL. Commercial use
needs Adzuna's written agreement. Calls are capped per account (API Access plan: 500 a day,
5,000 a month; before activation 25 test calls in all), so a read makes at most ADZUNA_MAX_CALLS
requests and stops, keeping what it has, when Adzuna refuses (quota spent, key not active).
Needs ADZUNA_APP_ID and ADZUNA_APP_KEY; without them it is off. The key travels as a query
parameter, so request URLs never go into logs or error messages.

https://developer.adzuna.com/docs/search
"""

import logging
from typing import Optional

from careeros.jobs.sources.ats.base import TIMEOUT, html_to_text, parse_time
from careeros.jobs.sources.feeds.base import FeedPosting, yearly

logger = logging.getLogger(__name__)

API = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
PER_PAGE = 50
PAGES = 2
MAX_CALLS = 40          # default per read (ADZUNA_MAX_CALLS); feeds run about twice a day
REFUSED = (401, 403, 429)  # bad or inactive key, plan not allowing it, quota spent: stop, keep what we have
MAX_QUERIES = 4
MAX_DAYS_OLD = 30

# Country code → (currency, Adzuna's local site for the attribution link)
COUNTRIES = {
    "gb": ("GBP", "https://www.adzuna.co.uk"), "de": ("EUR", "https://www.adzuna.de"),
    "nl": ("EUR", "https://www.adzuna.nl"), "pl": ("PLN", "https://www.adzuna.pl"),
    "at": ("EUR", "https://www.adzuna.at"), "es": ("EUR", "https://www.adzuna.es"),
    "ch": ("CHF", "https://www.adzuna.ch"), "fr": ("EUR", "https://www.adzuna.fr"),
    "it": ("EUR", "https://www.adzuna.it"), "be": ("EUR", "https://www.adzuna.be"),
    "us": ("USD", "https://www.adzuna.com"), "ca": ("CAD", "https://www.adzuna.ca"),
    "au": ("AUD", "https://www.adzuna.com.au"), "nz": ("NZD", "https://www.adzuna.co.nz"),
    "sg": ("SGD", "https://www.adzuna.sg"), "in": ("INR", "https://www.adzuna.in"),
}
DEFAULT_COUNTRIES = ("gb", "de", "nl", "pl", "es", "ch")
DEFAULT_QUERIES = ("machine learning engineer", "AI engineer", "data scientist", "backend engineer")


def site_for(country_code: Optional[str]) -> str:
    """Adzuna's local site for an ISO country code (the attribution link)."""
    return COUNTRIES.get((country_code or "").lower(), ("", "https://www.adzuna.co.uk"))[1]


class AdzunaError(RuntimeError):
    """An Adzuna failure, described without the request URL (it carries the key)."""


def _reason(resp) -> str:
    """Adzuna's short error code (e.g. AUTH_FAIL) if the body has one; never the URL."""
    try:
        body = resp.json() or {}
        return str(body.get("exception") or body.get("display") or "")[:120]
    except Exception:
        return ""


def _budget() -> int:
    from careeros.shared.config import get_settings

    return getattr(get_settings(), "adzuna_max_calls", MAX_CALLS)


def _keys() -> Optional[tuple[str, str]]:
    from careeros.shared.config import get_settings

    s = get_settings()
    return (s.adzuna_app_id, s.adzuna_app_key) if s.adzuna_app_id and s.adzuna_app_key else None


def targets() -> tuple[list[str], list[str]]:
    """(countries, queries) from what users target, limited to what Adzuna covers; defaults if none."""
    countries, queries = [], []
    try:
        from careeros.db.connection import db
        from careeros.identity.models.career_preferences import CareerPreferences
        from careeros.identity.models.role import Role

        with db.session_scope() as s:
            role_ids: set[str] = set()
            for codes, roles in s.query(CareerPreferences.preferred_country_codes, CareerPreferences.preferred_role_ids):
                countries += [c.lower() for c in codes or [] if c and c.lower() in COUNTRIES]
                role_ids.update(str(r) for r in roles or [])
            if role_ids:
                from sqlalchemy import String, cast, or_

                queries = [t for (t,) in s.query(Role.title).filter(
                    or_(cast(Role.id, String).in_(role_ids), Role.slug.in_(role_ids))).all() if t]
    except Exception as e:  # no database (tests, CLI dry run elsewhere): defaults
        logger.info("Adzuna targets from defaults (%s)", e)
    countries = list(dict.fromkeys(countries)) or list(DEFAULT_COUNTRIES)
    queries = list(dict.fromkeys(q.strip() for q in queries if q and q.strip()))[:MAX_QUERIES] or list(DEFAULT_QUERIES)
    return countries, queries


def fetch(http, countries: Optional[list[str]] = None, queries: Optional[list[str]] = None) -> list[FeedPosting]:
    keys = _keys()
    if not keys:
        logger.info("Adzuna is off: ADZUNA_APP_ID / ADZUNA_APP_KEY not set")
        return []
    if countries is None or queries is None:
        c, q = targets()
        countries, queries = countries or c, queries or q
    seen: dict[str, FeedPosting] = {}
    calls, budget = 0, _budget()
    for country in countries:
        offered = True
        for q in queries:
            if not offered:
                break
            for page in range(1, PAGES + 1):
                if calls >= budget:
                    return list(seen.values())
                calls += 1
                try:
                    resp = http.get(API.format(country=country, page=page), timeout=TIMEOUT, params={
                        "app_id": keys[0], "app_key": keys[1], "what": q, "results_per_page": PER_PAGE,
                        "max_days_old": MAX_DAYS_OLD, "sort_by": "date", "content-type": "application/json"})
                except Exception as e:  # connection errors quote the URL, key included: name the error only
                    if seen:
                        logger.warning("Adzuna request failed (%s): keeping %d job(s)", type(e).__name__, len(seen))
                        return list(seen.values())
                    raise AdzunaError(f"request failed: {type(e).__name__}") from None
                if resp.status_code == 404:  # country not offered: skip it entirely
                    offered = False
                    break
                if resp.status_code in REFUSED:
                    logger.warning("Adzuna refused (HTTP %s %s) after %d call(s): keeping %d job(s)",
                                   resp.status_code, _reason(resp), calls, len(seen))
                    return list(seen.values())
                if resp.status_code >= 400:  # not raise_for_status(): its message holds the URL and key
                    if seen:
                        logger.warning("Adzuna HTTP %s %s: keeping %d job(s)", resp.status_code, _reason(resp), len(seen))
                        return list(seen.values())
                    raise AdzunaError(f"HTTP {resp.status_code} {_reason(resp)}".strip())
                results = resp.json().get("results") or []
                for j in results:
                    p = _posting(j, country)
                    if p and p.url not in seen:
                        seen[p.url] = p
                if len(results) < PER_PAGE:
                    break
    return list(seen.values())


def _posting(j: dict, country: str) -> Optional[FeedPosting]:
    url = j.get("redirect_url")
    title = (j.get("title") or "").strip()
    if not url or not title:
        return None
    loc = j.get("location") or {}
    where = (loc.get("display_name") or "").strip()
    area = [a for a in loc.get("area") or [] if a]
    if area and area[0] not in where:
        where = f"{where}, {area[0]}" if where else area[0]
    description = html_to_text(j.get("description"))
    text = f"{title} {description}".lower()
    predicted = str(j.get("salary_is_predicted") or "0") == "1"
    currency = COUNTRIES.get(country, ("USD", ""))[0]
    low, high, cur = (None, None, None) if predicted else yearly(j.get("salary_min"), j.get("salary_max"), currency, "year")
    return FeedPosting(
        source="adzuna",
        external_id=str(j.get("id") or url)[-128:],
        url=url,
        apply_url=url,
        title=title,
        company=((j.get("company") or {}).get("display_name") or "").strip()[:200] or "Unknown",
        location=where[:200],
        description=description,
        posted_at=parse_time(j.get("created")),
        remote=True if ("remote" in title.lower() or "fully remote" in text) else None,
        employment_type=j.get("contract_time") or None,
        salary_min=low, salary_max=high, salary_currency=cur,
    )
