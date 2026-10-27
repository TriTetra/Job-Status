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


def _row(url="https://x/1", **kw):
    from careeros.jobs.models.job import Job as JobRow
    base = dict(url=url, title="Backend Engineer", company="Acme", location="Remote", description="Python",
                content_hash="h-" + url, required_skills=["Python"], required_years=3.0, remote=True,
                remote_region="Europe", ats="greenhouse", source="greenhouse", company_key="acme",
                application_url=url + "/apply", sponsors_visa=None)
    base.update(kw)
    return JobRow(**base)


def test_to_scoring_input_maps_rows_and_keeps_metadata():
    jobs, meta = to_scoring_input([_row()])
    assert jobs[0].required_years == 3.0 and jobs[0].remote is True and jobs[0].sponsors_visa is None
    m = meta["https://x/1"]
    assert m["remote_region"] == "Europe" and m["source"] == "greenhouse"
    assert m["application_url"] == "https://x/1/apply" and m["company_key"] == "acme"


def test_to_scoring_input_defaults():
    jobs, meta = to_scoring_input([_row(required_years=None, remote=None, ats=None, source=None, application_url=None)])
    assert jobs[0].required_years == 2.0 and jobs[0].remote is False
    assert meta["https://x/1"]["source"] == "unknown"
    assert meta["https://x/1"]["application_url"] == "https://x/1"  # the posting page itself


def test_only_changed_jobs_are_rescored():
    from careeros.jobs.scan import input_hash, pick_changed

    a, b, c = _row("a"), _row("b"), _row("c")
    known = {"a": input_hash(a, "fp1"), "b": "stale"}  # a unchanged, b changed, c new
    rows, hashes, unchanged = pick_changed([a, b, c], known, "fp1", limit=10)
    assert [r.url for r in rows] == ["b", "c"] and unchanged == 1
    assert hashes["c"] == input_hash(c, "fp1")


def test_profile_change_rescores_everything_and_limit_applies_in_order():
    from careeros.jobs.scan import input_hash, pick_changed

    rows_in = [_row(u) for u in "abcd"]
    known = {r.url: input_hash(r, "old-profile") for r in rows_in}
    rows, hashes, unchanged = pick_changed(rows_in, known, "new-profile", limit=2)
    assert [r.url for r in rows] == ["a", "b"] and set(hashes) == {"a", "b"} and unchanged == 0


def test_posting_edit_changes_input_hash():
    from careeros.jobs.scan import input_hash

    assert input_hash(_row(content_hash="v1"), "fp") != input_hash(_row(content_hash="v2"), "fp")
    # imports without a content hash still hash their text
    assert input_hash(_row(content_hash=None, description="x"), "fp") != input_hash(_row(content_hash=None, description="y"), "fp")


def test_profile_fingerprint_tracks_skills_and_prefs():
    from careeros.identity.domain.profile import UserProfile
    from careeros.identity.domain.skill import Skill
    from careeros.jobs.scan import profile_fingerprint

    p1 = UserProfile(name="A", email="", years_experience=3, skills=[Skill("Python", SkillLevel.EXPERT)])
    p2 = UserProfile(name="A", email="", years_experience=3, skills=[Skill("Python", SkillLevel.WORKING)])
    assert profile_fingerprint(p1, {}) == profile_fingerprint(p1, {})
    assert profile_fingerprint(p1, {}) != profile_fingerprint(p2, {})
    assert profile_fingerprint(p1, {}) != profile_fingerprint(p1, {"salary_min": 100000})


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


def test_opportunities_query_hides_closed_jobs_and_has_no_filters_by_default():
    sql = _sql(min_score=None, recommendation=None)
    assert "LEFT OUTER JOIN jobs" in sql and "jobs.closed_at IS NULL" in sql
    assert "career_scores.recommendation LIKE" not in sql
    assert "career_scores.career_score >=" not in sql
    assert "LIMIT" in sql


def test_opportunities_query_with_filters():
    sql = _sql(min_score=60.0, recommendation="APPLY")
    assert "career_scores.recommendation LIKE" in sql  # prefix match
    assert "career_scores.career_score >=" in sql


# ── scan job ──────────────────────────────────────────────────────────────

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
    assert "count(*)" in sql and "LIMIT" not in sql and "jobs.closed_at IS NULL" in sql
    assert "career_scores.recommendation LIKE" in sql
