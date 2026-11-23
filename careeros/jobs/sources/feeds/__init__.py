"""Job feeds: sites listing many companies' jobs. Each module exposes `fetch(http) -> list[FeedPosting]`."""

from careeros.jobs.sources.feeds import adzuna, arbeitnow, hackernews, himalayas, jobicy, remotive
from careeros.jobs.sources.feeds.base import FeedFetcher, FeedPosting

FEEDS: dict[str, FeedFetcher] = {
    "hackernews": hackernews.fetch,
    "arbeitnow": arbeitnow.fetch,
    "remotive": remotive.fetch,
    "himalayas": himalayas.fetch,
    "jobicy": jobicy.fetch,
    "adzuna": adzuna.fetch,      # off until ADZUNA_APP_ID / ADZUNA_APP_KEY are set
}

# Shown next to each posting: the feeds ask to be credited
LABELS = {
    "hackernews": "Hacker News",
    "arbeitnow": "Arbeitnow",
    "remotive": "Remotive",
    "himalayas": "Himalayas",
    "jobicy": "Jobicy",
    "adzuna": "Adzuna",
}

__all__ = ["FEEDS", "LABELS", "FeedPosting"]
