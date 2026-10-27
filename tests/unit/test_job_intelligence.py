"""careeros.jobs — scan input mapping, skill levels, opportunity query."""

import pytest
from sqlalchemy.dialects import postgresql

from careeros.jobs.repositories.career_score_repo import CareerScoreRepository
from careeros.identity.domain.skill import SkillLevel
from careeros.jobs.opportunities import DECISION_BY_APPLICATION_STATUS
from careeros.jobs.scan import skill_level_for, to_scoring_input


@pytest.mark.parametrize("conf, level", [
    (0.95, SkillLevel.EXPERT), (0.9, SkillLevel.EXPERT),
    (0.85, SkillLevel.ADVANCED), (0.8, SkillLevel.ADVANCED),
    (0.7, SkillLevel.INDEPENDENT), (0.65, SkillLevel.INDEPENDENT),
    (0.3, SkillLevel.WORKING),
])
def test_skill_level_for(conf, level):
    assert skill_level_for(conf) == level


def test_to_scoring_input_respects_limit_and_keeps_metadata():
    raw = [
        {"url": f"https://x/{i}", "title": f"T{i}", "remote_region": "Europe", "source": "linkedin",
         "required_skills": ["Python"], "required_years": 3}
        for i in range(5)
    ]
    jobs, meta = to_scoring_input(raw, limit=2)
    assert [j.url for j in jobs] == ["https://x/0", "https://x/1"]
    assert jobs[0].required_years == 3.0
    assert set(meta) == {"https://x/0", "https://x/1"}
    assert meta["https://x/0"]["remote_region"] == "Europe"
    assert meta["https://x/0"]["source"] == "linkedin"


def test_to_scoring_input_defaults():
    jobs, meta = to_scoring_input([{"url": "u"}], limit=10)
    assert jobs[0].required_years == 2.0
    assert meta["u"]["source"] == "unknown" and meta["u"]["remote"] is False


def test_rejected_and_withdrawn_count_as_skipped():
    assert DECISION_BY_APPLICATION_STATUS["rejected"] == "skipped"
    assert DECISION_BY_APPLICATION_STATUS["withdrawn"] == "skipped"
    assert DECISION_BY_APPLICATION_STATUS["interview"] == "interviewing"


class CapturingSession:
    def __init__(self):
        self.stmt = None

    def execute(self, stmt):
        self.stmt = stmt

        class _R:
            def scalars(self):
                return self

            def all(self):
                return []
        return _R()


def _sql(**kwargs):
    session = CapturingSession()
    CareerScoreRepository(session).get_top_opportunities(user_id="u1", limit=50, **kwargs)
    return str(session.stmt.compile(dialect=postgresql.dialect()))


def test_opportunities_query_without_filters_is_latest_per_url_only():
    sql = _sql(min_score=None, recommendation=None)
    assert "max(career_scores.scanned_at)" in sql
    assert "career_scores.recommendation LIKE" not in sql
    assert "career_scores.career_score >=" not in sql
    assert "LIMIT" in sql


def test_opportunities_query_with_filters():
    sql = _sql(min_score=60.0, recommendation="APPLY")
    assert "career_scores.recommendation LIKE" in sql  # prefix match
    assert "career_scores.career_score >=" in sql


# ── scan job (sources and scorer faked) ───────────────────────────────────

def test_run_scan_happy_path(monkeypatch):
    from types import SimpleNamespace

    import careeros.jobs.sources.loader as loader
    import careeros.jobs.scoring_service as scoring
    from careeros.jobs import scan
    from careeros.shared.background import JobStore

    profile = SimpleNamespace(skills=["Python"], years_experience=3)
    monkeypatch.setattr(scan, "load_profile", lambda uid: profile)

    seen = {}

    class Source:
        def scan_and_normalize(self, hours_old, min_score):
            seen["source"] = (hours_old, min_score)
            return [{"url": "u1"}, {"url": "u2"}, {"url": "u3"}]

    class Scorer:
        def __init__(self, user_id):
            seen["user"] = user_id

        def run_pipeline(self, jobs, prof, semantic, job_meta):
            seen["scored"] = [j.url for j in jobs]
            return {"scored": len(jobs), "apply": 1, "consider": 1, "skip": 0}

    monkeypatch.setattr(loader, "load_job_source_plugin", lambda name: Source())
    monkeypatch.setattr(scoring, "ScoringService", Scorer)

    job = JobStore().create("user_1")
    scan.run_scan(job, "user_1", hours=48, limit=2)

    assert job.status == "completed" and job.result["apply"] == 1
    assert seen == {"source": (48, scan.SOURCE_MIN_FIT_SCORE), "user": "user_1", "scored": ["u1", "u2"]}
    assert "1 APPLY" in job.logs[-1]["message"]


def test_run_scan_without_profile_fails_with_guidance(monkeypatch):
    from careeros.jobs import scan
    from careeros.shared.background import JobStore

    monkeypatch.setattr(scan, "load_profile", lambda uid: None)
    job = JobStore().create("user_1")
    scan.run_scan(job, "user_1", hours=1, limit=1)
    assert job.status == "failed" and "complete onboarding" in job.error


class _CountSession(CapturingSession):
    def execute(self, stmt):
        self.stmt = stmt

        class _R:
            def scalar_one(self):
                return 7
        return _R()


def test_count_latest_counts_all_matches_without_limit():
    session = _CountSession()
    assert CareerScoreRepository(session).count_latest("u1", recommendation="APPLY") == 7
    sql = str(session.stmt.compile(dialect=postgresql.dialect()))
    assert "count(*)" in sql and "LIMIT" not in sql
    assert "career_scores.recommendation LIKE" in sql
