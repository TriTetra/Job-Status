"""Hacker News Algolia API client."""

import calendar
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests


class HackerNewsClient:
    BASE_URL = "https://hn.algolia.com/api/v1"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "CareerOS/1.0"})

    def search_stories(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        hits_per_page: int = 100,
        numeric_filters: Optional[List[str]] = None,
    ) -> List[Dict]:
        params: Dict = {"query": query, "hitsPerPage": hits_per_page}
        if tags:
            params["tags"] = ",".join(tags)
        if numeric_filters:
            params["numericFilters"] = ",".join(numeric_filters)

        resp = self.session.get(f"{self.BASE_URL}/search", params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("hits", [])

    def get_item(self, item_id: int) -> Optional[Dict]:
        resp = self.session.get(f"{self.BASE_URL}/items/{item_id}", timeout=30)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    def find_who_is_hiring_thread(self, year: int, month: int) -> Optional[Dict]:
        """Find the monthly 'Ask HN: Who is hiring?' thread."""
        first_day = datetime(year, month, 1)
        last_day = first_day + timedelta(days=7)
        start_ts = int(first_day.timestamp())
        end_ts = int(last_day.timestamp())

        results = self.search_stories(
            query="Ask HN: Who is hiring",
            tags=["story", "author_whoishiring"],
            numeric_filters=[f"created_at_i>{start_ts}", f"created_at_i<{end_ts}"],
            hits_per_page=10,
        )

        month_name = calendar.month_name[month]
        for story in results:
            title = story.get("title", "")
            if f"{month_name} {year}" in title or "Who is hiring" in title:
                return story

        return results[0] if results else None

    def get_top_level_comments(self, story_id: int) -> List[Dict]:
        item = self.get_item(story_id)
        if not item:
            return []
        return item.get("children", [])
