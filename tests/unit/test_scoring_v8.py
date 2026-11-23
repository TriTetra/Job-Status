"""Scoring v8 (chance-weighted surplus): gates, chance factors, value, ranking, inputs."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from careeros.jobs.scoring import model_v8 as m
from careeros.jobs.scoring.model_v8 import Seeker, Signals, evaluate
from careeros.jobs.scoring.signals import language_codes, languages_required, offer_usd, remote_scope


def me(**kw):
    base = dict(skills={"python", "pytorch", "kubernetes", "go"}, years=5, target_roles=["Machine Learning Engineer"],
                residence="TR", languages={"en", "tr"}, needs_sponsorship=True)
    return Seeker(**{**base, **kw})


def job(**kw):
    base = dict(title="Machine Learning Engineer", must=["python", "pytorch", "kubernetes"], nice=["go"],
                required_years=4, remote=True, regions=["Worldwide"], remote_scope="worldwide", age_days=2,
                company_size="startup", trust="verified", offer_usd=90_000, market_median_usd=80_000)
    return Signals(**{**base, **kw})


# ── the pieces ───────────────────────────────────────────────────────────

def test_skill_curve_has_no_cliff_and_favours_the_first_requirements():
    full, _, _ = m.skill_match(["a", "b", "c", "d"], [], {"a", "b", "c", "d"})
    half_first, _, _ = m.skill_match(["a", "b", "c", "d"], [], {"a", "b"})
    half_last, _, _ = m.skill_match(["a", "b", "c", "d"], [], {"c", "d"})
    none, _, _ = m.skill_match(["a", "b", "c", "d"], [], set())
    assert full > 0.9 and none < 0.01
    assert half_first > half_last          # earlier = more important
    assert 0.2 < half_first < 0.6          # smooth, not a 60% cliff


def test_title_family():
    assert m.title_match("Senior Machine Learning Engineer", ["Machine Learning Engineer"]) == 1.0
    assert m.title_match("ML Platform Engineer", ["Machine Learning Engineer"]) == 1.0   # ML = machine learning
    assert m.title_match("Data Engineer", ["Machine Learning Engineer"]) == 0.4          # near family
    assert m.title_match("Applied Scientist", ["Machine Learning Engineer"]) == 0.6      # same family
    assert m.title_match("Python Developer", ["Backend Engineer"]) == 0.6
    # sharing only "Engineer" doesn't make roles related
    assert m.title_match("Cryogenics Engineer", ["Backend Engineer", "ML Engineer"]) == 0.25
    assert m.title_match("Mechanical Engineer", ["Software Engineer"]) == 0.25
    assert m.title_match("Kıdemli Yazılım Geliştirici", ["Software Engineer"]) == 1.0  # Turkish title, same family
    assert m.title_match("Account Executive", ["Machine Learning Engineer"]) == 0.25


def test_under_qualification_costs_per_year_and_big_overshoot_is_a_flight_risk():
    short, note = m.qualification(job(required_years=8, title="Engineer"), me(years=5))
    assert short == pytest.approx(0.75 ** 3) and "short" in note
    over, _ = m.qualification(job(required_years=0, title="Junior Engineer"), me(years=10))
    assert over == 0.7
    assert m.qualification(job(required_years=4, title="Engineer"), me(years=5))[0] == 1.0


def test_age_timing_and_ghost_risk():
    assert m.timing(3) == 1.0 and m.timing(13) == pytest.approx(0.88 ** 9) and m.timing(90) == 0.3
    assert m.p_real(5, False) == 0.9 and m.p_real(200, False) == 0.3 and m.p_real(5, True) == 0.45


def test_competition_by_remote_scope_and_fame():
    assert m.competition(job(remote_scope="worldwide")) == 0.27
    assert m.competition(job(remote_scope="region")) == 0.42
    assert m.competition(job(remote=False, remote_scope=None)) == 1.0
    assert m.competition(job(remote=False, remote_scope=None, company_size="big_tech")) == 0.6


@pytest.mark.parametrize("country, extra, expected", [
    ("TR", {}, 1.0),                                              # home
    ("DE", {"offer_usd": 60_000}, 0.7),                           # Blue Card shortage route
    ("DE", {"offer_usd": 40_000}, 0.3),                           # below the Blue Card floor
    ("GB", {"sponsors_visa": True, "offer_usd": 70_000}, 0.8),
    ("GB", {"offer_usd": 70_000}, 0.25),                          # silent on sponsorship
    ("CH", {}, 0.05),                                             # small company, priority test
    ("CH", {"relocation": True}, 0.35),
    ("US", {}, 0.08),
])
def test_relocation_markets_for_someone_in_turkey(country, extra, expected):
    gates = []
    assert m.market(job(remote=False, regions=[], remote_scope=None, countries=[country], **extra), me(), gates)[0] == expected
    assert gates == []


def test_market_gates_and_remote_eligibility():
    gates = []
    m.market(job(remote=False, regions=[], remote_scope=None, countries=["GB"], offer_usd=40_000), me(), gates)
    assert "UK sponsorship floor" in gates[0]
    gates = []
    m.market(job(remote=False, regions=[], remote_scope=None, countries=["DE"], sponsors_visa=False), me(), gates)
    assert gates == ["States no visa sponsorship"]
    assert m.market(job(regions=["EMEA"], remote_scope="region"), me(), [])[0] == 0.6        # EMEA includes Turkey
    assert m.market(job(regions=["United States"], remote_scope="country"), me(), [])[0] == 0.1
    assert m.market(job(remote=False, regions=[], remote_scope=None, countries=["DE"]), me(needs_sponsorship=False), [])[0] == 0.9


def test_hard_gates():
    assert "scam" in m.gates_for(job(trust="risk"), me())[0]
    assert m.gates_for(job(remote=False, hybrid=False), me(onsite_ok=False, hybrid_ok=False))
    assert "DE" in m.gates_for(job(languages_required=["de"]), me())[0]
    assert m.gates_for(job(languages_required=["de"]), me(languages=set())) == []   # languages unknown: no gate


def test_pay_is_log_with_a_steeper_loss_and_a_floor_below_your_minimum():
    assert m.pay_value(120_000, 80_000) == 1.0          # +50% = full
    assert m.pay_value(80_000, 80_000) == 0.5
    assert m.pay_value(64_000, 80_000) < 0.5 - (0.5 - m.pay_value(96_000, 80_000)) * 0.9  # losses fall faster
    v, parts = m.value(job(offer_usd=50_000), me(min_salary_usd=70_000), 1.0)
    assert v <= 0.3 and parts["below_minimum"]


# ── the whole model ──────────────────────────────────────────────────────

def test_surplus_index_prefers_a_likely_good_job_over_a_long_shot_dream():
    berlin = evaluate(job(remote=False, regions=[], remote_scope=None, countries=["DE"], offer_usd=70_000,
                          company_size="midsize", age_days=3), me())
    dream = evaluate(job(company_size="big_tech", offer_usd=250_000, age_days=10,
                         must=["python", "rust", "cuda", "triton"]), me())
    assert berlin.p_effective > dream.p_effective * 3
    assert dream.value > berlin.value          # the dream pays more…
    assert berlin.score > dream.score          # …but the likely one ranks higher


def test_gated_jobs_are_skipped_with_the_reason():
    r = evaluate(job(trust="risk"), me())
    assert r.recommendation.startswith("SKIP - Posting shows scam") and r.p_interview == 0 and r.score <= 10


def test_effort_raises_the_bar_for_long_shots():
    long_shot = job(must=["python", "rust", "cuda", "triton"], regions=["Turkey"], remote_scope="country")
    quick = evaluate(long_shot, me(effort="quick")).score
    tailored = evaluate(long_shot, me(effort="tailored")).score
    assert quick > tailored


def test_explanation_is_serialisable_and_versioned():
    import json

    d = evaluate(job(), me()).explain()
    assert d["v"] == 8 and json.dumps(d)
    assert {"skills", "title", "experience", "timing", "competition", "location"} <= set(d["chance_factors"])


# ── inputs ───────────────────────────────────────────────────────────────

def test_languages():
    assert language_codes([{"code": "English", "level": "C1"}, {"code": "German", "level": "A2"},
                           {"code": "Turkish", "level": "Native"}]) == {"en", "tr"}
    assert languages_required("Fluent German is required for client meetings.", "") == ["de"]
    assert languages_required("Sehr gute Deutschkenntnisse (C1) zwingend erforderlich", "") == ["de"]
    assert languages_required("Wir suchen dich für unser Team und die Aufgaben mit Kunden bei uns", "x") == ["de"]
    assert languages_required("We work in English. Spanish is a plus.", "") == []


def test_offer_and_remote_scope():
    assert offer_usd(60_000, 90_000, "EUR") == int(60_000 * 1.08 + (90_000 * 1.08 - 60_000 * 1.08) / 3)
    assert offer_usd(None, None, "USD") is None
    assert remote_scope(True, ["Worldwide"], "") == "worldwide"
    assert remote_scope(True, ["Europe"], "") == "region"
    assert remote_scope(True, ["Germany"], "") == "country"
    assert remote_scope(False, ["Germany"], "") is None


def test_scan_builds_signals_and_seeker(monkeypatch):
    from careeros.identity.domain.profile import Skill, SkillLevel, UserPreferences, UserProfile
    from careeros.jobs.scoring.signals import build_signals, seeker_for
    from careeros.jobs.trust import Trust

    now = datetime(2026, 11, 23, tzinfo=timezone.utc)
    sig = build_signals(title="ML Engineer", fields={"required_skills": ["Python"], "preferred_skills": [], "remote": False,
                                                     "hybrid": True, "salary_min": 70_000, "salary_max": 90_000,
                                                     "salary_currency": "EUR", "required_years": 3, "sponsors_visa": None},
                        regions=[], location="Berlin, Germany", description="Visa sponsorship available. Relocation support.",
                        discovered_at=now - timedelta(days=10), posted_at=now - timedelta(days=40), company_size="midsize",
                        trust=Trust("verified"), market_medians={"DE": 75_000}, now=now)
    assert sig.countries == ["DE"] and sig.age_days == 40 and sig.sponsors_visa is True and sig.relocation
    assert sig.market_median_usd == 75_000 and sig.must == ["python"]

    p = UserPreferences(remote=True, hybrid_acceptable=True, onsite_acceptable=False, work_visa_required=True,
                        min_salary=60_000, salary_currency="EUR", residence_country="TR", languages=["en"])
    prof = UserProfile(name="A", email="a@x", years_experience=4, skills=[Skill("Python", SkillLevel.ADVANCED)],
                       preferences=p, target_roles=["ML Engineer"])
    s = seeker_for(prof, {"pay": 0.5, "growth": 0.2, "stability": 0.2, "work_style": 0.1, "effort": 3})
    assert s.effort == "tailored" and s.residence == "TR" and s.min_salary_usd == 64_800 and "python" in s.skills
    assert not s.onsite_ok and s.needs_sponsorship
    assert SimpleNamespace  # keep import used
