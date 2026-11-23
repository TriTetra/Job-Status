"""P0 fixes: decision reaches the client, decisions create applications, real preferences
and weights in scoring, briefing skips acted-on jobs, market counts every mention."""

from datetime import datetime
from types import SimpleNamespace

import pytest

from careeros.identity.domain.profile import UserProfile
from careeros.jobs import scan


# ── scoring inputs ────────────────────────────────────────────────────────

def _profile():
    return UserProfile(name="A", email="", years_experience=5, skills=[])


def test_no_saved_preferences_accepts_every_work_style_and_no_visa():
    p = _profile()
    scan.apply_preferences(p, None)
    prefs = p.preferences
    assert (prefs.remote, prefs.hybrid_acceptable, prefs.onsite_acceptable, prefs.work_visa_required) == (
        True, True, True, False)


@pytest.mark.parametrize("arrangements, expected", [
    (["remote"], (True, False, False)),
    (["hybrid"], (False, True, False)),
    (["remote", "onsite"], (True, False, True)),
    ([], (True, True, True)),          # nothing chosen = any
])
def test_saved_arrangements_map_to_scorer_preferences(arrangements, expected):
    p = _profile()
    scan.apply_preferences(p, (True, arrangements, ["DE", "NL"], 70000, None))
    prefs = p.preferences
    assert (prefs.remote, prefs.hybrid_acceptable, prefs.onsite_acceptable) == expected
    assert prefs.work_visa_required is True
    assert prefs.preferred_locations == ["DE", "NL"] and prefs.min_salary == 70000


def test_weights_are_normalised_and_bad_input_falls_back_to_defaults():
    # v8 value weights: scaled to sum to 1, effort (1–3) kept and clamped
    assert scan.normalize_weights({"pay": 3, "growth": 1, "stability": 0, "work_style": 0, "effort": 5}) == {
        "pay": 0.75, "growth": 0.25, "stability": 0.0, "work_style": 0.0, "effort": 3.0}
    defaults = scan.normalize_weights({})
    assert abs(sum(v for k, v in defaults.items() if k != "effort") - 1) < 1e-3 and defaults["effort"] == 2.0
    # old (v7) keys are ignored, not misread
    assert scan.normalize_weights({"fit": 1, "acceptance": 1})["pay"] == defaults["pay"]
    assert scan.normalize_weights({"pay": 0, "growth": 0, "stability": 0, "work_style": 0})["pay"] == 0.35
    assert scan.normalize_weights({"pay": -1, "growth": "x" == "y"})["stability"] > 0  # negatives / junk can't zero it


def test_weights_change_the_fingerprint_so_jobs_get_rescored():
    p = _profile()
    a = scan.profile_fingerprint(p, {}, {"fit": 0.5, "acceptance": 0.5})
    b = scan.profile_fingerprint(p, {}, {"fit": 0.9, "acceptance": 0.1})
    assert a != b


def test_weights_change_the_score():
    from careeros.jobs.domain.job import Job
    from careeros.jobs.scoring.opportunity_scorer import OpportunityScorer

    p = _profile()
    scan.apply_preferences(p, None)
    job = Job(id="j", title="Backend", company="X", description="", url="j", required_skills=["Go"])
    scorer = OpportunityScorer()
    fit_heavy = scorer.score(job, p, weights={"fit": 1, "acceptance": 0, "career_value": 0, "market_demand": 0})
    acc_heavy = scorer.score(job, p, weights={"fit": 0, "acceptance": 1, "career_value": 0, "market_demand": 0})
    assert fit_heavy.career_score != acc_heavy.career_score


@pytest.mark.parametrize("arrangements, job_kind, penalised", [
    (["remote"], "onsite", True),
    (["remote"], "hybrid", True),
    (["remote", "hybrid"], "hybrid", False),
    (["remote", "hybrid"], "onsite", True),
    (["onsite"], "onsite", False),
])
def test_office_penalty_follows_saved_arrangements(arrangements, job_kind, penalised):
    from careeros.jobs.domain.job import Job
    from careeros.jobs.scoring.opportunity_scorer import OpportunityScorer

    p = _profile()
    scan.apply_preferences(p, (False, arrangements, [], None, None))
    office = Job(id="o", title="Backend", company="X", description="", url="o", hybrid=job_kind == "hybrid")
    p_ok = _profile()
    scan.apply_preferences(p_ok, (False, ["onsite", "hybrid"], [], None, None))
    scorer = OpportunityScorer()
    mine = scorer._estimate_acceptance(office, p)
    reference = scorer._estimate_acceptance(office, p_ok)
    assert (mine < reference * 0.5) is penalised


# ── decision reaches the client ───────────────────────────────────────────

