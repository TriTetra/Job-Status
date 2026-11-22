"""Public-profile readers: input parsing, API shapes → evidence, failures."""

import json

import pytest

from careeros.evidence import profiles
from careeros.evidence.profiles import ProfileError, read_profile


class _Resp:
    def __init__(self, status=200, body=None, text=None, headers=None):
        self.status_code = status
        self._body = body
        self.text = text if text is not None else json.dumps(body)
        self.content = self.text.encode()
        self.encoding = "utf-8"
        self.headers = headers or {}

    def json(self):
        if self._body is None:
            raise ValueError("not json")
        return self._body


class _HTTP:
    """Routes by URL prefix; records what was asked."""

    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs.get("params")))
        for prefix, resp in self.routes.items():
            if url.startswith(prefix):
                return resp(url, kwargs) if callable(resp) else resp
        return _Resp(404, {})


@pytest.mark.parametrize("value", ["octocat", "@octocat", "github.com/octocat", "https://github.com/octocat/",
                                   "https://www.github.com/octocat?tab=repositories"])
def test_github_accepts_names_and_links(value):
    http = _HTTP({"https://api.github.com/users/octocat/repos": _Resp(body=[]),
                  "https://api.github.com/users/octocat": _Resp(body={"login": "octocat"})})
    assert read_profile("github", value, http).handle == "octocat"


@pytest.mark.parametrize("source, value, message", [
    ("github", "gitlab.com/octocat", "isn't a GitHub link"),
    ("github", "not a name!", "username"),
    ("stackoverflow", "jon skeet", "profile link"),
    ("orcid", "1234", "ORCID iD"),
    ("substack", "not a/valid", "Substack"),
    ("kaggle", "someone", "can't be connected"),
])
def test_bad_input_is_explained(source, value, message):
    with pytest.raises(ProfileError, match=message):
        read_profile(source, value, _HTTP({}))


def test_github_repos_become_languages_topics_and_projects():
    repos = [
        {"name": "api", "language": "Python", "topics": ["fastapi", "not-a-skill"], "fork": False,
         "stargazers_count": 5, "html_url": "https://github.com/o/api", "pushed_at": "2026-01-01"},
        {"name": "ml", "language": "Python", "topics": [], "fork": False, "stargazers_count": 50},
        {"name": "fork", "language": "Go", "fork": True},
        {"name": "old", "language": "Perl", "archived": True},
    ]
    http = _HTTP({"https://api.github.com/users/o/repos": _Resp(body=repos),
                  "https://api.github.com/users/o": _Resp(body={"login": "o", "public_repos": 4})})
    p = read_profile("github", "o", http)
    skills = {name: conf for name, conf, _ in p.skills}
    assert set(skills) == {"Python", "FastAPI"}                 # forks/archived ignored, unknown topics dropped
    assert skills["Python"] > skills["FastAPI"]
    assert [i["name"] for i in p.items] == ["ml", "api"]        # most starred first
    assert "2 public repositories" in p.summary


def test_github_rate_limit_message():
    http = _HTTP({"https://api.github.com/users/o": _Resp(403, {"message": "rate limit"})})
    with pytest.raises(ProfileError, match="limiting requests"):
        read_profile("github", "o", http)


def test_rejected_server_token_falls_back_to_anonymous(monkeypatch):
    monkeypatch.setattr(profiles, "get_settings", lambda: type("S", (), {"github_token": "expired"})())

    def user(url, kw):
        return _Resp(401, {}) if "Authorization" in kw["headers"] else _Resp(body={"login": "o"})

    def repos(url, kw):
        assert "Authorization" not in kw["headers"]
        return _Resp(body=[])

    http = _HTTP({"https://api.github.com/users/o/repos": repos, "https://api.github.com/users/o": user})
    assert read_profile("github", "o", http).handle == "o"


def test_unknown_profile_message():
    with pytest.raises(ProfileError, match="No GitHub profile"):
        read_profile("github", "nobody", _HTTP({}))


def test_stackoverflow_tags_map_to_known_skills():
    tags = [{"tag_name": "python-3.x", "answer_count": 40, "answer_score": 300},
            {"tag_name": "reactjs", "answer_count": 3, "answer_score": 2},
            {"tag_name": "python", "answer_count": 9, "answer_score": 10},          # same skill again
            {"tag_name": "arrays", "answer_count": 90, "answer_score": 500},       # not a skill
            {"tag_name": "rust", "answer_count": 0, "answer_score": 0, "question_count": 1}]
    http = _HTTP({
        "https://api.stackexchange.com/2.3/users/42/top-tags": _Resp(body={"items": tags}),
        "https://api.stackexchange.com/2.3/users/42": _Resp(body={"items": [{"reputation": 1234, "link": "L"}]}),
    })
    p = read_profile("stackoverflow", "https://stackoverflow.com/users/42/me", http)
    skills = {n: c for n, c, _ in p.skills}
    assert [n for n, _, _ in p.skills] == ["Python", "React"]   # version tag folded, duplicates, generic and lurker tags dropped
    assert skills["Python"] > skills["React"]
    assert p.metadata["reputation"] == 1234 and p.handle == "42"


