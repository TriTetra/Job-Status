"""Rate-limited GitHub API client wrapper."""

from typing import Optional

from github import Github, Repository

from shared.config import get_settings


class GitHubClient:
    """Thin wrapper around PyGithub with rate-limit reporting."""

    def __init__(self, token: Optional[str] = None):
        token = token or get_settings().github_token
        if not token:
            raise ValueError("GITHUB_TOKEN required for GitHub enrichment")
        self._client = Github(token)

    def get_repo(self, full_name: str) -> Repository.Repository:
        """Get repo by 'owner/name' string."""
        return self._client.get_repo(full_name)

    def get_user_repos(self, username: str):
        """Get all public repos for a user, sorted by last updated."""
        user = self._client.get_user(username)
        return user.get_repos(type="owner", sort="updated")

    def check_rate_limit(self) -> dict:
        # PyGithub 2.x: RateLimitOverview uses .rate (not .core)
        rate = self._client.get_rate_limit()
        core = rate.rate
        return {
            "remaining": core.remaining,
            "limit": core.limit,
            "reset": core.reset.isoformat(),
        }
