"""services.evidence and the resume generator's evidence view — pure parts, no DB."""

from types import SimpleNamespace

import pytest

from services.evidence.github import GitHubAnalyzer, detect_docs, detect_tests
from services.evidence.skills import find_canonical
from services.resume_intelligence.application.resume_generator import build_project_list, build_skill_evidence


# ── skills: canonical matching ────────────────────────────────────────────

def _skill(id, name, aliases=()):
    return SimpleNamespace(id=id, name=name, aliases=list(aliases))


SKILLS = [_skill(1, "Python", ["py"]), _skill(2, "JavaScript", ["js"]), _skill(3, "PostgreSQL", ["postgres"])]


@pytest.mark.parametrize("raw, expected", [
    ("python", "Python"),          # exact, case-insensitive
    ("  Python ", "Python"),       # trimmed
    ("js", "JavaScript"),          # alias
    ("Postgres", "PostgreSQL"),    # alias
    ("Postgresql", "PostgreSQL"),  # exact
    ("Pythn", "Python"),           # fuzzy (>= 0.8)
])
def test_find_canonical_matches(raw, expected):
    assert find_canonical(raw, SKILLS).name == expected


def test_find_canonical_returns_none_for_unknown():
    assert find_canonical("Haskell", SKILLS) is None


# ── GitHub quality signals ────────────────────────────────────────────────

def test_detect_tests():
    assert detect_tests([{"name": "tests", "type": "dir"}])
    assert detect_tests([{"name": "jest.config.js", "type": "file"}])
    assert detect_tests([{"name": "integration_tests", "type": "dir"}])
    assert not detect_tests([{"name": "src", "type": "dir"}, {"name": "latest.md", "type": "file"}])


def test_detect_docs_needs_readme_and_docs_dir():
    assert detect_docs([{"name": "README.md"}, {"name": "docs"}])
    assert not detect_docs([{"name": "docs"}])
    assert not detect_docs([{"name": "README.md"}])


class FakeResponse:
    def __init__(self, status, body):
        self.status_code = status
        self._body = body

    def json(self):
        return self._body


class FakeGitHub:
    """Routes GitHub REST paths to canned responses."""

    def __init__(self, routes):
        self.routes = routes
        self.paths = []

    def get(self, url, headers=None, params=None, timeout=None):
        path = url.replace(GitHubAnalyzer.BASE_URL, "")
        self.paths.append(path)
        status, body = self.routes.get(path, (404, None))
        if path == "/user/repos" and (params or {}).get("page", 1) > 1:
            return FakeResponse(200, [])
        return FakeResponse(status, body)


def test_get_top_repos_collects_signals_and_skips_forks():
    repo = {
        "name": "engine", "full_name": "me/engine", "description": "fast", "language": "Rust",
        "topics": ["db"], "stargazers_count": 12, "size": 600, "pushed_at": "2026-10-01",
        "html_url": "https://github.com/me/engine", "fork": False, "archived": False,
    }
    fork = {**repo, "name": "forked", "full_name": "me/forked", "fork": True}
    gh = FakeGitHub({
        "/user/repos": (200, [repo, fork]),
        "/repos/me/engine/contents/": (200, [{"name": "README.md", "type": "file"}, {"name": "docs", "type": "dir"},
                                            {"name": "tests", "type": "dir"}]),
        "/repos/me/engine/releases": (200, [{"id": 1}]),
        "/repos/me/engine/languages": (200, {"Rust": 9000, "Python": 1000}),
    })

    repos = GitHubAnalyzer("tok", session=gh).get_top_repos(limit=5)

    assert [r["name"] for r in repos] == ["engine"]
    r = repos[0]
    assert r["languages"] == {"Rust": 9000, "Python": 1000}
    assert r["topics"] == ["db"]
    assert r["stars"] == 12
    assert r["commits_count"] == 12  # 600 KB // 50
    assert (r["has_tests"], r["has_docs"], r["has_releases"]) == (True, True, True)
    assert not any("forked" in p for p in gh.paths)


def test_missing_repo_details_degrade_to_false():
    repo = {"name": "x", "full_name": "me/x", "fork": False, "archived": False}
    gh = FakeGitHub({"/user/repos": (200, [repo])})  # contents/releases/languages all 404
    r = GitHubAnalyzer("tok", session=gh).get_top_repos(limit=1)[0]
    assert r["languages"] == {}
    assert (r["has_tests"], r["has_docs"], r["has_releases"]) == (False, False, False)


# ── resume generator: evidence_items → prompt/template shapes ─────────────

def _item(name, source, data, url=None):
    return SimpleNamespace(skill_name=name, source=source, evidence_data=data, source_url=url)


