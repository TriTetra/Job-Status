"""Saving the profile from Settings keeps app state in profile_data and logs the role only on change."""

from types import SimpleNamespace

from careeros.onboarding import profile


class FakeSession:
    def __init__(self):
        self.executed = []

    def execute(self, stmt, params=None):
        self.executed.append(str(stmt))

    def commit(self):
        pass


def _identity(**kw):
    base = dict(first_name="Ada", last_name="L", country="Germany", current_role_id="r1",
                current_role_title="Backend Engineer", years_in_role=2, career_level="mid",
                total_years=6, languages=[], education_level=None)
    return {**base, **kw}


def _user(**kw):
    base = dict(current_role_id="r1", current_custom_role_id=None, years_in_role=1, career_level="mid",
                career_level_origin="system", onboarding_state="complete",
                profile_data={"first_name": "Old", "briefing_seen": "2026-11-20T10:00:00+00:00",
                              "briefing_dismissed": {"skill:rust": "2026-11-21"}})
    return SimpleNamespace(**{**base, **kw})


def test_save_keeps_briefing_state_and_skips_unchanged_role(monkeypatch):
    user, session = _user(), FakeSession()
    monkeypatch.setattr(profile, "require_user", lambda s, uid: user)
    monkeypatch.setattr(profile, "_resolve_role", lambda s, uid, rid, title: ("r1", None))

    profile.save_identity(session, "u1", _identity())

    assert user.profile_data["first_name"] == "Ada"
    assert user.profile_data["total_years"] == 6
    assert user.profile_data["briefing_seen"] == "2026-11-20T10:00:00+00:00"
    assert user.profile_data["briefing_dismissed"] == {"skill:rust": "2026-11-21"}
    assert session.executed == []  # same role: no new role-history row


def test_save_records_role_history_when_role_changes(monkeypatch):
    user, session = _user(), FakeSession()
    monkeypatch.setattr(profile, "require_user", lambda s, uid: user)
    monkeypatch.setattr(profile, "_resolve_role", lambda s, uid, rid, title: ("r2", None))

    profile.save_identity(session, "u1", _identity(current_role_id="r2"))

    assert user.current_role_id == "r2"
    assert len(session.executed) == 2 and "INSERT INTO user_roles" in session.executed[1]
