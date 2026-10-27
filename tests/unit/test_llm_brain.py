"""Phase 3: LLM gateway (routing, budget, call log, schema), job facts, canonical skills, scoring."""

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from careeros.shared import llm as llm_mod
from careeros.shared import llm_usage
from careeros.shared.llm import CallRecord, LLMBudgetExceeded, LLMClient, LLMError
from tests.unit.test_shared_llm import FakeResponse, FakeSession


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr(llm_mod.time, "sleep", lambda s: None)


class RecordingGuard:
    def __init__(self, refuse=False):
        self.refuse, self.checks, self.records = refuse, [], []

    def check(self, task, tier, user_id):
        self.checks.append((task, tier, user_id))
        if self.refuse:
            raise LLMBudgetExceeded("budget gone")

    def record(self, call: CallRecord):
        self.records.append(call)


def _client(*responses, base="https://openrouter.ai/api/v1", **kw):
    session = FakeSession(*responses)
    return LLMClient("sk", "smart/model", base, session=session, fast_model="fast/model", **kw), session


def _ok(content="ok", usage=None):
    body = {"choices": [{"message": {"content": content}}]}
    if usage is not None:
        body["usage"] = usage
    return FakeResponse(body=body)


# ── routing ───────────────────────────────────────────────────────────────

def test_bulk_tasks_use_the_fast_model_and_overrides_win():
    client, session = _client(_ok(), _ok(), _ok(), task_models={"reasoning": "special/model"})
    client.complete("x", task="job_extract")
    client.complete("x", task="cv_extract")
    client.complete("x", task="reasoning")
    assert [c["json"]["model"] for c in session.calls] == ["fast/model", "smart/model", "special/model"]


def test_openrouter_is_asked_for_real_cost_others_are_not():
    client, session = _client(_ok())
    client.complete("x")
    assert session.calls[0]["json"]["usage"] == {"include": True}
    other, s2 = _client(_ok(), base="https://api.other.example/v1")
    other.complete("x")
    assert "usage" not in s2.calls[0]["json"]


# ── guard + call log ──────────────────────────────────────────────────────

def test_successful_call_is_recorded_with_reported_cost():
    guard = RecordingGuard()
    client, _ = _client(_ok(usage={"prompt_tokens": 1000, "completion_tokens": 200, "cost": 0.0012}), guard=guard)
    client.complete("x", task="reasoning", user_id="u1")
    assert guard.checks == [("reasoning", "interactive", "u1")]
    [rec] = guard.records
    assert (rec.status, rec.task, rec.user_id, rec.prompt_tokens, rec.completion_tokens) == ("ok", "reasoning", "u1", 1000, 200)
    assert rec.cost_usd == 0.0012 and rec.cost_estimated is False


def test_missing_cost_is_estimated_pessimistically():
    guard = RecordingGuard()
    client, _ = _client(_ok(usage={"prompt_tokens": 1_000_000, "completion_tokens": 0}), guard=guard)
    client.complete("x")
    assert guard.records[0].cost_usd == llm_mod.FALLBACK_PRICE_IN and guard.records[0].cost_estimated


def test_refused_call_never_reaches_the_api_and_is_logged():
    guard = RecordingGuard(refuse=True)
    client, session = _client(_ok(), guard=guard)
    with pytest.raises(LLMBudgetExceeded):
        client.complete("x", task="job_extract")
    assert session.calls == [] and guard.records[0].status == "budget"
    assert issubclass(LLMBudgetExceeded, LLMError)  # callers' fallbacks already catch it


def test_failed_call_is_logged_as_error():
    guard = RecordingGuard()
    client, _ = _client(FakeResponse(status=401, body={"error": "nope"}), guard=guard)
    with pytest.raises(LLMError):
        client.complete("x")
    assert guard.records[0].status == "error" and "401" in guard.records[0].error


def test_recording_failure_does_not_break_the_call():
    class Broken(RecordingGuard):
        def record(self, call):
            raise RuntimeError("db down")
    client, _ = _client(_ok("fine"), guard=Broken())
    assert client.complete("x") == "fine"


# ── schema validation ─────────────────────────────────────────────────────

def test_complete_model_retries_once_with_the_validation_error():
    from careeros.jobs.llm_extract import JobFacts

    client, session = _client(_ok('{"min_years": -3}'), _ok('{"min_years": 3, "required_skills": ["postgres"]}'))
    facts = client.complete_model("read this", JobFacts, task="job_extract")
    assert facts.min_years == 3 and facts.required_skills == ["PostgreSQL"]
    assert "previous answer was invalid" in session.calls[1]["json"]["messages"][-1]["content"]
    assert session.calls[0]["json"]["response_format"] == {"type": "json_object"}


