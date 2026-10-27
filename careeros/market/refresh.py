"""Market refresh: crawl HN "Who is hiring?" + TechCrunch into market signals.

Market data is global (not per user), so at most one refresh runs at a time and
any signed-in user may poll it.
"""

import logging
from datetime import datetime

from careeros.shared.background import BackgroundJob, JobStore

logger = logging.getLogger(__name__)

refresh_jobs = JobStore()
REFRESH_LABEL = "market_refresh"


def start_refresh(user_id: str) -> tuple[BackgroundJob, bool]:
    """(job, created). Returns the in-flight job instead of starting a second crawl."""
    return refresh_jobs.create_unless_active(user_id, REFRESH_LABEL)


def run_refresh(job: BackgroundJob, hours: int) -> None:
    """Background task. Each source is independent: one failing does not stop the other."""
    from careeros.market.sources.hackernews.signal_extractor import HNSignalExtractor
    from careeros.market.sources.techcrunch.signal_extractor import TechCrunchSignalExtractor

    job.update(status="running", progress=10)

    now = datetime.utcnow()
    job.log("Scanning HackerNews Who is Hiring…")
    try:
        count = HNSignalExtractor().extract_monthly_signals(now.year, now.month)
        job.log(f"✓ HackerNews: {count} signals")
    except Exception as e:
        logger.warning("HackerNews refresh failed: %s", e)
        job.log(f"⚠ HackerNews skipped: {e}", "warning")

    job.progress = 60
    job.log(f"Scanning TechCrunch (last {hours}h)…")
    try:
        count = TechCrunchSignalExtractor().extract_signals(hours=hours)
        job.log(f"✓ TechCrunch: {count} signals")
    except Exception as e:
        logger.warning("TechCrunch refresh failed: %s", e)
        job.log(f"⚠ TechCrunch skipped: {e}", "warning")

    job.update(status="completed", progress=100)
    job.log("✓ Refresh complete")