def test_job_list_carries_the_decision():
    from apps.api.app.routers.jobs import _serialize

    decision = {"v": 1, "semantic": {"tier": "strong", "label": "Strong match"}, "criteria": []}
    row = SimpleNamespace(url="u", career_score=80.0, fit_score=0.8, acceptance_probability=0.4, career_value=0.6,
                          market_demand=0.5, expected_value=10.0, recommendation="APPLY - strong",
                          skill_gaps=[], explanation={"decision": decision}, scanned_at=None)
    out = _serialize(row)
    assert out.decision == decision and out.recommendation == "APPLY"
    assert _serialize(SimpleNamespace(**{**vars(row), "explanation": {}})).decision is None


# ── decisions create the application row ──────────────────────────────────

class _Repo:
    rows: dict = {}

    def __init__(self, session):
        pass

    def upsert(self, url, title, company=None, status="to_apply", user_id="default", notes=None):
        return self.rows.setdefault(url, SimpleNamespace(url=url, title=title, company=company, status=status,
                                                         updated_at=datetime(2026, 11, 22)))

    def mark_applied(self, url, user_id="default"):
        self.rows[url].status = "applied"
        return self.rows[url]

    def advance_status(self, url, new_status, notes=None, user_id="default"):
        self.rows[url].status = new_status
        return self.rows[url]


def test_decision_creates_the_application_from_the_posting(monkeypatch):
    from careeros.jobs import opportunities

    _Repo.rows = {}
    monkeypatch.setattr(opportunities, "ApplicationRepository", _Repo)
    session = SimpleNamespace(get=lambda model, url: SimpleNamespace(title="Backend Engineer", company="Stripe"))

    out = opportunities.record_decision(session, "u1", "https://jobs/1", "to_apply")
    assert out["status"] == "shortlisted"
    assert (_Repo.rows["https://jobs/1"].title, _Repo.rows["https://jobs/1"].company) == ("Backend Engineer", "Stripe")

    assert opportunities.record_decision(session, "u1", "https://jobs/1", "skipped")["status"] == "skipped"
    assert opportunities.record_decision(session, "u1", "https://jobs/1", "applied")["status"] == "applied"


def test_decision_rejects_unknown_jobs_and_statuses():
    from careeros.jobs import opportunities

    session = SimpleNamespace(get=lambda model, url: None)
    with pytest.raises(opportunities.UnknownJob):
        opportunities.record_decision(session, "u1", "https://gone", "to_apply")
    with pytest.raises(ValueError):
        opportunities.record_decision(session, "u1", "https://x", "interview")


# ── market ────────────────────────────────────────────────────────────────

def test_record_mentions_keeps_one_name_per_mention():
    from careeros.market.sources import skill_registry

    added = []

    class _Result:
        def scalars(self):
            return self

        def all(self):
            return []

    session = SimpleNamespace(execute=lambda stmt: _Result(), add=added.append, flush=lambda: None)
    names = skill_registry.record_mentions(session, ["Python", "Go", "Python", "python", "Rust"])
    assert names.count("Python") == 3 and len(names) == 5
    assert {s.name: s.mention_count for s in added} == {"Python": 3, "Go": 1, "Rust": 1}  # every mention counts


@pytest.mark.parametrize("fn, value, expected", [
    ("volume_impact", 600, "high"), ("volume_impact", 200, "medium"), ("volume_impact", 40, "low"),
    ("skill_impact", 55, "high"), ("skill_impact", 12, "medium"), ("skill_impact", 3, "low"),
    ("company_impact", 4, "high"), ("company_impact", 2, "medium"), ("company_impact", 1, "low"),
])
def test_market_impact_bands_include_low(fn, value, expected):
    from careeros.market.sources.hackernews import signal_extractor

    assert getattr(signal_extractor, fn)(value) == expected


# ── briefing headline ─────────────────────────────────────────────────────

def test_briefing_puts_apply_before_a_higher_consider_and_skips_acted_on(monkeypatch):
    from careeros.briefing import facts

    rows = [SimpleNamespace(url="nuro", career_score=63.0, recommendation="CONSIDER", skill_gaps=[], explanation={}),
            SimpleNamespace(url="cohere", career_score=59.4, recommendation="APPLY - strong", skill_gaps=[], explanation={}),
            SimpleNamespace(url="done", career_score=70.0, recommendation="APPLY", skill_gaps=[], explanation={}),
            SimpleNamespace(url="rivian", career_score=57.0, recommendation="APPLY", skill_gaps=[], explanation={})]

    class Repo:
        def __init__(self, session):
            pass

        def get_top_opportunities(self, **kwargs):
            return rows

    class Q:
        def filter(self, *a):
            return self

        def all(self):
            return [("done",)]

    monkeypatch.setattr(facts, "CareerScoreRepository", Repo)
    out = facts._top_opportunities(SimpleNamespace(query=lambda *a: Q()), "u1")
    assert [o["url"] for o in out] == ["cohere", "rivian"]
