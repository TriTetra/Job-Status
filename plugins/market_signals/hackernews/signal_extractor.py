"""Extract MarketSignal rows from HN 'Who is hiring?' threads."""

from collections import Counter
from datetime import datetime
from typing import Optional

from packages.db.connection import db
from packages.db.repositories import MarketSignalRepository

from .client import HackerNewsClient
from .who_is_hiring_parser import WhoIsHiringParser


class HNSignalExtractor:
    def __init__(self):
        self.client = HackerNewsClient()
        self.parser = WhoIsHiringParser()

    def extract_monthly_signals(self, year: int, month: int) -> int:
        thread = self.client.find_who_is_hiring_thread(year, month)
        if not thread:
            print(f"  No thread found for {year}-{month:02d}")
            return 0

        thread_id = thread["objectID"]
        thread_title = thread.get("title", f"Who is Hiring {year}-{month:02d}")
        thread_url = f"https://news.ycombinator.com/item?id={thread_id}"
        thread_date = datetime.fromtimestamp(thread.get("created_at_i", 0))

        print(f"  Thread: {thread_title}")

        comments = self.client.get_top_level_comments(int(thread_id))
        print(f"  Comments: {len(comments)}")
        if not comments:
            return 0

        # Parse all job postings
        parsed = []
        for c in comments:
            try:
                job = self.parser.parse_comment(c)
                if job and job.get("company"):
                    parsed.append(job)
            except Exception:
                continue

        companies = [j["company"] for j in parsed]
        skills: list = []
        for j in parsed:
            skills.extend(j.get("skills", []))

        company_counts = Counter(companies)
        skill_counts = Counter(skills)
        remote_count = sum(1 for j in parsed if j.get("remote"))

        signals_created = 0

        with db.session_scope() as session:
            repo = MarketSignalRepository(session)

            # 1. Thread-level hiring volume
            repo.add_signal(
                signal_type="hiring_volume",
                source="hackernews",
                title=f"HN Who is Hiring: {len(parsed)} posts ({thread_title})",
                occurred_at=thread_date,
                source_id=f"hn_thread_{thread_id}",
                impact="high" if len(parsed) > 2000 else "medium",
                url=thread_url,
                magnitude=float(len(parsed)),
                metadata_json={"thread_id": thread_id, "year": year, "month": month},
            )
            signals_created += 1

            # 2. Top 20 skill demand signals
            for skill, count in skill_counts.most_common(20):
                repo.add_signal(
                    signal_type="skill_demand",
                    source="hackernews",
                    title=f"{skill}: {count} mentions in {thread_title}",
                    occurred_at=thread_date,
                    source_id=f"hn_skill_{thread_id}_{skill.lower().replace(' ', '_')}",
                    impact="high" if count > 50 else "medium",
                    skills_affected=[skill],
                    magnitude=float(count),
                    metadata_json={"skill": skill, "mention_count": count},
                )
                signals_created += 1

            # 3. Top 20 company hiring spikes
            for company, count in company_counts.most_common(20):
                slug = company.lower().replace(" ", "_")[:50]
                repo.add_signal(
                    signal_type="hiring_spike",
                    source="hackernews",
                    title=f"{company}: {count} open position(s) in {thread_title}",
                    occurred_at=thread_date,
                    source_id=f"hn_co_{thread_id}_{slug}",
                    impact="high" if count > 5 else "medium",
                    companies_affected=[company],
                    magnitude=float(count),
                    metadata_json={"company": company, "position_count": count},
                )
                signals_created += 1

            # 4. Remote % stat
            if parsed:
                pct = remote_count / len(parsed) * 100
                repo.add_signal(
                    signal_type="market_stat",
                    source="hackernews",
                    title=f"Remote: {pct:.1f}% of {thread_title} postings",
                    occurred_at=thread_date,
                    source_id=f"hn_remote_{thread_id}",
                    impact="medium",
                    magnitude=round(pct, 1),
                    metadata_json={"remote_count": remote_count, "total": len(parsed)},
                )
                signals_created += 1

        print(f"  Signals created: {signals_created}")
        return signals_created
