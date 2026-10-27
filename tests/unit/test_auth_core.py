"""careeros.identity.auth — passwords, throttle, sessions, accounts (fake DB)."""

from datetime import timedelta

import pytest

from careeros.identity.auth import accounts, passwords, sessions
from careeros.identity.auth.throttle import LoginThrottle
from careeros.identity.models.auth import AuthCredential, AuthSession
from careeros.identity.models.user import User


# ── passwords ─────────────────────────────────────────────────────────────

def test_hash_and_verify():
    h = passwords.hash_password("correct horse battery")
    assert h.startswith("$argon2id$")
    assert passwords.verify_password(h, "correct horse battery")
    assert not passwords.verify_password(h, "correct horse batterY")


def test_unknown_user_never_verifies():
    assert not passwords.verify_password(None, "timing-equalizer-not-a-real-password")
    assert not passwords.verify_password("not-a-hash", "anything")


@pytest.mark.parametrize("bad", ["short", " leading space pw", "trailing space pw "])
def test_password_policy(bad):
    with pytest.raises(passwords.WeakPassword):
        passwords.hash_password(bad)


# ── throttle ──────────────────────────────────────────────────────────────

def test_throttle_blocks_after_limit_and_recovers():
    now = [1000.0]
    t = LoginThrottle(window=60, per_email=3, per_ip=100, clock=lambda: now[0])
    for _ in range(3):
        assert t.retry_after("a@x.com", "1.1.1.1") == 0
        t.record_failure("A@x.com", "1.1.1.1")  # case-insensitive email key
    assert t.retry_after("a@x.com", "1.1.1.1") > 0
    assert t.retry_after("b@x.com", "1.1.1.1") == 0  # other emails unaffected
    now[0] += 61
    assert t.retry_after("a@x.com", "1.1.1.1") == 0


def test_throttle_per_ip_across_emails():
    t = LoginThrottle(window=60, per_email=100, per_ip=2, clock=lambda: 0.0)
    t.record_failure("a@x.com", "9.9.9.9")
    t.record_failure("b@x.com", "9.9.9.9")
    assert t.retry_after("c@x.com", "9.9.9.9") > 0


def test_success_clears_email_failures():
    t = LoginThrottle(window=60, per_email=2, per_ip=100, clock=lambda: 0.0)
    t.record_failure("a@x.com", "1.1.1.1")
    t.record_success("a@x.com")
    t.record_failure("a@x.com", "1.1.1.1")
    assert t.retry_after("a@x.com", "1.1.1.1") == 0


# ── fake DB ───────────────────────────────────────────────────────────────

class FakeQuery:
    def __init__(self, db, model):
        self.db, self.model, self.preds = db, model, []

    def filter(self, *preds):
        self.preds += preds
        return self

    def _rows(self):
        rows = list(self.db.rows[self.model].values())
        for p in self.preds:  # supports `Model.col == value` only
            col, val = p.left.key, p.right.value
            rows = [r for r in rows if getattr(r, col) == val]
        return rows

    def first(self):
        rows = self._rows()
        return rows[0] if rows else None

    def all(self):
        return self._rows()

    def delete(self):
        rows = self._rows()
        key = "token_hash" if self.model is AuthSession else "user_id"
        for r in rows:
            self.db.rows[self.model].pop(getattr(r, key))
        return len(rows)


class FakeDB:
    def __init__(self):
        self.rows = {User: {}, AuthCredential: {}, AuthSession: {}}

    def add(self, obj):
        key = {User: "id", AuthCredential: "user_id", AuthSession: "token_hash"}[type(obj)]
        if type(obj) is User and obj.is_active is None:
            obj.is_active = True
        self.rows[type(obj)][getattr(obj, key)] = obj

    def get(self, model, key):
        return self.rows[model].get(key)

    def query(self, model):
        return FakeQuery(self, model)

    def flush(self):
        pass


