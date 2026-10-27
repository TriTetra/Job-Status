"""TechCrunch RSS feed reader."""

from datetime import datetime
from typing import Dict, List

import feedparser


class TechCrunchClient:
    FEEDS = {
        "main": "https://techcrunch.com/feed/",
        "startups": "https://techcrunch.com/category/startups/feed/",
        "ai": "https://techcrunch.com/category/artificial-intelligence/feed/",
    }

    def get_recent_articles(self, feed_name: str = "main", hours: int = 168) -> List[Dict]:
        url = self.FEEDS.get(feed_name, self.FEEDS["main"])
        feed = feedparser.parse(url)

        cutoff = datetime.utcnow().timestamp() - hours * 3600
        articles = []

        for entry in feed.entries:
            published = entry.get("published_parsed")
            if published:
                pub_ts = datetime(*published[:6]).timestamp()
                if pub_ts < cutoff:
                    continue
                pub_dt = datetime(*published[:6])
            else:
                pub_dt = datetime.utcnow()

            articles.append({
                "title": entry.get("title", ""),
                "summary": entry.get("summary", ""),
                "url": entry.get("link", ""),
                "published": pub_dt,
            })

        return articles
