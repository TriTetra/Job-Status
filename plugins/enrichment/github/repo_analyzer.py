"""Extract real metrics from a GitHub repository."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict


class RepoAnalyzer:
    """Extracts LOC, language, topics, PRs, tests, docs, commit frequency."""

    def analyze(self, repo) -> Dict[str, Any]:
        """
        Analyze a PyGithub Repository object.

        Returns:
            loc_count, language, languages, topics, pr_count, issue_count,
            has_releases, has_tests, has_docs, last_commit_date,
            commit_frequency (commits/week last 3 months), readme_length
        """
        # PyGithub 2.x includes a 'url' key; filter to integer values only
        languages = {k: int(v) for k, v in repo.get_languages().items() if isinstance(v, int)}
        total_loc = sum(languages.values())
        primary_language = max(languages, key=languages.get) if languages else None

        topics = list(repo.get_topics())

        pr_count = repo.get_pulls(state="all").totalCount
        issue_count = repo.get_issues(state="all").totalCount

        has_releases = repo.get_releases().totalCount > 0

        has_tests = self._detect_tests(repo)
        has_docs = self._detect_docs(repo)

        commits = list(repo.get_commits()[:1])
        last_commit_date = commits[0].commit.author.date if commits else None

        commit_frequency = self._calc_commit_frequency(repo)

        readme_length = 0
        try:
            readme_length = len(repo.get_readme().decoded_content)
        except Exception:
            pass

        return {
            "loc_count": total_loc,
            "language": primary_language,
            "languages": languages,
            "topics": topics,
            "pr_count": pr_count,
            "issue_count": issue_count,
            "has_releases": has_releases,
            "has_tests": has_tests,
            "has_docs": has_docs,
            "last_commit_date": last_commit_date,
            "commit_frequency": commit_frequency,
            "readme_length": readme_length,
        }

    def _detect_tests(self, repo) -> bool:
        test_markers = {"tests", "test", "pytest.ini", "setup.cfg", "jest.config.js"}
        try:
            for item in repo.get_contents(""):
                if item.name.lower() in test_markers:
                    return True
                if "test" in item.name.lower() and item.type == "dir":
                    return True
        except Exception:
            pass
        return False

    def _detect_docs(self, repo) -> bool:
        try:
            repo.get_readme()
            for item in repo.get_contents(""):
                if item.name.lower() in {"docs", "documentation", "wiki"}:
                    return True
        except Exception:
            pass
        return False

    def _calc_commit_frequency(self, repo) -> float:
        since = datetime.now(tz=timezone.utc) - timedelta(days=90)
        try:
            count = repo.get_commits(since=since).totalCount
            return count / 13.0  # 13 weeks ≈ 3 months
        except Exception:
            return 0.0