ITEMS = [
    _item("engine", "github", {"type": "project", "technologies": ["Rust", "Python"], "language": "Rust",
                                "stars": 12, "code_bytes": 10240, "has_tests": True, "topics": ["db"]},
          url="https://github.com/me/engine"),
    _item("site", "portfolio", {"type": "project", "technologies": ["React"], "description": "my site"}),
    _item("Python", "resume", {"type": "skill"}),          # skill items are not projects
    _item("Backend @ Acme", "resume", {"type": "experience"}),
]


def test_build_project_list_keeps_projects_only_github_first():
    projects = build_project_list(ITEMS)
    assert [p["name"] for p in projects] == ["engine", "site"]
    engine = projects[0]
    assert engine["github_url"] == "https://github.com/me/engine"
    assert engine["github_details"]["size"] == "10 KB of code"
    assert engine["author_commit_count"] is None  # never invent a commit count
    assert projects[1]["github_url"] is None


def test_build_skill_evidence_links_skills_to_projects_case_insensitively():
    projects = build_project_list(ITEMS)
    aggregated = [
        {"skill_name": "python", "aggregated_confidence": 0.7},
        {"skill_name": "Go", "aggregated_confidence": 0.4},
    ]
    evidence = build_skill_evidence(aggregated, projects)

    assert evidence["python"]["confidence"] == 0.7
    assert [e["project_name"] for e in evidence["python"]["evidence_list"]] == ["engine"]
    assert evidence["python"]["evidence_list"][0]["has_tests"] is True
    assert evidence["Go"]["evidence_list"] == []


# ── DB writers, with an in-memory fake session ────────────────────────────

class FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.deleted = False

    def filter(self, *args):
        return self

    def all(self):
        return list(self.rows)

    def first(self):
        return self.rows[0] if self.rows else None

    def delete(self):
        self.deleted = True
        return 0


class FakeSession:
    def __init__(self, skills):
        from core.db.models.skill import Skill

        self._rows = {Skill: skills}
        self.added = []
        self.queries = []
        self.commits = 0

    def query(self, model):
        q = FakeQuery(self._rows.get(model, []))
        self.queries.append((model, q))
        return q

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.commits += 1


def test_create_github_evidence_projects_and_canonical_language_skills():
    from core.db.models.evidence_item import EvidenceItem
    from services.evidence.github import create_github_evidence

    session = FakeSession(SKILLS)
    repos = [
        {"name": "a", "url": "u/a", "languages": {"Python": 800, "JS": 200}, "stars": 0, "commits_count": 1,
         "has_tests": True, "topics": ["x"]},
        {"name": "b", "url": "u/b", "languages": {"python": 100}, "stars": 30, "commits_count": 300},
    ]
    stats = create_github_evidence("user_1", repos, session)

    deletes = [q for model, q in session.queries if model is EvidenceItem]
    assert deletes and deletes[0].deleted  # old GitHub evidence replaced
    projects = [i for i in session.added if i.evidence_data["type"] == "project"]
    skills = {i.skill_name: i for i in session.added if i.evidence_data["type"] == "skill"}

    assert stats == {"skills_created": 3, "projects_created": 2}
    assert projects[0].evidence_data["has_tests"] is True
    assert projects[0].evidence_data["code_bytes"] == 1000
    assert skills["JavaScript"].skill_id == 2            # alias "js" → canonical
    assert skills["Python"].skill_id == 1
    assert all(0 < i.confidence_score < 1 for i in skills.values())
    assert session.commits == 1


def test_sync_portfolio_dedupes_technologies_and_maps_canonical():
    from services.evidence.portfolio import sync_portfolio_evidence

    class Crawler:
        def crawl(self, url):
            return {"projects": [{"name": "Site", "technologies": ["react"]}],
                    "technologies": ["python", "Python", "py", "rust"]}

    session = FakeSession(SKILLS)
    out = sync_portfolio_evidence("user_1", "https://me.dev", session, crawler=Crawler())

    skills = [i for i in session.added if getattr(i, "evidence_data", None) == {"type": "skill"}]
    assert sorted(i.skill_name for i in skills) == ["Python", "rust"]  # 3 spellings of Python → 1
    assert out["evidence_created"] == 3  # 1 project + 2 skills
    assert out["technologies_found"] == 4


def test_sync_portfolio_raises_on_crawl_error():
    from services.evidence.portfolio import PortfolioCrawlError, sync_portfolio_evidence

    class Broken:
        def crawl(self, url):
            return {"error": "Request timeout"}

    with pytest.raises(PortfolioCrawlError, match="timeout"):
        sync_portfolio_evidence("user_1", "https://me.dev", FakeSession(SKILLS), crawler=Broken())