@pytest.fixture
def fake(monkeypatch):
    db = FakeDB()

    class Repo:
        def __init__(self, session):
            pass

        def get_by_email(self, email):
            return next((u for u in db.rows[User].values() if u.email == email), None)

        def get_by_id(self, uid):
            return db.rows[User].get(uid)

        def create_user(self, *, user_id, email, first_name=None, last_name=None):
            u = User(id=user_id, email=email, first_name=first_name, last_name=last_name,
                     onboarding_state="NOT_STARTED", profile_data={}, goals={}, is_active=True)
            db.add(u)
            return u

    monkeypatch.setattr(accounts, "UserRepository", Repo)
    return db


# ── sessions ──────────────────────────────────────────────────────────────

def test_session_roundtrip_stores_only_a_hash(fake):
    fake.add(User(id="u1", email="a@x.com", is_active=True))
    token = sessions.create_session(fake, "u1", "UA", "1.2.3.4")
    assert token not in fake.rows[AuthSession]  # only sha256(token) is stored
    assert sessions.resolve_session(fake, token) == "u1"
    assert sessions.resolve_session(fake, "forged") is None
    assert sessions.resolve_session(fake, None) is None


def test_expired_session_is_rejected(fake):
    fake.add(User(id="u1", email="a@x.com", is_active=True))
    token = sessions.create_session(fake, "u1")
    row = fake.rows[AuthSession][sessions.hash_token(token)]
    row.expires_at = sessions.utcnow() - timedelta(seconds=1)
    assert sessions.resolve_session(fake, token) is None


def test_session_slides_after_refresh_interval(fake):
    fake.add(User(id="u1", email="a@x.com", is_active=True))
    token = sessions.create_session(fake, "u1")
    row = fake.rows[AuthSession][sessions.hash_token(token)]
    row.last_seen_at -= sessions.REFRESH_AFTER  # as if last used 12h ago
    row.expires_at -= sessions.REFRESH_AFTER
    old_expiry = row.expires_at
    assert sessions.resolve_session(fake, token) == "u1"
    assert row.expires_at > old_expiry


def test_deactivated_user_loses_access(fake):
    fake.add(User(id="u1", email="a@x.com", is_active=False))
    token = sessions.create_session(fake, "u1")
    assert sessions.resolve_session(fake, token) is None


# ── accounts ──────────────────────────────────────────────────────────────

def test_create_and_authenticate(fake):
    user = accounts.create_account(fake, " Me@Example.com ", "correct horse battery", "Ada")
    assert user.email == "me@example.com" and user.id.startswith("user_")
    assert accounts.authenticate(fake, "ME@example.com", "correct horse battery") is user
    assert accounts.authenticate(fake, "me@example.com", "wrong password!!") is None
    assert accounts.authenticate(fake, "nobody@example.com", "correct horse battery") is None
    assert accounts.authenticate(fake, "not-an-email", "x") is None


def test_duplicate_email_is_refused(fake):
    accounts.create_account(fake, "me@example.com", "correct horse battery")
    with pytest.raises(accounts.AccountError):
        accounts.create_account(fake, "me@example.com", "another long password")


def test_set_password_for_migrated_user_and_sign_out_everywhere(fake):
    # a user created under Clerk: row exists, no credential yet
    fake.add(User(id="user_2abcCLERK", email="friend@example.com", is_active=True))
    old = sessions.create_session(fake, "user_2abcCLERK")
    accounts.set_password(fake, "friend@example.com", "a brand new password")
    assert accounts.authenticate(fake, "friend@example.com", "a brand new password").id == "user_2abcCLERK"
    assert sessions.resolve_session(fake, old) is None


def test_disable_blocks_login(fake):
    accounts.create_account(fake, "me@example.com", "correct horse battery")
    accounts.set_active(fake, "me@example.com", False)
    assert accounts.authenticate(fake, "me@example.com", "correct horse battery") is None


def test_invalid_email_rejected():
    with pytest.raises(accounts.AccountError):
        accounts.normalize_email("nope")
