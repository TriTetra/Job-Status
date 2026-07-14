"""Enrich evidence table rows with real GitHub metrics."""

from typing import Any, Dict, Optional

from core.db.connection import db
from core.db.repositories import EvidenceRepository

from .client import GitHubClient
from .repo_analyzer import RepoAnalyzer


class EvidenceEnricher:
    """
    Reads all evidence rows for a user, fetches real GitHub metrics for each
    unique repo URL, then updates confidence with the new formula.
    """

    def __init__(self, user_id: str = "default", github_token: Optional[str] = None):
        self.user_id = user_id
        self.github = GitHubClient(token=github_token)
        self.analyzer = RepoAnalyzer()

    def enrich_all_projects(self) -> int:
        """
        Enrich all evidence rows for this user.

        Returns:
            Number of unique projects successfully enriched.
        """
        with db.session_scope() as session:
            repo = EvidenceRepository(session)
            all_evidence = repo.get_all_evidence_for_user(self.user_id)

            # Group by github_url (one API call per repo)
            projects: Dict[str, list] = {}
            for ev in all_evidence:
                if ev.github_url:
                    projects.setdefault(ev.github_url, []).append(ev)

            enriched = 0
            for url, evidence_list in projects.items():
                try:
                    metrics = self._fetch_metrics(url)
                    if not metrics:
                        continue

                    for ev in evidence_list:
                        ev.loc_count = metrics.get("loc_count")
                        ev.language = metrics.get("language")
                        ev.topics = metrics.get("topics", [])
                        ev.pr_count = metrics.get("pr_count")
                        ev.issue_count = metrics.get("issue_count")
                        ev.has_releases = metrics.get("has_releases")
                        ev.has_tests = metrics.get("has_tests")
                        ev.has_docs = metrics.get("has_docs")
                        ev.last_commit_date = metrics.get("last_commit_date")
                        ev.confidence = self._calc_confidence(ev, metrics)

                    enriched += 1
                    print(
                        f"  OK  {url.split('/')[-1]}: "
                        f"{metrics['loc_count']:,} LOC, "
                        f"{metrics['language']}, "
                        f"{len(metrics['topics'])} topics"
                    )

                except Exception as e:
                    print(f"  ERR {url}: {e}")

            return enriched

    def _fetch_metrics(self, github_url: str) -> Optional[Dict[str, Any]]:
        """Parse owner/repo from URL and call GitHub API."""
        parts = github_url.rstrip("/").split("/")
        if len(parts) < 2:
            return None
        full_name = f"{parts[-2]}/{parts[-1]}"
        repo = self.github.get_repo(full_name)
        return self.analyzer.analyze(repo)

    @staticmethod
    def _calc_confidence(evidence, metrics: Dict[str, Any]) -> float:
        """
        Upgraded confidence formula using real GitHub metrics.

        Components:
          base         (0.0–0.50) from evaluation_scores.technical_skills
          commit_bonus (0.0–0.20) author commits relative to 100
          star_bonus   (0.0–0.10) stars relative to 50
          loc_bonus    (0.0–0.15) LOC relative to 5 000
          quality_bonus(0.0–0.20) tests + docs + releases + PRs + issues
        """
        tech_score = (evidence.evaluation_scores or {}).get("technical_skills", 50)
        base = tech_score / 100.0

        commits = evidence.author_commits or 0
        commit_bonus = min(commits / 100.0, 0.20)

        stars = evidence.stars or 0
        star_bonus = min(stars / 50.0, 0.10)

        loc = metrics.get("loc_count") or 0
        loc_bonus = min(loc / 5000.0, 0.15)

        quality = 0.0
        if metrics.get("has_tests"):
            quality += 0.05
        if metrics.get("has_docs"):
            quality += 0.03
        if metrics.get("has_releases"):
            quality += 0.05
        if (metrics.get("pr_count") or 0) > 5:
            quality += 0.04
        if (metrics.get("issue_count") or 0) > 3:
            quality += 0.03

        return min(base + commit_bonus + star_bonus + loc_bonus + quality, 1.0)
