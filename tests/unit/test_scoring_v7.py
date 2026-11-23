"""Scoring v7: location, trust, company size, currencies, demand from the corpus, logos for small companies."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from careeros.identity.domain.profile import UserPreferences, UserProfile
from careeros.jobs import geo, scan
from careeros.jobs.domain.job import Job
from careeros.jobs.scoring.opportunity_scorer import OpportunityScorer
from careeros.jobs.trust import assess
from careeros.shared.money import to_usd_year

NOW = datetime(2026, 11, 23, tzinfo=timezone.utc)


# ── geo ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("location, regions, remote, preferred, expected", [
    ("İstanbul, Türkiye", [], False, ["TR"], True),
    ("Berlin", [], False, ["GB", "DE"], True),                         # city without its country
    ("Austin, TX", [], False, ["DE"], False),
    ("Remote: 76 countries (Albania, …)", ["Albania", "Germany", "Turkey"], True, ["TR"], True),
    ("Remote", ["United States"], True, ["TR", "DE"], False),
    ("Remote", ["Europe"], True, ["NL"], True),
    ("Remote", ["EMEA"], True, ["TR"], True),                          # EMEA includes Turkey, Europe doesn't
    ("Remote", ["Europe"], True, ["TR"], False),
    ("Remote: anywhere", ["Worldwide"], True, ["TR"], True),
    ("Somewhere", [], False, ["TR"], None),
    ("Berlin, Germany", [], False, [], None),                          # no targets: can't judge
])
def test_location_match(location, regions, remote, preferred, expected):
    assert geo.location_match(location, regions, preferred, remote) is expected


def test_open_to_list_is_read_from_the_description():
    assert geo.open_to("Open to candidates in: Germany, Turkey, Spain.\n\nAbout us") == ["Germany", "Turkey", "Spain"]


# ── trust ────────────────────────────────────────────────────────────────

def _assess(**kw):
    base = dict(company="Acme AI", description="We build models.", ats="ashby", company_domain="acme.ai",
                salary_stated=True, posted_at=NOW - timedelta(days=5), now=NOW)
    return assess(**{**base, **kw})


def test_employer_board_with_nothing_odd_is_verified():
    t = _assess()
    assert t.level == "verified" and not t.agency and len(t.good) == 4


def test_agency_by_name_or_wording():
    assert _assess(company="headhunter.digital / Recruiting für IT", ats=None).agency
    t = _assess(company="Talentful", description="On behalf of our client, a fintech in Berlin, we are hiring…", ats=None)
    assert t.agency and t.level == "caution"
    assert _assess(company="X", description="Müşterimiz için Python geliştirici arıyoruz", ats=None).agency


def test_stale_posting_and_personal_email_are_cautions():
    assert "months" in " ".join(_assess(posted_at=NOW - timedelta(days=200)).concerns)
    assert _assess(description="Send your CV to hiring.acme@gmail.com").level == "caution"


@pytest.mark.parametrize("text", [
    "Message us on WhatsApp to apply today",
    "A small training fee of $50 is required. Pay the registration fee to start.",
    "Earn $300 per day from home",
    "Become a crypto trader and invest with us",
])
def test_scam_signs_are_risk(text):
    t = _assess(description=text, ats=None)
    assert t.level == "risk" and t.concerns


# ── money ────────────────────────────────────────────────────────────────

def test_currency_conversion():
    assert to_usd_year(100_000, "USD") == 100_000
    assert to_usd_year(70_000, "EUR") == 75_600
    assert to_usd_year(100_000, "TRY", "month") == 34_800
    assert to_usd_year(50_000, "XYZ") is None and to_usd_year(None, "USD") is None


# ── scorer ───────────────────────────────────────────────────────────────

def _user(**prefs):
    p = UserPreferences(remote=True, hybrid_acceptable=True, onsite_acceptable=True, work_visa_required=False)
    for k, v in prefs.items():
        setattr(p, k, v)
    return UserProfile(name="A", email="a@x", years_experience=5, preferences=p)


def _job(**kw):
    base = dict(id="j", title="ML Engineer", company="Acme", description="", url="j", remote=True,
                required_years=5, company_size="startup", trust="verified")
    return Job(**{**base, **kw})


def test_location_and_trust_move_the_chance():
    s, u = OpportunityScorer(), _user(preferred_locations=["TR"])
    inside = s._estimate_acceptance(_job(location_match=True), u)
    outside = s._estimate_acceptance(_job(location_match=False), u)
    risky = s._estimate_acceptance(_job(location_match=True, trust="risk"), u)
    assert inside > outside * 2 and risky < inside * 0.3


def test_risky_postings_are_skipped():
    rec = OpportunityScorer().score(_job(trust="risk"), _user()).recommendation
    assert rec.startswith("SKIP") and "warning" in rec


def test_salary_is_compared_in_usd_against_the_users_minimum():
    s = OpportunityScorer()
    u = _user(min_salary=60_000, salary_currency="EUR")       # ≈ $64.8k
    above = s._calculate_career_value(_job(salary_min=90_000, salary_currency="EUR"), u)
    below = s._calculate_career_value(_job(salary_min=40_000, salary_currency="EUR"), u)
    unstated = s._calculate_career_value(_job(), u)
    assert above > unstated > below


# ── scan inputs ──────────────────────────────────────────────────────────

def _row(**kw):
    base = dict(company_size="unknown", company_key=None, site=None, required_skills=[], llm_facts=None,
                llm_facts_hash=None, content_hash="h", remote_region=None, description="", full_description=None,
                required_years=None, remote=False, sponsors_visa=None, salary_min=None, salary_max=None,
                salary_currency=None, title="t", location="")
    return SimpleNamespace(**{**base, **kw})


def test_company_size_from_open_roles_list_or_feed():
    counts = {"tiny": 6, "mid": 120, "big": 400}
    assert scan.company_size_of(_row(company_key="tiny"), counts) == "startup"
    assert scan.company_size_of(_row(company_key="mid"), counts) == "midsize"
    assert scan.company_size_of(_row(company_key="big"), counts) == "large"
    assert scan.company_size_of(_row(company_size="big_tech", company_key="tiny"), counts) == "big_tech"
    assert scan.company_size_of(_row(site="hackernews"), counts) == "startup"
    assert scan.company_size_of(_row(site="jobicy"), counts) == "unknown"


def test_market_demand_comes_from_the_jobs_themselves():
    rows = [_row(required_skills=["Python", "PyTorch"]) for _ in range(80)] + [_row(required_skills=["Python"]) for _ in range(40)]
    demand = scan.market_demand(rows)
    assert demand["python"] == 1.0 and 0.3 < demand["pytorch"] < 1.0
    assert scan.market_demand(rows[:10]) == {}             # too few jobs: keep the built-in table


# ── logos ────────────────────────────────────────────────────────────────

def test_job_logo_uses_domain_then_only_trusted_feed_image_hosts(monkeypatch):
    from careeros.companies import logos

    fetched = []
    monkeypatch.setattr(logos, "_get_image", lambda http, url, params=None: (fetched.append((url, params)) or (b"img", "image/png")))
    logos._cache.clear()
    jobs = {
        "a": SimpleNamespace(company_key=None, company_domain="acme.ai", company_logo=None),
        "b": SimpleNamespace(company_key=None, company_domain=None, company_logo="https://cdn-images.himalayas.app/x.png"),
        "c": SimpleNamespace(company_key=None, company_domain=None, company_logo="https://evil.example/x.png"),
    }
    session = SimpleNamespace(get=lambda model, url: jobs.get(url))
    assert logos.logo_for_job(session, "a") == (b"img", "image/png") and fetched[-1][1]["domain"] == "acme.ai"
    assert logos.logo_for_job(session, "b") and fetched[-1][0].startswith("https://cdn-images.himalayas.app/")
    assert logos.logo_for_job(session, "c") is None                    # not an open proxy
    assert logos.logo_for_job(session, "missing") is None
