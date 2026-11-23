"""Search every open job, not just the user's matches: by words, country and filters.

Opportunities are the jobs that match the user's target roles, scored by the scan. Search
reads the whole corpus (company boards + feeds). A result the scan already scored keeps
that score; any other is scored on the fly with the same model and not saved, so a search
never changes Opportunities.
"""

import logging
import time
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from careeros.jobs.geo import CITIES, COUNTRY_NAMES, location_match
from careeros.jobs.models.career_score import CareerScore
from careeros.jobs.models.job import Job as JobRow

logger = logging.getLogger(__name__)

MAX_CANDIDATES = 600       # newest postings read per search; the UI asks to narrow beyond that
PAGE_MAX = 100
PROFILE_TTL_S = 60         # profile, weights and preferences are re-read at most once a minute
SIZES = {"startup", "midsize", "large"}
WORK = {"remote", "hybrid", "onsite"}
SORTS = {"score", "newest"}


@dataclass
class SearchFilters:
    q: str = ""
    country: Optional[str] = None          # ISO code: located there, or remote and open to it
    work: list[str] = field(default_factory=list)   # remote / hybrid / onsite; empty = any
    sizes: list[str] = field(default_factory=list)  # startup / midsize / large; empty = any
    reliable: bool = False                 # hide agencies and postings with scam signs
    reachable: bool = True                 # hide roles you can't take (gated, or remote for other countries)
    visa: bool = False                     # only postings that say they sponsor a visa
    min_salary_usd: Optional[int] = None   # only postings stating at least this (yearly, in USD)
    source: Optional[str] = None           # "company" (their own job system) / "feed"
    days: Optional[int] = None             # posted within
    sort: str = "score"
    limit: int = 50
    offset: int = 0


@dataclass
class SearchResult:
    total: int
    capped: bool                           # more postings matched the words than were read
    items: list[dict]
    country: Optional[str] = None          # the country searched (also when it was typed as a place)


# ── who is searching (cached briefly: a search is typed, filtered, refined) ──

_viewer_cache: dict[str, tuple[float, tuple]] = {}


def _viewer(user_id: str):
    """(profile or None, weights, prefs) for scoring on the fly."""
    hit = _viewer_cache.get(user_id)
    if hit and time.monotonic() - hit[0] < PROFILE_TTL_S:
        return hit[1]
    from careeros.jobs.scan import load_profile, load_weights
    from careeros.jobs.scoring.signals import seeker_for
    from careeros.jobs.scoring_service import ScoringService

    profile = load_profile(user_id)
    weights = load_weights(user_id)
    if profile is not None:
        profile.seeker = seeker_for(profile, weights)
    value = (profile, weights, ScoringService(user_id).load_prefs())
    _viewer_cache[user_id] = (time.monotonic(), value)
    return value


def forget_viewer(user_id: str) -> None:
    _viewer_cache.pop(user_id, None)


# ── the query ──

def _words(q: str) -> list[str]:
    cleaned = "".join(" " if ch in "%_\\" else ch for ch in (q or ""))
    return [w for w in cleaned.split() if len(w) >= 2][:6]


def _place_names(code: str) -> list[str]:
    """Every way a location string may name this country (SQL ILIKE, so dotted capitals are added:
    the database doesn't lower-case "İstanbul" to "istanbul")."""
    from careeros.jobs.geo import COUNTRY_ALIASES

    names = [n for n, c in COUNTRY_NAMES + COUNTRY_ALIASES if c == code] + [city for city, c in CITIES.items() if c == code]
    dotted = ["İ" + n[2:] for n in names if n.startswith("i̇")] + [n.replace("i", "İ", 1) for n in names if n.startswith("i") and not n.startswith("i̇")]
    return list(dict.fromkeys(names + dotted))


def place_in_query(q: str) -> tuple[Optional[str], str]:
    """A place typed in the search box ("İstanbul", "Türkiye", "Berlin") → (its country code, the other words).
    Only when every place word points to one country; otherwise the words stay as text."""
    from careeros.jobs.geo import countries_in

    words = (q or "").split()
    codes = {w: {c for c, _ in countries_in(w)} for w in words if len(w) >= 3}
    found = {c for cs in codes.values() for c in cs}
    if len(found) != 1:
        return None, q
    rest = [w for w in words if not codes.get(w)]
    return found.pop(), " ".join(rest)


