"""GitHub API client for repository analysis."""

import requests
import logging

logger = logging.getLogger(__name__)


class GitHubAnalyzer:
    """Analyze GitHub repositories for skill extraction."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }
    
    def get_top_repos(self, limit: int = 20) -> list[dict]:
        """Get user's top repositories by activity."""
        repos = []
        page = 1
        
        while len(repos) < limit:
            response = requests.get(
                f"{self.BASE_URL}/user/repos",
                headers=self.headers,
                params={
                    "sort": "pushed",
                    "direction": "desc",
                    "per_page": min(100, limit - len(repos)),
                    "page": page,
                    "type": "owner",  # Only user's own repos
                },
                timeout=15,
            )
            
            if response.status_code != 200:
                logger.error(f"GitHub repos fetch failed: {response.status_code}")
                break
            
            page_repos = response.json()
            if not page_repos:
                break
            
            for repo in page_repos:
                # Skip forks and archived repos
                if repo.get("fork") or repo.get("archived"):
                    continue
                
                # Get detailed language breakdown
                languages = self._get_repo_languages(repo["full_name"])
                
                repos.append({
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "description": repo.get("description"),
                    "language": repo.get("language"),
                    "languages": languages,
                    "stars": repo.get("stargazers_count", 0),
                    "commits_count": self._estimate_commits(repo),
                    "last_push": repo.get("pushed_at"),
                    "url": repo.get("html_url"),
                })
                
                if len(repos) >= limit:
                    break
            
            page += 1
            
            # Safety limit
            if page > 5:
                break
        
        logger.info(f"Fetched {len(repos)} repos from GitHub")
        return repos
    
    def _get_repo_languages(self, full_name: str) -> dict[str, int]:
        """Get language breakdown for a repo (bytes per language)."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/repos/{full_name}/languages",
                headers=self.headers,
                timeout=10,
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to get languages for {full_name}: {e}")
        return {}
    
    def _estimate_commits(self, repo: dict) -> int:
        """Estimate commit count (GitHub API doesn't provide this directly)."""
        # Use size as a rough proxy (KB)
        size_kb = repo.get("size", 0)
        # Rough estimate: 1 commit per 50KB of code
        return max(1, size_kb // 50)
