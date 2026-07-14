"""
Import all jobs from ApplyPilot SQLite into the PostgreSQL jobs table.

Usage:
    python scripts/sync_jobs_from_applypilot.py [--min-score 0] [--hours 0]

After running, the project's PostgreSQL is the single source of truth
for all job data. The SQLite file is read-only input and not needed again
unless new jobs are scanned by ApplyPilot.
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from core.db.connection import db
from core.db.repositories import JobRepository
from plugins.plugin_loader import load_job_source_plugin


def _parse_dt(val) -> datetime | None:
    if not val:
        return None
    try:
        dt = datetime.fromisoformat(str(val))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def sync(min_score: int = 0, hours: int = 0) -> int:
    plugin = load_job_source_plugin("applypilot")

    meta = plugin.get_metadata()
    print(f"Source: {meta['db_path']}")
    print(f"Total jobs in SQLite: {meta['job_count']}")

    raw_jobs = plugin.scan(hours_old=hours, min_score=min_score)
    print(f"Fetched: {len(raw_jobs)} jobs (min_score={min_score}, hours={hours or 'all'})")

    if not raw_jobs:
        print("Nothing to sync.")
        return 0

    rows = []
    for raw in raw_jobs:
        normalized = plugin.normalize(raw)

        # Map to DB model fields (strip keys that don't exist in jobs table)
        row = {
            "url": normalized["url"],
            "title": normalized["title"] or "",
            "company": normalized["company"] or "",
            "location": normalized["location"] or "",
            "description": normalized["description"] or "",
            "full_description": raw.get("full_description"),
            "site": normalized.get("source") or raw.get("site"),
            "source": "applypilot",
            "application_url": normalized.get("application_url"),
            "fit_score": normalized.get("fit_score"),
            "score_reasoning": normalized.get("score_reasoning"),
            "salary_min": normalized.get("salary_min"),
            "salary_max": normalized.get("salary_max"),
            "required_years": normalized.get("required_years"),
            "company_size": normalized.get("company_size"),
            "remote": normalized.get("remote"),
            "required_skills": normalized.get("required_skills") or [],
            "discovered_at": _parse_dt(normalized.get("posted_date") or raw.get("discovered_at")),
        }
        rows.append(row)

    batch_size = 200
    total_upserted = 0
    with db.session_scope() as session:
        repo = JobRepository(session)
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            count = repo.upsert_many(batch)
            total_upserted += count
            print(f"  Upserted batch {i // batch_size + 1}: {len(batch)} rows")

    print(f"\nDone. {total_upserted} total rows upserted into PostgreSQL jobs table.")
    return total_upserted


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync ApplyPilot SQLite jobs to PostgreSQL")
    parser.add_argument("--min-score", type=int, default=0, help="Minimum fit_score (default: 0 = all)")
    parser.add_argument("--hours", type=int, default=0, help="Only jobs from last N hours (default: 0 = all)")
    args = parser.parse_args()

    try:
        sync(min_score=args.min_score, hours=args.hours)
        return 0
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("Make sure ApplyPilot has been run at least once to create the database.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