def candidates(session: Session, f: SearchFilters, now: datetime,
               user_id: Optional[str] = None) -> tuple[list[JobRow], bool]:
    """Open postings matching the words, country (by name, or remote), source and age; newest first.
    Jobs people added themselves are seen only by them."""
    q = session.query(JobRow).filter(JobRow.closed_at.is_(None), JobRow.visible_to(user_id))
    for w in _words(f.q):
        like = f"%{w}%"
        q = q.filter(or_(JobRow.title.ilike(like), JobRow.company.ilike(like), JobRow.department.ilike(like),
                         JobRow.location.ilike(like)))
    if f.source == "feed":
        q = q.filter(JobRow.source == "feed")
    elif f.source == "company":
        q = q.filter(JobRow.source != "feed")
    when = func.coalesce(JobRow.posted_at, JobRow.discovered_at)
    if f.days:
        q = q.filter(when >= now - timedelta(days=f.days))
    if not f.country:
        rows = q.order_by(when.desc().nullslast()).limit(MAX_CANDIDATES + 1).all()
        return rows[:MAX_CANDIDATES], len(rows) > MAX_CANDIDATES
    # Jobs located in the country first: remote postings (open to many countries) are far more
    # numerous and would otherwise fill the read and push them out
    in_country = or_(*[JobRow.location.ilike(f"%{n}%") for n in _place_names(f.country)])
    located = q.filter(in_country).order_by(when.desc().nullslast()).limit(MAX_CANDIDATES + 1).all()
    room = max(0, MAX_CANDIDATES - len(located))
    remote = or_(JobRow.remote.is_(True), JobRow.llm_facts["workplace"].astext == "remote")
    far = (q.filter(remote, ~in_country).order_by(when.desc().nullslast()).limit(room + 1).all() if room else [])
    capped = len(located) > MAX_CANDIDATES or len(far) > room
    return located[:MAX_CANDIDATES] + far[:room], capped


def _workplace(job) -> str:
    return "remote" if job.remote else "hybrid" if job.hybrid else "onsite"


def _size(size: str) -> str:
    return "large" if size == "big_tech" else size


def keeps(job, meta: dict, f: SearchFilters) -> bool:
    """The filters the database can't apply: country by geography, work style, size, trust, visa, pay."""
    if f.country and location_match(meta["location"], meta["remote_regions"], [f.country], job.remote) is not True:
        return False
    if f.work and _workplace(job) not in f.work:
        return False
    if f.sizes and _size(meta["company_size"]) not in f.sizes:
        return False
    trust = meta.get("trust") or {}
    if f.reliable and (trust.get("level") == "risk" or trust.get("agency")):
        return False
    if f.visa and job.sponsors_visa is not True:
        return False
    if f.min_salary_usd:
        offer = getattr(job.signals, "offer_usd", None)
        if not offer or offer < f.min_salary_usd:
            return False
    return True


def reachable(record: dict) -> bool:
    """False when the model rules the job out for you, or it's remote only for people elsewhere."""
    m = (record.get("explanation") or {}).get("model") or {}
    if not m:
        return True
    if m.get("gates"):
        return False
    return (m.get("chance_factors") or {}).get("location", 1) > 0.1


def _plain(meta: dict) -> dict:
    """A result with no score (the user has no profile yet): what the reader needs to show it."""
    return dict(career_score=None, fit_score=None, acceptance_probability=None, career_value=None,
                market_demand=None, expected_value=None, recommendation=None, skill_gaps=[],
                explanation={k: v for k, v in meta.items() if v not in (None, "", [], "unknown")})


def _stored(s: CareerScore) -> dict:
    return dict(career_score=s.career_score, fit_score=s.fit_score, acceptance_probability=s.acceptance_probability,
                career_value=s.career_value, market_demand=s.market_demand, expected_value=s.expected_value,
                recommendation=s.recommendation, skill_gaps=s.skill_gaps or [], explanation=s.explanation or {},
                scanned_at=s.scanned_at.isoformat() if s.scanned_at else None)


# ── per-posting work, cached: reading a posting's text (trust, languages, signals) is the slow part ──

CACHE_MAX = 6000
_prepared: dict[tuple, tuple] = {}
_scored: dict[tuple, dict] = {}


