"""Extract MarketSignal rows from HN 'Who is hiring?' threads.

Hybrid skill detection:
  Layer 1 — seed keywords + market_skills registry (fast, free)
  Layer 2 — LLM for comments the regex couldn't read (capped budget)
  Learning — LLM-discovered skills are promoted into market_skills,
             so the next scan recognizes them without another LLM call.
"""

import logging
import re as _re
from collections import Counter
from datetime import datetime
from typing import List

from careeros.db.connection import db
from careeros.market.repositories.market_signal_repo import MarketSignalRepository

from careeros.market.sources.hackernews.client import HackerNewsClient
from careeros.market.sources.hackernews.who_is_hiring_parser import WhoIsHiringParser

logger = logging.getLogger(__name__)


class HNSignalExtractor:
    def __init__(self):
        self.client = HackerNewsClient()
        self.parser = WhoIsHiringParser()

    def extract_monthly_signals(
        self,
        year: int,
        month: int,
        use_llm: bool = True,
        llm_budget: int = 4,   # max LLM batch calls per run (~$0.02)
        batch_size: int = 8,   # comments per LLM call
    ) -> int:
        thread = self.client.find_who_is_hiring_thread(year, month)
        if not thread:
            logger.info("No HN who-is-hiring thread for %d-%02d", year, month)
            return 0

        thread_id = thread["objectID"]
        thread_title = thread.get("title", f"Who is Hiring {year}-{month:02d}")
        thread_url = f"https://news.ycombinator.com/item?id={thread_id}"
        thread_date = datetime.fromtimestamp(thread.get("created_at_i", 0))

        logger.info("HN thread: %s", thread_title)

        comments = self.client.get_top_level_comments(int(thread_id))
        logger.info("HN comments: %d", len(comments))
        if not comments:
            return 0

        # ── Layer 1: regex fast path ──────────────────────────────────────
        parsed: List[dict] = []
        regex_skills: List[str] = []
        weak_comments: List[str] = []   # comment texts that yielded no skills

        for c in comments:
            try:
                job = self.parser.parse_comment(c)
            except Exception:
                job = {}

            if job and job.get("company"):
                parsed.append(job)
                skills = job.get("skills", [])
                regex_skills.extend(skills)
                if not skills:
                    # company found but no skills → candidate for LLM
                    weak_comments.append(c.get("text") or "")
            else:
                # no company → LLM might still recover it
                weak_comments.append(c.get("text") or "")

        logger.info("Layer-1: %d postings parsed, %d weak", len(parsed), len(weak_comments))

        # ── Layer 2: LLM on capped sample of weak comments ───────────────
        llm_skills: List[str] = []
        llm_count = 0

        if use_llm and weak_comments:
            try:
                from careeros.market.sources.hackernews.llm_extractor import extract_batch
            except ImportError:
                use_llm = False

        if use_llm and weak_comments:
            # Strip HTML, filter very short texts, cap to budget
            clean = [_re.sub(r"<[^>]+>", " ", t) for t in weak_comments]
            clean = [t.strip() for t in clean if len(t.strip()) > 60]
            clean = clean[: llm_budget * batch_size]

            for i in range(0, len(clean), batch_size):
                batch = clean[i : i + batch_size]
                try:
                    jobs = extract_batch(batch)
                except Exception as e:
                    logger.warning("LLM batch %d failed: %s", i // batch_size + 1, e)
                    continue

                llm_count += len(jobs)
                for j in jobs:
                    if not j.company:
                        continue
                    parsed.append(
                        {
                            "company": j.company,
                            "role": j.role,
                            "remote": j.remote,
                            "sponsors_visa": j.sponsors_visa,
                            "skills": j.skills,
                            "url": None,
                            "description": "",
                        }
                    )
                    llm_skills.extend(j.skills)

            logger.info("Layer-2: LLM recovered %d postings", llm_count)

        # ── Learning: promote into registry, get canonical names ──────────
        from careeros.market.sources.skill_registry import record_mentions

        with db.session_scope() as session:
            canon_regex = record_mentions(session, regex_skills, source="seed_match")
            canon_llm = record_mentions(session, llm_skills, source="llm_discovered")
            session.commit()

        # ── Aggregate ─────────────────────────────────────────────────────
        companies = [j["company"] for j in parsed]
        company_counts = Counter(companies)
        skill_counts = Counter(canon_regex + canon_llm)
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

            # 2. Top 20 skill demand (canonical + learned names)
            for skill, count in skill_counts.most_common(20):
                repo.add_signal(
                    signal_type="skill_demand",
                    source="hackernews",
                    title=f"{skill}: {count} mentions in {thread_title}",
                    occurred_at=thread_date,
                    source_id=f"hn_skill_{thread_id}_{skill.lower().replace(' ', '_')[:40]}",
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

        logger.info("HN signals created: %d", signals_created)
        return signals_created
