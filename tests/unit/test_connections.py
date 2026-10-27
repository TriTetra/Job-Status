"""Role context, evidence sources, goals catalog, evidence review, GitHub linking, market refresh."""

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from careeros.evidence.items import group_for_review
from careeros.evidence.sources import DEFAULT_SOURCES, present_sources, suggested_source_ids
from careeros.identity import github_account
from careeros.identity.current_role import CurrentRole, infer_category
from careeros.onboarding.goals_catalog import visible_goals
from careeros.shared.background import JobStore
from careeros.shared.config import get_settings


# ── role → category → sources / goals ─────────────────────────────────────

@pytest.mark.parametrize("title, category", [
    ("Senior Cardiologist", "medical"),
    ("Postdoc researcher", "academic"),
    ("Landscape Architect", "architecture"),
    ("Corporate Attorney", "legal"),
    ("Backend Engineer", None),
    (None, None),
])
def test_infer_category(title, category):
    assert infer_category(title) == category


def test_suggested_sources():
    canonical = CurrentRole("Backend Engineer", "Engineering", is_custom=False, suggested_source_ids=["github", "stackoverflow"])
    assert suggested_source_ids(canonical) == ["github", "stackoverflow"]
    custom = CurrentRole("Nurse", "medical", is_custom=True)
    assert suggested_source_ids(custom) == ["pubmed", "orcid", "scholar", "doximity"]
    assert suggested_source_ids(CurrentRole("Juggler", None, is_custom=True)) == DEFAULT_SOURCES
    assert suggested_source_ids(CurrentRole("X", "Engineering", is_custom=False)) == DEFAULT_SOURCES  # nothing seeded
    assert suggested_source_ids(None) == DEFAULT_SOURCES


def _src(id, oauth=None, order=0):
    return SimpleNamespace(id=id, label=id.title(), icon=None, category=None, status="available",
                           connect_kind="oauth" if oauth else "url", oauth_provider=oauth, sort_order=order)


def test_present_sources_orders_recommended_by_suggestion_and_marks_connected():
    sources = [_src("portfolio"), _src("github", oauth="github"), _src("linkedin")]
    view = present_sources(sources, suggested=["github", "portfolio"], connected={"github"})
    assert [s["id"] for s in view["recommended"]] == ["github", "portfolio"]
    assert [s["id"] for s in view["all"]] == ["portfolio", "github", "linkedin"]
    assert next(s for s in view["all"] if s["id"] == "github")["connected"] is True
    assert next(s for s in view["all"] if s["id"] == "linkedin")["suggested"] is False


def test_visible_goals_hide_other_professions_and_flag_priorities():
    rows = [
        ("ship", "Ship faster", "growth", ["Engineering"], ["Engineering"]),
        ("residency", "Get residency", "career", ["medical"], ["medical"]),
        ("salary", "Earn more", "money", ["Engineering", "medical"], []),
    ]
    eng = visible_goals(rows, "Engineering")
    assert [(g["id"], g["suggested"]) for g in eng] == [("ship", True), ("salary", False)]
    assert [g["id"] for g in visible_goals(rows, None)] == ["ship", "residency", "salary"]  # no role → all


def test_group_for_review_buckets():
    now = datetime(2026, 10, 1)
    items = [
        SimpleNamespace(id=i, skill_name=n, skill_id=None, confidence_score=0.8, source="resume",
                        source_url=None, evidence_text=None, evidence_data=d, created_at=now)
        for i, (n, d) in enumerate([
            ("Python", {"type": "skill"}), ("Rust", None), ("engine", {"type": "project"}),
            ("Acme", {"type": "experience"}), ("BSc", {"type": "education"}),
            ("AWS SA", {"type": "certification"}), ("Medal", {"type": "award"}),
        ])
    ]
    g = group_for_review(items)
    assert [len(g[k]) for k in ("skills", "projects", "experiences", "education", "certifications")] == [3, 1, 1, 1, 1]
    assert g["skills"][0]["id"] == "0" and g["skills"][0]["created_at"] == "2026-10-01T00:00:00"


# ── GitHub OAuth ──────────────────────────────────────────────────────────

def test_oauth_state_is_single_use_and_expires():
    states = github_account.OAuthStates(ttl=timedelta(minutes=10))
    s = states.issue("user_1")
    assert states.consume(s) == "user_1"
    assert states.consume(s) is None          # replay rejected
    assert states.consume("forged") is None

    old = states.issue("user_2")
    states._states[old] = ("user_2", datetime.utcnow() - timedelta(minutes=11))
    assert states.consume(old) is None        # expired


class FakeHTTP:
    def __init__(self, token_resp, user_resp=None):
        self.token_resp, self.user_resp = token_resp, user_resp

    def post(self, url, **kw):
        return self.token_resp

    def get(self, url, **kw):
        return self.user_resp


def _resp(status, body, text=""):
    return SimpleNamespace(status_code=status, json=lambda: body, text=text or str(body))