def _remember(cache: dict, key, value) -> None:
    if len(cache) >= CACHE_MAX:
        for k in list(cache)[: CACHE_MAX // 4]:  # oldest first
            cache.pop(k, None)
    cache[key] = value


def _content_key(r: JobRow) -> tuple:
    return (r.url, r.content_hash, r.llm_facts_hash, r.closed_at is None)


def prepare(rows: list[JobRow], open_counts: dict, preferred: list[str], now: datetime) -> tuple[list, dict]:
    """to_scoring_input for these rows, reusing what was read today for the same posting.
    Pay references (market medians) are left out here and set per search."""
    from careeros.jobs.scan import company_size_of, to_scoring_input

    pref = tuple(sorted(preferred or []))
    keys = {r.url: (*_content_key(r), company_size_of(r, open_counts), pref, now.date()) for r in rows}
    missing = [r for r in rows if keys[r.url] not in _prepared]
    if missing:
        jobs, meta = to_scoring_input(missing, open_counts, list(pref), now=now, market_medians={})
        for j in jobs:
            _remember(_prepared, keys[j.url], (j, meta[j.url]))
    jobs, meta = [], {}
    for r in rows:
        j, m = _prepared[keys[r.url]]
        jobs.append(j)
        meta[r.url] = m
    return jobs, meta


def with_pay_reference(jobs: list, medians: dict[str, int]) -> list:
    """Copies of the jobs whose signals carry this search's typical pay per country."""
    out = []
    for j in jobs:
        sig = j.signals
        ref = next((medians[c] for c in sig.countries if c in medians), medians.get("*"))
        out.append(replace(j, signals=replace(sig, market_median_usd=ref)))
    return out


def search(session: Session, user_id: str, f: SearchFilters, now: Optional[datetime] = None) -> SearchResult:
    from careeros.jobs.scan import company_open_counts, profile_fingerprint
    from careeros.jobs.scoring.signals import market_medians
    from careeros.jobs.scoring_service import ScoringService

    now = now or datetime.now(timezone.utc)
    if not f.country and f.q:
        code, rest = place_in_query(f.q)
        if code:  # "istanbul engineer" → country Türkiye, words "engineer"
            f = replace(f, country=code, q=rest)
    rows, capped = candidates(session, f, now, user_id)
    if not rows:
        return SearchResult(total=0, capped=False, items=[], country=f.country)

    profile, weights, prefs = _viewer(user_id)
    preferred = profile.preferences.preferred_locations if profile else []
    jobs, meta = prepare(rows, company_open_counts(session), preferred, now)
    # Pay is judged against what similar roles (this search's postings) pay in the same country
    medians = market_medians((j.signals.countries, j.signals.offer_usd) for j in jobs)
    kept = with_pay_reference([j for j in jobs if keeps(j, meta[j.url], f)], medians)

    urls = [j.url for j in kept]
    stored = {s.url: s for s in session.query(CareerScore)
              .filter(CareerScore.user_id == user_id, CareerScore.url.in_(urls)).all()} if urls else {}
    # The scan's own score when it is current (v8); everything else is scored now, not saved
    records: dict[str, dict] = {}
    for url in urls:
        s = stored.get(url)
        if s is not None and ((s.explanation or {}).get("model") or {}).get("v") == 8:
            records[url] = {**_stored(s), "in_opportunities": True}
    fresh = [j for j in kept if j.url not in records]
    if fresh and profile is not None:
        viewer = profile_fingerprint(profile, prefs, weights)
        by_row = {r.url: r for r in rows}
        key = {j.url: (user_id, viewer, *_content_key(by_row[j.url]), j.signals.market_median_usd, now.date())
               for j in fresh}
        todo = [j for j in fresh if key[j.url] not in _scored]
        if todo:
            scored = ScoringService(user_id).preview(todo, profile, weights, job_meta=meta, prefs=prefs)
            for url, rec in scored.items():
                _remember(_scored, key[url], rec)
        for j in fresh:
            records[j.url] = {**_scored[key[j.url]], "scanned_at": None, "in_opportunities": False}
    for j in fresh:
        records.setdefault(j.url, {**_plain(meta[j.url]), "scanned_at": None, "in_opportunities": False})

    order = {j.url: i for i, j in enumerate(kept)}  # newest first
    items = [{"url": u, **records[u]} for u in urls]
    if f.reachable and profile is not None:
        items = [it for it in items if reachable(it)]
    if f.sort == "score":
        items.sort(key=lambda it: (-(it["career_score"] or 0), order[it["url"]]))
    total = len(items)
    return SearchResult(total=total, capped=capped, items=items[f.offset:f.offset + f.limit], country=f.country)