def test_orcid_works_and_fundings_become_achievements():
    record = {
        "person": {"name": {"given-names": {"value": "Ada"}, "family-name": {"value": "L"}},
                   "keywords": {"keyword": [{"content": "Machine Learning"}, {"content": "poetry"}]}},
        "activities-summary": {
            "works": {"group": [{"work-summary": [{
                "title": {"title": {"value": "A paper"}}, "type": "journal-article",
                "publication-date": {"year": {"value": "2024"}}, "journal-title": {"value": "Nature"},
                "external-ids": {"external-id": [{"external-id-type": "doi", "external-id-value": "10.1/x"}]}}]},
                {"work-summary": [{"title": None}]}]},
            "fundings": {"group": [{"funding-summary": [{"title": {"title": {"value": "Grant X"}},
                                                         "organization": {"name": "TUBITAK"}}]}]},
        },
    }
    http = _HTTP({"https://pub.orcid.org/v3.0/0000-0002-1825-0097/record": _Resp(body=record)})
    p = read_profile("orcid", "https://orcid.org/0000-0002-1825-0097", http)
    pub, grant = p.items
    assert (pub["type"], pub["url"], pub["data"]["detail"], pub["data"]["year"]) == (
        "publication", "https://doi.org/10.1/x", "Nature", "2024")
    assert (grant["type"], grant["data"]["detail"]) == ("grant", "TUBITAK")
    assert [n for n, _, _ in p.skills] == ["Machine Learning"]
    assert p.metadata["name"] == "Ada L"


FEED = """<?xml version="1.0"?><rss><channel>
<item><title>Building a RAG app with LangChain</title><link>https://x/1</link>
  <category>python</category><category>machine-learning</category></item>
<item><title>Why I like Rust</title><link>https://x/2</link></item>
<item><title>Notes on gardening</title></item>
</channel></rss>"""


def test_medium_feed_becomes_articles_and_topics():
    http = _HTTP({"https://medium.com/feed/@me": _Resp(text=FEED)})
    p = read_profile("medium", "medium.com/@me", http)
    assert [i["type"] for i in p.items] == ["article"] * 3
    assert {"Python", "Machine Learning", "RAG", "LangChain", "Rust"} <= {n for n, _, _ in p.skills}


def test_substack_redirect_to_private_address_is_refused(monkeypatch):
    def check(url):
        if "internal" in url:
            raise profiles.PortfolioCrawlError("Only public websites can be added.")
        return url
    monkeypatch.setattr(profiles, "check_url", check)
    http = _HTTP({"https://me.substack.com/feed": _Resp(301, text="", headers={"location": "http://internal/feed"})})
    with pytest.raises(ProfileError, match="public"):
        read_profile("substack", "me.substack.com", http)


def test_substack_follows_redirect_to_its_own_domain(monkeypatch):
    monkeypatch.setattr(profiles, "check_url", lambda url: url)
    http = _HTTP({"https://me.substack.com/feed": _Resp(301, text="", headers={"location": "https://www.me.com/feed"}),
                  "https://www.me.com/feed": _Resp(text=FEED)})
    assert len(read_profile("substack", "me", http).items) == 3


def test_save_profile_replaces_evidence_and_remembers_account():
    from careeros.evidence.models.evidence_item import EvidenceItem
    from careeros.identity.models.connected_account import ConnectedAccount
    from tests.unit.test_evidence import SKILLS, FakeSession

    session = FakeSession(SKILLS)
    prof = profiles.Profile(handle="o", url="https://github.com/o", summary="Read 2.",
                            skills=[("Python", 0.7, "a"), ("python", 0.8, "b"), ("Elm", 0.6, "c")],
                            items=[{"name": "api", "type": "project", "confidence": 0.75, "url": "u", "data": {"stars": 1}}])
    out = profiles.save_profile(session, "u1", "github", prof)

    deletes = [q for model, q in session.queries if model is EvidenceItem]
    assert deletes and deletes[0].deleted
    skills = {i.skill_name: i for i in session.added if isinstance(i, EvidenceItem) and i.evidence_data["type"] == "skill"}
    assert set(skills) == {"Python", "Elm"} and skills["Python"].confidence_score == 0.8 and skills["Python"].skill_id == 1
    account = next(i for i in session.added if isinstance(i, ConnectedAccount))
    assert (account.provider, account.provider_username, account.account_metadata["summary"]) == ("github", "o", "Read 2.")
    assert out == {"status": "connected", "source": "github", "handle": "o", "url": "https://github.com/o",
                   "summary": "Read 2.", "skills_found": 2, "items_found": 1}