def test_complete_model_gives_up_after_retry():
    from careeros.jobs.llm_extract import JobFacts

    client, _ = _client(_ok("not json"), _ok('{"seniority": "wizard"}'))
    with pytest.raises(LLMError, match="JobFacts"):
        client.complete_model("x", JobFacts)


# ── DbUsageGuard (DB faked) ───────────────────────────────────────────────

@pytest.fixture
def spend(monkeypatch):
    totals = {"all": 0.0, "u1": 0.0}

    @contextmanager
    def scope():
        yield object()

    import careeros.db.connection as conn
    monkeypatch.setattr(conn.db, "session_scope", scope)
    monkeypatch.setattr(llm_usage, "spent_since", lambda s, since, user_id=None: totals[user_id or "all"])
    return totals


def test_bulk_stops_at_its_share_while_interactive_continues(spend):
    guard = llm_usage.DbUsageGuard(daily_usd=1.0, user_daily_usd=0, bulk_share=0.7)
    spend["all"] = 0.75
    with pytest.raises(LLMBudgetExceeded, match="bulk"):
        guard.check("job_extract", "bulk", None)
    guard.check("reasoning", "interactive", "u1")  # still allowed
    spend["all"] = 1.0
    with pytest.raises(LLMBudgetExceeded):
        guard.check("reasoning", "interactive", "u1")


def test_per_user_budget(spend):
    guard = llm_usage.DbUsageGuard(daily_usd=10, user_daily_usd=0.5, bulk_share=0.7)
    spend["u1"] = 0.5
    with pytest.raises(LLMBudgetExceeded, match="Your daily"):
        guard.check("reasoning", "interactive", "u1")
    guard.check("job_extract", "bulk", None)  # system work isn't charged to a user


def test_no_budgets_means_no_db_lookups(monkeypatch):
    import careeros.db.connection as conn
    monkeypatch.setattr(conn.db, "session_scope", lambda: (_ for _ in ()).throw(AssertionError("queried")))
    llm_usage.DbUsageGuard(0, 0, 0.7).check("reasoning", "interactive", "u1")


# ── canonical skills ──────────────────────────────────────────────────────

def test_skill_names_are_canonical():
    from careeros.knowledge.skill_names import canonical, canonical_list, key

    assert canonical("postgres") == "PostgreSQL" and canonical("golang") == "Go" and canonical("k8s") == "Kubernetes"
    assert canonical_list(["py", "Python", "TS", " Snowflake "]) == ["Python", "TypeScript", "Snowflake"]
    assert key("JS") == key("javascript")


def test_fit_uses_canonical_names_and_counts_nice_to_haves():
    from careeros.identity.domain.profile import UserProfile
    from careeros.identity.domain.skill import Skill, SkillLevel
    from careeros.jobs.domain.job import Job
    from careeros.jobs.scoring.opportunity_scorer import OpportunityScorer

    me = UserProfile(name="A", email="", years_experience=5,
                     skills=[Skill("golang", SkillLevel.EXPERT), Skill("Postgres", SkillLevel.ADVANCED)])
    job = Job(id="j", title="Backend", company="X", description="", url="j", required_skills=["Go", "PostgreSQL"])
    assert OpportunityScorer()._simple_fit(me, job) == 1.0
    job.preferred_skills = ["Kubernetes"]
    assert OpportunityScorer()._simple_fit(me, job) == pytest.approx(0.85)
    job.preferred_skills = []
    job.required_skills = ["Go", "PostgreSQL"] + [f"Tool{i}" for i in range(10)]  # long tail of extras
    assert OpportunityScorer()._simple_fit(me, job) == pytest.approx(2 / 6)


def test_skill_gaps_are_saved_and_matched_skills_are_exact():
    from careeros.identity.domain.profile import UserProfile
    from careeros.identity.domain.skill import Skill, SkillLevel
    from careeros.jobs.domain.job import Job
    from careeros.jobs.scoring_service import ScoringService, skill_gaps

    me = UserProfile(name="A", email="", years_experience=5, skills=[Skill("Go", SkillLevel.EXPERT)])
    job = Job(id="j", title="Django Dev", company="X", description="", url="j", required_skills=["Django", "golang", "AWS"])
    assert skill_gaps([job], me) == {"j": ["Django", "AWS"]}
    opp = SimpleNamespace(job=job, career_value=0, market_demand=0, fit_score=50, acceptance_probability=20)
    matched = ScoringService.__new__(ScoringService)._build_explanation(opp, me)["matched_skills"]
    assert [m["name"] for m in matched] == ["Go"]  # "Go" is not a substring hit on "Django"


