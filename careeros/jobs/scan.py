"""Scan pipeline: open jobs in `jobs` → the user's titles → score what changed → upsert.

Jobs come from board syncs (careeros/jobs/ingest.py), not from the scan itself.
A job is rescored only when its input hash changes: the posting's content, the
user's profile fingerprint, or SCORER_VERSION. Runs as a background job; progress
is polled from `scan_jobs`.
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import sqlalchemy as sa

from careeros.db.connection import db
from careeros.jobs.domain.job import Job
from careeros.jobs.llm_extract import SENIORITY_YEARS
from careeros.jobs.models.job import Job as JobRow
from careeros.knowledge.skill_names import canonical_list
from careeros.identity.domain.skill import Skill, SkillLevel
from careeros.identity.domain.profile import UserProfile
from careeros.evidence.aggregation import aggregate_user_skills
from careeros.shared.background import BackgroundJob, JobStore

logger = logging.getLogger(__name__)

scan_jobs = JobStore()

DEFAULT_YEARS_EXPERIENCE = 2.0
ALL_TIME_HOURS = 99999
# Bump when scoring logic changes: every job is rescored on the next scan
SCORER_VERSION = "8.2"  # 8.2: locations (USA, states, cities; unknown ≠ free pass), on-site vs hybrid, implied skills · 8.1: title families (generic words don't match), one profile source · 5: work-style prefs, user weights · 6: salary in the explanation · 7: location, trust, company size, currencies, demand from the corpus · 8: chance-weighted surplus


def skill_level_for(confidence: float) -> SkillLevel:
    """Aggregated evidence confidence → the scorer's skill level."""
    if confidence >= 0.9:
        return SkillLevel.EXPERT
    if confidence >= 0.8:
        return SkillLevel.ADVANCED
    if confidence >= 0.65:
        return SkillLevel.INDEPENDENT
    return SkillLevel.WORKING


def build_profile_from_evidence(user_id: str) -> Optional[UserProfile]:
    """UserProfile for a web user from users + evidence_items (+ sponsorship preference)."""
    with db.session_scope() as s:
        row = s.execute(
            sa.text("SELECT profile_data, years_in_role, email FROM users WHERE id = :u"), {"u": user_id}
        ).fetchone()
        if not row:
            return None
        aggregated = aggregate_user_skills(user_id, s)
        if not aggregated:
            return None

        profile_data, years_in_role, email = row[0] or {}, row[1], row[2]
        name = " ".join(x for x in [profile_data.get("first_name"), profile_data.get("last_name")] if x) or "Candidate"
        # total_years lives in profile_data JSONB; years_in_role is the column fallback
        years = float(profile_data.get("total_years") or years_in_role or DEFAULT_YEARS_EXPERIENCE)
        skills = [Skill(a["skill_name"], skill_level_for(a["aggregated_confidence"])) for a in aggregated]
        skills += implied_skills(aggregated)
        profile = UserProfile(name=name, email=email or "", years_experience=years, skills=skills)

        prefs = s.execute(
            sa.text("SELECT requires_sponsorship, work_arrangements, preferred_country_codes, salary_min, salary_max, salary_currency "
                    "FROM career_preferences WHERE user_id = :u"), {"u": user_id}
        ).fetchone()
        apply_preferences(profile, prefs)
        apply_identity(profile, profile_data, s, user_id)
        return profile


def implied_skills(aggregated: list[dict]) -> list[Skill]:
    """Broader skills the evidence implies (PyTorch → Deep Learning → Machine Learning), at the
    confidence of the skill they come from, slightly lowered."""
    from careeros.knowledge.skill_names import canonical, implied_by, key

    conf = {key(a["skill_name"]): a["aggregated_confidence"] for a in aggregated}
    out = []
    for target, source in implied_by(a["skill_name"] for a in aggregated).items():
        conf[target] = conf.get(source, 0.6) * 0.9
        out.append(Skill(canonical(target), skill_level_for(conf[target])))
    return out


