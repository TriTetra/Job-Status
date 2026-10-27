"""GitHub repositories → evidence items.

Uses the user's own OAuth token (from the connected account), so it sees the
repos they own, including private ones. One project item per repo plus one
skill item per language, written to `evidence_items` with source="github".
"""

import logging
from typing import Iterable

import requests
from sqlalchemy.orm import Session

from core.db.models.evidence_item import EvidenceItem

from .skills import find_canonical, load_all_skills

logger = logging.getLogger(__name__)

# Source weight for GitHub evidence (higher than resume)
GITHUB_CONFIDENCE_BASE = 0.85
GITHUB_CONFIDENCE_BOOST_STARS = 0.05  # per 10 stars
GITHUB_CONFIDENCE_BOOST_COMMITS = 0.02  # per 100 commits

# Root entries that indicate a test suite / documentation
_TEST_MARKERS = {"tests", "test", "pytest.ini", "setup.cfg", "jest.config.js"}
_DOC_DIRS = {"docs", "documentation", "wiki"}


# ── quality signals (pure) ────────────────────────────────────────────────

def detect_tests(root_entries: Iterable[dict]) -> bool:
    """True if the repo root has a test directory or test-runner config."""
    for entry in root_entries:
        name = (entry.get("name") or "").lower()
        if name in _TEST_MARKERS:
            return True
        if entry.get("type") == "dir" and "test" in name:
            return True
    return False


def detect_docs(root_entries: Iterable[dict]) -> bool:
    """True if the repo has a README and a dedicated docs directory."""
    names = {(e.get("name") or "").lower() for e in root_entries}
    has_readme = any(n.startswith("readme") for n in names)
    return has_readme and bool(names & _DOC_DIRS)


# ── GitHub REST client ────────────────────────────────────────────────────

class GitHubAnalyzer:
    """Read a user's own repositories through the GitHub REST API."""

    BASE_URL = "https://api.github.com"

    def __init__(self, access_token: str, session: requests.Session | None = None):
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self._http = session or requests.Session()

    def get_top_repos(self, limit: int = 20) -> list[dict]:
        """User's own repos (no forks/archived), most recently pushed first."""
        repos: list[dict] = []
        page = 1

        while len(repos) < limit and page <= 5:
            response = self._http.get(
                f"{self.BASE_URL}/user/repos",
                headers=self.headers,
                params={
                    "sort": "pushed",
                    "direction": "desc",
                    "per_page": min(100, limit - len(repos)),
                    "page": page,
                    "type": "owner",
                },
                timeout=15,
            )
            if response.status_code != 200:
                logger.error("GitHub repos fetch failed: %s", response.status_code)
                break

            page_repos = response.json()
            if not page_repos:
                break

            for repo in page_repos:
                if repo.get("fork") or repo.get("archived"):
                    continue
                repos.append(self._describe(repo))
                if len(repos) >= limit:
                    break
            page += 1

        logger.info("Fetched %d repos from GitHub", len(repos))
        return repos

    def _describe(self, repo: dict) -> dict:
        full_name = repo["full_name"]
        root = self._get_json(f"/repos/{full_name}/contents/", default=[])
        root = root if isinstance(root, list) else []
        releases = self._get_json(f"/repos/{full_name}/releases", params={"per_page": 1}, default=[])
        return {
            "name": repo["name"],
            "full_name": full_name,
            "description": repo.get("description"),
            "language": repo.get("language"),
            "languages": self._get_json(f"/repos/{full_name}/languages", default={}),
            "topics": repo.get("topics") or [],
            "stars": repo.get("stargazers_count", 0),
            "commits_count": self._estimate_commits(repo),
            "last_push": repo.get("pushed_at"),
            "url": repo.get("html_url"),
            "has_tests": detect_tests(root),
            "has_docs": detect_docs(root),
            "has_releases": bool(releases),
        }

    def _get_json(self, path: str, params: dict | None = None, default=None):
        try:
            response = self._http.get(f"{self.BASE_URL}{path}", headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
        except requests.RequestException as e:
            logger.warning("GitHub request %s failed: %s", path, e)
        return default

    @staticmethod
    def _estimate_commits(repo: dict) -> int:
        """Rough proxy — the REST API has no cheap commit count. ~1 commit per 50 KB."""
        return max(1, repo.get("size", 0) // 50)


# ── evidence items ────────────────────────────────────────────────────────

def _calculate_confidence(repo: dict, total_bytes: int, lang_bytes: int) -> float:
    """Confidence for one language in one repo."""
    confidence = GITHUB_CONFIDENCE_BASE

    # Language proportion in repo (higher = stronger signal), up to +0.1
    if total_bytes > 0:
        confidence += (lang_bytes / total_bytes) * 0.1

    stars = repo.get("stars", 0)
    confidence += min(0.1, (stars // 10) * GITHUB_CONFIDENCE_BOOST_STARS)

    commits = repo.get("commits_count", 0)
    confidence += min(0.1, (commits // 100) * GITHUB_CONFIDENCE_BOOST_COMMITS)

    return min(0.99, confidence)


def create_github_evidence(user_id: str, repos: list[dict], session: Session) -> dict:
    """Replace the user's GitHub evidence with items built from `repos`.

    Returns {"skills_created": int, "projects_created": int}.
    """
    session.query(EvidenceItem).filter(
        EvidenceItem.user_id == user_id,
        EvidenceItem.source == "github",
    ).delete()

    canonical_skills = load_all_skills(session)
    projects_created = 0
    language_agg: dict[str, dict] = {}

    for repo in repos:
        languages = repo.get("languages") or {}

        if repo.get("name"):
            session.add(EvidenceItem(
                user_id=user_id,
                skill_name=repo["name"],
                source="github",
                source_url=repo.get("url"),
                confidence_score=0.85,
                evidence_data={
                    "type": "project",
                    "description": repo.get("description") or "",
                    "technologies": list(languages.keys()),
                    "language": repo.get("language"),
                    "topics": repo.get("topics") or [],
                    "stars": repo.get("stars", 0),
                    "commits_estimate": repo.get("commits_count", 0),
                    "code_bytes": sum(languages.values()),
                    "has_tests": repo.get("has_tests"),
                    "has_docs": repo.get("has_docs"),
                    "has_releases": repo.get("has_releases"),
                    "last_push": repo.get("last_push"),
                    "url": repo.get("url"),
                },
            ))
            projects_created += 1

        for lang, bytes_count in languages.items():
            agg = language_agg.setdefault(lang, {"total_bytes": 0, "repos": []})
            agg["total_bytes"] += bytes_count
            agg["repos"].append(repo)

    for lang, data in language_agg.items():
        canonical = find_canonical(lang, canonical_skills)
        avg_confidence = sum(
            _calculate_confidence(r, sum((r.get("languages") or {}).values()), (r.get("languages") or {}).get(lang, 0))
            for r in data["repos"]
        ) / len(data["repos"])

        session.add(EvidenceItem(
            user_id=user_id,
            skill_name=canonical.name if canonical else lang,
            skill_id=canonical.id if canonical else None,
            source="github",
            confidence_score=round(avg_confidence, 3),
            evidence_data={
                "type": "skill",
                "bytes_written": data["total_bytes"],
                "repo_count": len(data["repos"]),
                "matched_canonical": canonical.name if canonical else None,
            },
        ))

    session.commit()
    logger.info("GitHub evidence: %d skills, %d projects", len(language_agg), projects_created)
    return {"skills_created": len(language_agg), "projects_created": projects_created}