# ── facts → scoring input ─────────────────────────────────────────────────

def _row(**kw):
    from careeros.jobs.models.job import Job as JobRow
    base = dict(url="https://x/1", title="Backend Engineer", company="Acme", location="Berlin", description="…",
                content_hash="v1", required_skills=["Python"], required_years=2.0, remote=False, sponsors_visa=None,
                ats="greenhouse", source="greenhouse")
    base.update(kw)
    return JobRow(**base)


FACTS = {"required_skills": ["Go", "PostgreSQL"], "nice_to_have_skills": ["Kubernetes"], "min_years": None,
         "seniority": "senior", "workplace": "remote", "remote_regions": ["Europe"], "visa_sponsorship": "no",
         "salary_min": 90000, "salary_max": 120000, "salary_currency": "EUR", "salary_period": "year",
         "summary": "Builds payment APIs."}


def test_current_facts_replace_keyword_guesses():
    from careeros.jobs.scan import job_fields

    f = job_fields(_row(llm_facts=FACTS, llm_facts_hash="v1"))
    assert f["extracted_by"] == "llm" and f["required_skills"] == ["Go", "PostgreSQL"]
    assert f["preferred_skills"] == ["Kubernetes"] and f["required_years"] == 5.0  # from seniority
    assert f["remote"] is True and f["remote_region"] == "Europe" and f["sponsors_visa"] is False
    assert (f["salary_min"], f["salary_currency"]) == (90000, "EUR") and f["summary"] == "Builds payment APIs."


def test_stale_facts_are_ignored():
    from careeros.jobs.scan import job_fields

    f = job_fields(_row(llm_facts=FACTS, llm_facts_hash="v0"))  # posting changed since extraction
    assert f["extracted_by"] == "keywords" and f["required_skills"] == ["Python"]


def test_facts_arriving_triggers_a_rescore():
    from careeros.jobs.scan import input_hash

    assert input_hash(_row(), "fp") != input_hash(_row(llm_facts=FACTS, llm_facts_hash="v1"), "fp")


def test_job_facts_validation_cleans_model_output():
    from careeros.jobs.llm_extract import JobFacts

    f = JobFacts.model_validate({"required_skills": ["k8s", "Kubernetes", "x" * 100] + [f"S{i}" for i in range(30)],
                                 "salary_currency": " eur ", "summary": "  " + "w" * 400})
    assert f.required_skills[0] == "Kubernetes" and len(f.required_skills) == 12
    assert f.salary_currency == "EUR" and len(f.summary) == 300


# ── enrich_jobs (LLM + DB faked) ──────────────────────────────────────────

def test_enrich_stops_cleanly_when_the_budget_runs_out(monkeypatch):
    from careeros.jobs import llm_extract

    pending = [(f"u{i}", "Engineer", "Acme", "", "desc", f"h{i}") for i in range(10)]
    saved, calls = [], {"n": 0}

    def fake_extract(*a):
        calls["n"] += 1
        if calls["n"] > 3:
            raise LLMBudgetExceeded("budget gone")
        return llm_extract.JobFacts()

    monkeypatch.setattr(llm_extract, "get_llm_client", lambda: SimpleNamespace(model_for=lambda t: "fast/model"))
    monkeypatch.setattr(llm_extract, "_pending", lambda limit: pending)
    monkeypatch.setattr(llm_extract, "extract_facts", fake_extract)
    monkeypatch.setattr(llm_extract, "_save", lambda url, h, facts, model: saved.append(url))
    monkeypatch.setattr(llm_extract, "get_settings", lambda: SimpleNamespace(llm_max_concurrency=1))
    s = llm_extract.enrich_jobs(10)
    assert s.extracted == 3 and s.stopped == "budget gone" and len(saved) == 3 and s.candidates == 10


def test_enrich_without_api_key_is_a_no_op(monkeypatch):
    from careeros.jobs import llm_extract

    def missing():
        raise llm_mod.LLMNotConfiguredError("OPENROUTER_API_KEY not set")
    monkeypatch.setattr(llm_extract, "get_llm_client", missing)
    s = llm_extract.enrich_jobs(10)
    assert s.extracted == 0 and "not set" in s.stopped