def apply_identity(profile: UserProfile, profile_data: dict, session, user_id: str) -> None:
    """Where the person lives, the languages they work in, the roles they target."""
    from careeros.jobs.geo import countries_in
    from careeros.jobs.scoring.signals import language_codes
    from careeros.jobs.targeting import role_terms

    found = countries_in(profile_data.get("country") or "")
    profile.preferences.residence_country = found[0][0] if found else None
    profile.preferences.languages = sorted(language_codes(profile_data.get("languages") or []))
    try:
        profile.target_roles = role_terms(session, [user_id]) or [profile_data.get("current_role_title") or ""]
    except Exception:  # roles are a nicety for title matching, never a reason to fail a scan
        profile.target_roles = [t for t in [profile_data.get("current_role_title")] if t]


def apply_preferences(profile: UserProfile, row) -> None:
    """Saved career preferences → the scorer's UserPreferences.

    No saved work arrangement means "any": every work style is acceptable, instead of the
    library default that penalised every on-site and hybrid job.
    """
    p = profile.preferences
    if row is None:
        p.remote = p.hybrid_acceptable = p.onsite_acceptable = True
        p.work_visa_required = False
        return
    sponsorship, arrangements, countries, salary_min, salary_max, *rest = row
    salary_currency = rest[0] if rest else None
    p.work_visa_required = bool(sponsorship)
    chosen = set(arrangements or [])
    if chosen:
        p.remote = "remote" in chosen
        p.hybrid_acceptable = "hybrid" in chosen
        p.onsite_acceptable = "onsite" in chosen
    else:
        p.remote = p.hybrid_acceptable = p.onsite_acceptable = True
    p.preferred_locations = list(countries or [])
    p.min_salary = salary_min
    p.max_salary = salary_max
    p.salary_currency = salary_currency or "USD"


def load_weights(user_id: str) -> dict:
    """The user's Settings → Scoring weights, normalised to sum to 1 (defaults if unset)."""
    from careeros.identity.repositories.user_settings_repo import UserSettingsRepository

    try:
        with db.session_scope() as s:
            raw = UserSettingsRepository(s).get_weights(user_id=user_id)
    except Exception as e:
        logger.info("Weights unavailable for %s (%s); using defaults", user_id, e)
        return {}
    return normalize_weights(raw)


WEIGHT_KEYS = ("pay", "growth", "stability", "work_style")  # v8 value weights; "effort" 1–3 rides along


def normalize_weights(raw: dict) -> dict:
    """Value weights scaled to sum to 1 (defaults when unusable), plus the effort setting."""
    from careeros.jobs.scoring.model_v8 import VALUE_WEIGHTS

    values = {k: max(0.0, float(raw.get(k, VALUE_WEIGHTS[k]) or 0)) for k in WEIGHT_KEYS}
    total = sum(values.values())
    out = {k: round(v / total, 4) for k, v in values.items()} if total > 0 else dict(VALUE_WEIGHTS)
    try:
        out["effort"] = min(3.0, max(1.0, float(raw.get("effort", 2) or 2)))
    except (TypeError, ValueError):
        out["effort"] = 2.0
    return out


def load_profile(user_id: str) -> Optional[UserProfile]:
    """The web profile (evidence, preferences, identity) — one source of truth for who the person is.
    The CLI-era user_settings profile is only a fallback for accounts that have no evidence at all."""
    profile = build_profile_from_evidence(user_id)
    if profile is not None:
        return profile
    from careeros.identity.profile_service import ProfileService

    try:
        legacy = ProfileService(user_id=user_id).get_profile()
    except Exception as e:
        logger.info("No profile for %s (%s)", user_id, e)
        return None
    return legacy if legacy is not None and getattr(legacy, "skills", []) else None