class FakeSession:
    def __init__(self):
        self.added, self.commits = [], 0

    def query(self, model):
        class Q:
            def filter(self, *a):
                return self

            def first(self):
                return None
        return Q()

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.commits += 1


@pytest.fixture
def oauth_env(monkeypatch):
    from cryptography.fernet import Fernet

    from careeros.shared.crypto import get_token_cipher

    monkeypatch.setenv("GITHUB_CLIENT_ID", "cid")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "secret")
    monkeypatch.setenv("GITHUB_REDIRECT_URI", "http://localhost:8000/api/oauth/github/callback")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode())
    get_settings.cache_clear()
    get_token_cipher.cache_clear()
    monkeypatch.setattr(github_account, "oauth_states", github_account.OAuthStates())
    yield
    get_settings.cache_clear()
    get_token_cipher.cache_clear()


def test_authorize_url_carries_state_and_scopes(oauth_env):
    url = github_account.authorize_url("user_1")
    assert url.startswith(github_account.AUTHORIZE_URL)
    assert "client_id=cid" in url and "state=" in url and "scope=read%3Auser" in url


def test_callback_with_unknown_state_is_rejected(oauth_env):
    with pytest.raises(github_account.GitHubAccountError) as e:
        github_account.complete_authorization(FakeSession(), "forged", "code", http=FakeHTTP(None))
    assert e.value.status_code == 400


def test_failed_token_exchange_does_not_leak_github_response(oauth_env):
    state = github_account.oauth_states.issue("user_1")
    http = FakeHTTP(_resp(200, {"error": "bad_verification_code", "client_secret_hint": "s3cr3t"}))
    with pytest.raises(github_account.GitHubAccountError) as e:
        github_account.complete_authorization(FakeSession(), state, "code", http=http)
    assert e.value.status_code == 502
    assert "s3cr3t" not in str(e.value) and "bad_verification_code" not in str(e.value)


def test_successful_callback_stores_encrypted_token(oauth_env):
    from careeros.shared.crypto import get_token_cipher

    state = github_account.oauth_states.issue("user_1")
    http = FakeHTTP(_resp(200, {"access_token": "gho_real"}), _resp(200, {"id": 42, "login": "octo", "followers": 3}))
    session = FakeSession()

    assert github_account.complete_authorization(session, state, "code", http=http) == "user_1"

    account = session.added[0]
    assert account.provider == "github" and account.provider_username == "octo"
    assert account.access_token != "gho_real"
    assert get_token_cipher().decrypt(account.access_token) == "gho_real"
    assert account.account_metadata["followers"] == 3
    assert session.commits == 1


# ── single-flight jobs / market refresh ───────────────────────────────────

def test_create_unless_active_is_single_flight():
    store = JobStore()
    first, created = store.create_unless_active("user_a", "crawl")
    second, created2 = store.create_unless_active("user_b", "crawl")
    assert created and not created2 and second is first
    first.update(status="completed")
    third, created3 = store.create_unless_active("user_b", "crawl")
    assert created3 and third is not first


def test_market_refresh_continues_when_one_source_fails(monkeypatch):
    import careeros.market.sources.hackernews.signal_extractor as hn
    import careeros.market.sources.techcrunch.signal_extractor as tc
    from careeros.market import refresh

    class BrokenHN:
        def extract_monthly_signals(self, year, month):
            raise RuntimeError("HN down")

    class OkTC:
        def extract_signals(self, hours):
            return 7

    monkeypatch.setattr(hn, "HNSignalExtractor", BrokenHN)
    monkeypatch.setattr(tc, "TechCrunchSignalExtractor", OkTC)

    job = JobStore().create("user_a", label=refresh.REFRESH_LABEL)
    refresh.run_refresh(job, hours=24)

    messages = [entry["message"] for entry in job.logs]
    assert job.status == "completed" and job.progress == 100
    assert any("HackerNews skipped: HN down" in m for m in messages)
    assert "✓ TechCrunch: 7 signals" in messages


# ── role search relevance ─────────────────────────────────────────────────

def test_role_relevance_ranking():
    from careeros.identity.roles import relevance

    def role(title, slug, aliases=(), category="Engineering"):
        return SimpleNamespace(title=title, slug=slug, aliases=list(aliases), category=category)

    exact = role("Backend Engineer", "backend_engineer")
    alias = role("Server Developer", "server_developer", aliases=["backend engineer"])
    partial = role("Senior Backend Engineer", "senior_backend_engineer")
    unrelated = role("Nurse", "nurse", category="medical")

    q = "Backend Engineer"
    # exact title (1000) > exact alias (300) > title substring (200)
    assert relevance(exact, q) > relevance(alias, q) > relevance(partial, q) > 0
    assert relevance(unrelated, q) == 0
    assert relevance(role("Data Scientist", "data_scientist", category="AI/ML"), "ai/ml") == 50  # category only
