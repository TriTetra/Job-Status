"""Fix pack A (live test findings): locations, on-site vs hybrid, implied skills, the deeper-read prompt."""

import pytest

from careeros.jobs import decision_builder as db
from careeros.jobs.geo import countries_in
from careeros.jobs.scoring import model_v8 as m
from careeros.jobs.scoring.model_v8 import Seeker, Signals, evaluate
from careeros.knowledge.skill_names import canonical, implied_by, with_implied


def codes(text):
    return [c for c, _ in countries_in(text)]


# ── where a job is ───────────────────────────────────────────────────────

@pytest.mark.parametrize("text, expected", [
    ("Santa Clara, California, USA", ["US"]),
    ("Mountain View, California (Hybrid)", ["US"]),
    ("Bangalore, IND", ["IN"]),
    ("Nieuwegein", ["NL"]),
    ("London, UK", ["GB"]),
    ("Remote - US", ["US"]),
    ("Indianapolis, Indiana", ["US"]),        # not India
    ("Atlanta, Georgia", ["US"]),             # the state, not the country
    ("Tbilisi, Georgia", ["GE"]),
    ("Poland, Gdansk", ["PL"]),
    ("Hybrid - Munich, Germany; Remote US", ["DE", "US"]),
    ("Remote: EMEA", []),
])
def test_locations_are_recognised(text, expected):
    assert codes(text) == expected


def test_short_codes_only_count_in_capitals():
    assert codes("Come join us in Berlin") == ["DE"]   # "us" is a word here, not a country


def me(**kw):
    base = dict(skills={"python", "pytorch", "go", "rust"}, years=3, target_roles=["AI Engineer"], residence="UZ",
                languages={"en", "tr", "uz"}, needs_sponsorship=True, remote_ok=True, hybrid_ok=True, onsite_ok=False)
    return Seeker(**{**base, **kw})


def job(**kw):
    base = dict(title="AI Engineer", must=["python", "pytorch"], nice=[], required_years=2, remote=False,
                regions=[], countries=[], age_days=3, company_size="large", trust="verified", offer_usd=150_000)
    return Signals(**{**base, **kw})


def test_an_unknown_location_is_not_a_free_pass_when_you_need_a_visa():
    assert m.market(job(), me(), []) == (0.4, "Location unclear: check where it's based")
    assert m.market(job(), me(needs_sponsorship=False), [])[0] == 0.8
    assert m.market(job(), me(residence=None), [])[0] == 1.0


def test_us_onsite_for_someone_in_uzbekistan_ranks_far_below_before():
    # live case: Zscaler, Santa Clara — was location ×1.0 (country not recognised), score 87
    us = evaluate(job(countries=["US"], workplace="hybrid", hybrid=True), me())
    assert us.explain()["chance_factors"]["location"] == 0.08
    unknown_country = evaluate(job(countries=[], workplace="hybrid", hybrid=True), me())
    assert us.score < unknown_country.score


# ── on-site vs hybrid ────────────────────────────────────────────────────

def test_onsite_is_ruled_out_when_you_accept_hybrid_but_not_onsite():
    assert m.gates_for(job(workplace="onsite"), me()) == ["On-site role; you want remote or hybrid"]
    assert m.gates_for(job(workplace="hybrid", hybrid=True), me()) == []
    assert m.gates_for(job(workplace=None), me()) == []                       # not stated: kept, valued lower
    assert m.gates_for(job(workplace=None), me(hybrid_ok=False)) == ["Not remote; you only want remote"]
    assert m.gates_for(job(workplace="onsite"), me(onsite_ok=True)) == []


def test_work_style_value_by_what_the_posting_says():
    assert m.value(job(workplace="onsite"), me(onsite_ok=True), 1.0)[1]["work_style"] == 1.0
    assert m.value(job(workplace=None), me(), 1.0)[1]["work_style"] == 0.6
    assert m.value(job(workplace="hybrid", hybrid=True), me(), 1.0)[1]["work_style"] == 1.0


@pytest.mark.parametrize("workplace, wanted, state, detail_has", [
    ("onsite", ["remote", "hybrid"], "conflict", "On-site every day"),
    ("onsite", ["onsite"], "confirmed", "On-site"),
    ("hybrid", ["remote", "hybrid"], "confirmed", "Hybrid"),
    ("hybrid", ["remote"], "conflict", "remote-only"),
    (None, ["remote", "hybrid"], "unknown", "isn't stated"),
])
def test_work_style_criterion(workplace, wanted, state, detail_has):
    c = db.build_criteria({"remote": False, "workplace": workplace, "hybrid": workplace == "hybrid"},
                          {"work_arrangements": wanted})[0]
    assert c["state"] == state and detail_has in c["detail"]


def test_location_criterion_quotes_an_unrecognised_place():
    c = db._location_criterion({"remote": False, "location": "Somewhereville"}, ["GB"])
    assert c["state"] == "unknown" and "Somewhereville" in c["detail"]


# ── skills ───────────────────────────────────────────────────────────────

def test_skill_spelling_variants():
    assert canonical("RESTful APIs") == "REST API"
    assert canonical("Git/GitHub") == "Git"
    assert canonical("HuggingFace") == "Hugging Face"


def test_evidence_implies_broader_skills():
    got = implied_by(["PyTorch", "LLM Agents", "K3s", "YOLOv8"])
    assert {"deep learning", "machine learning", "llm", "kubernetes", "docker", "computer vision"} <= set(got)
    assert got["llm"] == "llm agents"
    assert "pytorch" not in with_implied({"deep learning"})   # never the other way round


def test_profile_gets_implied_skills_at_a_slightly_lower_level():
    from careeros.jobs.scan import implied_skills

    skills = implied_skills([{"skill_name": "LLM Agents", "aggregated_confidence": 0.8},
                             {"skill_name": "PyTorch", "aggregated_confidence": 0.97}])
    names = {s.name for s in skills}
    assert {"LLM", "Deep Learning", "Machine Learning"} <= names


# ── the deeper read ──────────────────────────────────────────────────────

def test_deeper_read_gets_the_raw_facts_of_both_sides():
    ex = {"title": "Staff Engineer", "company": "Zscaler", "location": "Santa Clara, California, USA",
          "remote": False, "workplace": "onsite", "salary_min": 152000, "salary_max": 190000, "salary_currency": "USD",
          "model": {"score": 86.9, "p_effective": 0.0107, "chance_factors": {"experience_note": "2 year(s) short of the 5 asked"}}}
    decision = {"semantic": {"label": "Strong"}, "criteria": [{"label": "Work style", "state": "conflict", "detail": "x"}]}
    person = {"country": "Uzbekistan", "requires_sponsorship": True, "work_arrangements": ["remote", "hybrid"],
              "preferred_country_codes": ["GB", "PL"], "years": 3, "level": "mid", "salary_min": 40000,
              "salary_currency": "EUR"}
    p = db.reasoning_prompt(ex, decision, [{"name": "Python"}], ["AWS"], person)
    for must in ("Santa Clara, California, USA (countries: US)", "Workplace: onsite", "Lives in: Uzbekistan",
                 "needs visa sponsorship: yes", "Wants to work: remote, hybrid", "2 year(s) short",
                 "chance of an interview 1.1%", "Minimum pay: 40000 EUR", "Visa sponsorship: not stated"):
        assert must in p, must
    assert "lead with that conflict" in db.REASONING_RULES