def profile_fingerprint(profile: UserProfile, prefs: dict, weights: Optional[dict] = None) -> str:
    """Everything about the user that changes a score (skills, years, preferences, weights)."""
    data = {
        "skills": sorted((sk.name.lower(), str(sk.level)) for sk in profile.skills),
        "years": profile.years_experience,
        "preferences": {k: str(v) for k, v in sorted(vars(profile.preferences).items())},
        "prefs": prefs,
        "weights": weights or {},
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()


def current_facts(row: JobRow) -> Optional[dict]:
    """LLM facts if they were extracted from this exact version of the posting."""
    if row.llm_facts and row.llm_facts_hash and row.llm_facts_hash == row.content_hash:
        return row.llm_facts
    return None


def input_hash(row: JobRow, fingerprint: str) -> str:
    content = row.content_hash or hashlib.sha256(f"{row.title}{row.location}{row.description}".encode()).hexdigest()
    reader = "llm" if current_facts(row) else "keywords"  # facts arriving later → rescore
    return hashlib.sha256(f"{SCORER_VERSION}:{content}:{reader}:{fingerprint}".encode()).hexdigest()


def pick_changed(rows: list[JobRow], known: dict[str, Optional[str]], fingerprint: str,
                 limit: int) -> tuple[list[JobRow], dict[str, str], int]:
    """(rows to score — first `limit`, in order —, their input hashes, how many are unchanged)."""
    changed, hashes = [], {}
    for r in rows:
        h = input_hash(r, fingerprint)
        if known.get(r.url) != h:
            changed.append(r)
            hashes[r.url] = h
    picked = changed[:limit]
    return picked, {r.url: hashes[r.url] for r in picked}, len(rows) - len(changed)


def candidate_urls(session, user_id: str, hours: int) -> list[str]:
    """Open jobs matching the user's titles, newest first (titles only — cheap)."""
    from careeros.jobs.targeting import user_title_filter

    titles = user_title_filter(session, user_id)
    q = session.query(JobRow.url, JobRow.title).filter(JobRow.closed_at.is_(None))
    if hours < ALL_TIME_HOURS:
        q = q.filter(JobRow.discovered_at >= datetime.now(timezone.utc) - timedelta(hours=hours))
    rows = q.order_by(JobRow.discovered_at.desc().nullslast()).all()
    return [url for url, title in rows if titles.keeps(title or "")]


_VISA = {"yes": True, "no": False}


def job_fields(r: JobRow) -> dict:
    """What scoring knows about a job: LLM facts when current, keyword extraction otherwise."""
    facts = current_facts(r)
    fields = {
        "required_skills": canonical_list(r.required_skills or []),
        "preferred_skills": [],
        "required_years": float(r.required_years or DEFAULT_YEARS_EXPERIENCE),
        "remote": bool(r.remote),
        "hybrid": False,
        "remote_region": r.remote_region,
        "sponsors_visa": r.sponsors_visa,
        "salary_min": r.salary_min,
        "salary_max": r.salary_max,
        "salary_currency": r.salary_currency or "USD",
        "summary": None,
        "extracted_by": "keywords",
        # what the posting says about where you work; None = not stated (keyword reading can't tell)
        "workplace": "remote" if r.remote else None,
    }
    if not facts:
        return fields
    fields["extracted_by"] = "llm"
    fields["summary"] = facts.get("summary") or None
    if facts.get("required_skills"):
        fields["required_skills"] = canonical_list(facts["required_skills"])
    fields["preferred_skills"] = canonical_list(facts.get("nice_to_have_skills") or [])
    years = facts.get("min_years")
    if years is None:
        years = SENIORITY_YEARS.get(facts.get("seniority"))
    if years is not None:
        fields["required_years"] = float(years)
    workplace = facts.get("workplace")
    if workplace in ("remote", "hybrid", "onsite"):
        fields["remote"] = workplace == "remote"
        fields["hybrid"] = workplace == "hybrid"
        fields["workplace"] = workplace
    if facts.get("remote_regions"):
        fields["remote_region"] = facts["remote_regions"][0]
    if facts.get("visa_sponsorship") in _VISA:
        fields["sponsors_visa"] = _VISA[facts["visa_sponsorship"]]
    if not (r.salary_min or r.salary_max) and facts.get("salary_period") == "year" and facts.get("salary_min"):
        fields.update(salary_min=facts["salary_min"], salary_max=facts.get("salary_max"),
                      salary_currency=facts.get("salary_currency") or "USD")
    return fields


# Postings on a company's whole board (every role, before the title filter) → its size,
# when the curated list doesn't say
SIZE_BY_OPEN_ROLES = ((25, "startup"), (200, "midsize"))
MIN_CORPUS_FOR_DEMAND = 100


def company_open_counts(session) -> dict[str, int]:
    """Board key → postings on the board at its last read (job_board_runs.fetched); stored
    open jobs only where a board has no run yet."""
    from sqlalchemy import func

    from careeros.jobs.models.board_run import JobBoardRun

    counts = {k: n for k, n in session.query(JobRow.company_key, func.count())
              .filter(JobRow.closed_at.is_(None), JobRow.company_key.isnot(None))
              .group_by(JobRow.company_key).all()}
    for key, fetched in session.query(JobBoardRun.company_key, JobBoardRun.fetched).all():
        if fetched and not key.startswith("feed:"):
            counts[key] = fetched
    return counts


def company_size_of(r: JobRow, open_counts: dict[str, int]) -> str:
    if r.company_size and r.company_size != "unknown":
        return r.company_size  # the curated list (big tech, large, …) wins
    n = open_counts.get(r.company_key or "")
    if n:
        return next((size for limit, size in SIZE_BY_OPEN_ROLES if n <= limit), "large")
    if r.site == "hackernews":
        return "startup"  # "Who is hiring?" posts are overwhelmingly startups
    return "unknown"


def market_demand(rows: list[JobRow]) -> dict[str, float]:
    """Skill → demand 0.3–1.0 from how often the open jobs matching the user ask for it.
    Empty (the scorer keeps its built-in table) when there are too few jobs to say."""
    from collections import Counter

    if len(rows) < MIN_CORPUS_FOR_DEMAND:
        return {}
    counts = Counter(s.lower() for r in rows for s in set(job_fields(r)["required_skills"]))
    if not counts:
        return {}
    top = counts.most_common(1)[0][1]
    return {skill: round(0.3 + 0.7 * n / top, 3) for skill, n in counts.items()}


def pool_medians(rows: list[JobRow]) -> dict[str, int]:
    """Typical expected offer per country among the user's matching jobs (pay reference)."""
    from careeros.jobs.geo import countries_in
    from careeros.jobs.scoring.signals import market_medians, offer_usd

    pairs = []
    for r in rows:
        f = job_fields(r)
        pairs.append(([c for c, _ in countries_in(r.location)],
                      offer_usd(f["salary_min"], f["salary_max"], f["salary_currency"])))
    return market_medians(pairs)


def demand_signature(demand: dict[str, float]) -> str:
    """Coarse view of the market for the profile fingerprint: a real shift rescores, noise doesn't."""
    top = sorted(demand.items(), key=lambda kv: -kv[1])[:15]
    return ",".join(f"{k}:{round(v * 10) / 10}" for k, v in top)


def remote_regions(r: JobRow, facts: Optional[dict]) -> list[str]:
    from careeros.jobs.geo import open_to

    regions = [x for x in ((facts or {}).get("remote_regions") or []) if isinstance(x, str)]
    return regions or open_to(r.description) or ([r.remote_region] if r.remote_region else [])


def to_scoring_input(rows: list[JobRow], open_counts: Optional[dict[str, int]] = None,
                     preferred_countries: Optional[list[str]] = None,
                     now: Optional[datetime] = None,
                     market_medians: Optional[dict[str, int]] = None) -> tuple[list[Job], dict[str, dict]]:
    """Stored job rows → (Job objects to score, per-URL metadata the Job type doesn't carry)."""
    from careeros.jobs.geo import location_match
    from careeros.jobs.trust import assess

    open_counts = open_counts or {}
    jobs, meta = [], {}
    for r in rows:
        f = job_fields(r)
        regions = remote_regions(r, current_facts(r))
        where = location_match(r.location, regions, preferred_countries or [], f["remote"])
        trust = assess(company=r.company or "", description=r.description or r.full_description or "",
                       ats=r.ats, company_domain=r.company_domain,
                       salary_stated=bool(f["salary_min"] or f["salary_max"]), posted_at=r.posted_at, now=now)
        size = company_size_of(r, open_counts)
        from careeros.jobs.scoring.signals import build_signals

        signals = build_signals(
            title=r.title or "", fields=f, regions=regions, location=r.location or "",
            description=r.description or r.full_description or "", discovered_at=r.discovered_at,
            posted_at=r.posted_at, company_size=size, trust=trust, market_medians=market_medians or {},
            now=now, seniority=(current_facts(r) or {}).get("seniority"))
        jobs.append(Job(
            id=r.url,
            title=r.title or "",
            company=r.company or "",
            description=r.description or r.full_description or "",
            url=r.url,
            location=r.location or "",
            remote=f["remote"],
            hybrid=f["hybrid"],
            required_skills=f["required_skills"],
            preferred_skills=f["preferred_skills"],
            required_years=f["required_years"],
            salary_min=f["salary_min"],
            salary_max=f["salary_max"],
            salary_currency=f["salary_currency"],
            company_size=size,
            sponsors_visa=f["sponsors_visa"],
            source=r.source or "unknown",
            trust=trust.level,
            location_match=where,
            signals=signals,
        ))
        meta[r.url] = {
            "title": r.title or "",
            "company": r.company or "",
            "location": r.location or "",
            "remote": f["remote"],
            "workplace": f["workplace"],
            "remote_region": f["remote_region"],
            "sponsors_visa": f["sponsors_visa"],
            "salary_min": f["salary_min"],
            "salary_max": f["salary_max"],
            "salary_currency": f["salary_currency"],
            "required_skills": f["required_skills"],
            "preferred_skills": f["preferred_skills"],
            "source": r.ats or r.site or r.source or "unknown",
            "company_key": r.company_key,
            "application_url": r.application_url or r.url,
            "posted_at": r.posted_at.isoformat() if r.posted_at else None,
            "summary": f["summary"],
            "extracted_by": f["extracted_by"],
            "remote_regions": regions[:40],
            "location_match": where,
            "trust": trust.to_dict(),
            "company_size": size,
            "company_domain": r.company_domain,
        }
    return jobs, meta


def run_scan(job: BackgroundJob, user_id: str, hours: int = ALL_TIME_HOURS, limit: int = 500) -> None:
    """Background task: pick → score what changed → upsert. Fills `job` with progress and a summary."""
    from careeros.jobs.repositories.career_score_repo import CareerScoreRepository
    from careeros.jobs.scoring_service import ScoringService

    try:
        job.update(status="profile", progress=10)
        job.log("Loading your profile…")
        profile = load_profile(user_id)
        if profile is None:
            job.update(status="failed", error="No profile found — complete onboarding first.")
            return
        job.log(f"✓ Profile: {len(profile.skills)} skills, {profile.years_experience}y")
        service = ScoringService(user_id=user_id)
        weights = load_weights(user_id)
        from careeros.jobs.scoring.signals import seeker_for

        profile.seeker = seeker_for(profile, weights)

        job.update(status="scanning", progress=30)
        job.log("Picking open jobs that match your roles…")
        with db.session_scope() as s:
            urls = candidate_urls(s, user_id, hours)
            known = CareerScoreRepository(s).input_hashes(user_id)
            loaded = []
            for i in range(0, len(urls), 500):
                loaded += s.query(JobRow).filter(JobRow.url.in_(urls[i:i + 500])).all()
            order = {u: i for i, u in enumerate(urls)}
            loaded.sort(key=lambda r: order[r.url])
            open_counts = company_open_counts(s)
            demand = market_demand(loaded)
            medians = pool_medians(loaded)
            # The market (what these jobs ask for) is part of what a score depends on
            fingerprint = profile_fingerprint(profile, {**service.load_prefs(), "_market": demand_signature(demand)},
                                              weights)
            rows, hashes, unchanged = pick_changed(loaded, known, fingerprint, limit)
            s.expunge_all()
        job.log(f"✓ {len(urls)} matching open jobs · {len(rows)} to score · {unchanged} unchanged")

        job.update(status="scoring", progress=60)
        if rows:
            job.log("Scoring against your career graph…")
            jobs, meta = to_scoring_input(rows, open_counts, profile.preferences.preferred_locations,
                                          market_medians=medians)
            service.set_market_demand(demand)
            result = service.run_pipeline(jobs, profile, weights=weights, semantic=False, job_meta=meta,
                                          input_hashes=hashes)
        else:
            result = {"total_jobs": 0, "scored": 0, "saved_to_db": 0, "apply": 0, "consider": 0, "skip": 0}
        result.update(matching=len(urls), unchanged=unchanged)

        job.update(status="completed", progress=100, result=result)
        job.log(
            f"✓ Done — {result.get('apply', 0)} APPLY · "
            f"{result.get('consider', 0)} CONSIDER · "
            f"{result.get('skip', 0)} SKIP"
        )
    except Exception as e:
        logger.exception("Scan failed for %s", user_id)
        job.fail(e)
