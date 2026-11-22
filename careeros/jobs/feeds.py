"""Job feed sync: read the feeds (careeros/jobs/sources/feeds), keep relevant titles,
store them as jobs, and remember every company job board they link to.

Feed postings are stored with source="feed" and site=<feed>. They keep the feed's
page as their link (the feeds' terms) and are closed once a feed stops listing them
for STALE_DAYS. When the company's own board is read too, its copy wins and the
feed copy is closed (see close_feed_duplicates), so a job never shows twice.
"""

import hashlib
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional

from sqlalchemy import func, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from careeros.db.connection import db
from careeros.jobs.boards import TitleFilter, load_boards
from careeros.jobs.discovery import FoundBoard, boards_in, company_site, key_for
from careeros.jobs.extraction import TextExtractor
from careeros.jobs.models.board_run import JobBoardRun
from careeros.jobs.models.discovered_board import DiscoveredBoard
from careeros.jobs.models.job import Job
from careeros.jobs.sources.ats import http_session
from careeros.jobs.sources.feeds import FEEDS, FeedPosting

logger = logging.getLogger(__name__)

SOURCE = "feed"
STALE_DAYS = 21          # a feed posting not listed for three weeks is gone
MAX_NEW_BOARDS = 40      # boards added per run (each is read on every sync after)
CHUNK = 200
MIN_INTERVAL_H = 11      # at most ~twice a day per feed (Remotive allows 4 requests a day)


@dataclass
class FeedResult:
    feed: str
    fetched: int = 0
    kept: int = 0
    new: int = 0
    seen: int = 0
    closed: int = 0
    duplicates: int = 0
    boards_found: int = 0
    error: Optional[str] = None
    duration_ms: int = 0


@dataclass
class FeedSummary:
    feeds: list[FeedResult] = field(default_factory=list)
    new_boards: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"feeds": [asdict(f) for f in self.feeds], "new_boards": self.new_boards}


def _http(url: Optional[str]) -> Optional[str]:
    return url if url and url.lower().startswith(("https://", "http://")) else None


def content_hash(p: FeedPosting) -> str:
    raw = "\x1f".join([p.title, p.company, p.location, p.description])
    return hashlib.sha256(raw.encode()).hexdigest()


def dedupe_key(company: str, title: str) -> tuple[str, str]:
    return (" ".join(company.lower().split()), " ".join(title.lower().split()))


def to_row(p: FeedPosting, extract: TextExtractor) -> dict:
    remote = p.remote if p.remote is not None else extract.is_remote(p.location, p.description)
    low, high, currency = p.salary_min, p.salary_max, p.salary_currency
    if not (low or high):
        low, high = extract.salary(p.description)
        currency = "USD" if low else None
    return {
        "url": p.url[:2048],
        "title": p.title[:512],
        "company": p.company[:256],
        "location": p.location[:256],
        "description": p.description,
        "employment_type": (p.employment_type or None) and p.employment_type[:64],
        "source": SOURCE,
        "site": p.source,
        "company_key": None,       # a board key would make the board sync close this row
        "ats": None,
        "external_id": p.external_id[:128],
        "application_url": _http(p.apply_url) or p.url,
        "salary_min": low,
        "salary_max": high,
        "salary_currency": currency,
        "required_years": extract.required_years(p.title, p.description),
        "company_size": extract.company_size(p.company),
        "remote": remote,
        "remote_region": extract.remote_region(p.location, p.description) if remote else None,
        "sponsors_visa": extract.sponsors_visa(p.description),
        "required_skills": extract.skills(p.description, p.title),
        "content_hash": content_hash(p),
        "posted_at": p.posted_at,
    }


def _board_jobs(session) -> set[tuple[str, str]]:
    """(company, title) of open jobs read from company boards: a feed copy of one is a duplicate."""
    rows = session.query(Job.company, Job.title).filter(Job.closed_at.is_(None), Job.source != SOURCE).all()
    return {dedupe_key(c or "", t or "") for c, t in rows}


def _write(rows: list[dict], now: datetime) -> int:
    """Upsert; returns how many were new."""
    with db.session_scope() as s:
        urls = [r["url"] for r in rows]
        known = {u for (u,) in s.query(Job.url).filter(Job.url.in_(urls)).all()} if urls else set()
        for i in range(0, len(rows), CHUNK):
            chunk = [{**r, "discovered_at": now, "last_seen_at": now, "closed_at": None} for r in rows[i:i + CHUNK]]
            stmt = pg_insert(Job).values(chunk)
            s.execute(stmt.on_conflict_do_update(
                index_elements=["url"],
                set_={k: stmt.excluded[k] for k in chunk[0] if k not in ("url", "discovered_at", "created_at")} | {"updated_at": now},
            ))
    return len(set(urls) - known)


def _close_stale(feed: str, now: datetime) -> int:
    with db.session_scope() as s:
        res = s.execute(update(Job).where(
            Job.source == SOURCE, Job.site == feed, Job.closed_at.is_(None),
            Job.last_seen_at < now - timedelta(days=STALE_DAYS),
        ).values(closed_at=now))
        return res.rowcount or 0


def _record(r: FeedResult, now: datetime) -> None:
    values = {"last_run_at": now, "last_error": r.error, "fetched": r.fetched, "kept": r.kept,
              "new": r.new, "updated": 0, "closed": r.closed, "duration_ms": r.duration_ms}
    if not r.error:
        values["last_success_at"] = now
    with db.session_scope() as s:
        stmt = pg_insert(JobBoardRun).values(company_key=f"feed:{r.feed}", **values)
        s.execute(stmt.on_conflict_do_update(index_elements=["company_key"], set_=values))


def remember_boards(found: dict[FoundBoard, FeedPosting], now: datetime, limit: int = MAX_NEW_BOARDS) -> list[str]:
    """Store boards not seen before (and not already in companies.yaml); refresh last_linked_at on known ones."""
    config = load_boards().boards
    configured = {(b.ats, b.board.lower()) for b in config}
    added: list[str] = []
    with db.session_scope() as s:
        existing = {(d.ats, d.board.lower()): d for d in s.query(DiscoveredBoard).all()}
        taken = {b.key for b in config} | {d.key for d in existing.values()}
        for fb, post in found.items():
            ident = (fb.ats, fb.board.lower())
            if ident in configured:
                continue
            if ident in existing:
                if existing[ident] is not None:
                    existing[ident].last_linked_at = now
                continue
            if len(added) >= limit:
                continue
            key = key_for(fb, taken)
            taken.add(key)
            s.add(DiscoveredBoard(
                key=key, name=post.company[:256] if post.company != "Unknown" else fb.board[:256],
                ats=fb.ats, board=fb.board, host=fb.host,
                domain=company_site(post.links) or "", source=post.source, source_url=post.url[:2048],
                discovered_at=now, last_linked_at=now, active=True, failures=0,
            ))
            existing[ident] = None  # type: ignore[assignment]  # don't add twice in one run
            added.append(key)
    return added


def due_feeds(session, names: Iterable[str], now: datetime, min_interval_h: float) -> list[str]:
    """Feeds whose last read (successful or not) is older than `min_interval_h`."""
    runs = {r.company_key: r.last_run_at for r in session.query(JobBoardRun)
            .filter(JobBoardRun.company_key.in_([f"feed:{n}" for n in names])).all()}
    cutoff = now - timedelta(hours=min_interval_h)
    return [n for n in names if (runs.get(f"feed:{n}") or cutoff) <= cutoff]


def sync_feeds(names: Optional[Iterable[str]] = None, *, dry_run: bool = False,
               titles: Optional[TitleFilter] = None, min_interval_h: float = 0) -> FeedSummary:
    """Read every feed (or `names`); with `min_interval_h`, only those not read that recently.
    Never raises for one feed failing: it is recorded."""
    now = datetime.now(timezone.utc)
    names = list(names) if names else list(FEEDS)
    if min_interval_h and not dry_run:
        with db.session_scope() as s:
            names = due_feeds(s, names, now, min_interval_h)
        if not names:
            return FeedSummary()
    if titles is None:
        titles = load_boards().titles
        if not dry_run:
            from careeros.jobs.targeting import role_terms
            with db.session_scope() as s:
                titles = titles.with_terms(role_terms(s))
    extract = TextExtractor()
    with db.session_scope() as s:
        on_boards = _board_jobs(s) if not dry_run else set()

    summary, found = FeedSummary(), {}
    for name in names:
        started = time.monotonic()
        r = FeedResult(feed=name)
        try:
            postings = FEEDS[name](http_session())
            r.fetched = len(postings)
            kept = [p for p in postings if _http(p.url) and p.title and titles.keeps(p.title)]
            r.kept = len(kept)
            rows = []
            for p in kept:
                for fb in boards_in([*p.links, p.apply_url or ""]):
                    found.setdefault(fb, p)
                if dedupe_key(p.company, p.title) in on_boards:
                    r.duplicates += 1
                    continue
                rows.append(to_row(p, extract))
            r.boards_found = len({fb for p in kept for fb in boards_in([*p.links, p.apply_url or ""])})
            r.seen = len(rows)
            if not dry_run:
                r.new = _write(rows, now)
                r.closed = _close_stale(name, now)
        except Exception as e:
            logger.warning("[feed:%s] failed: %s", name, e)
            r.error = f"{type(e).__name__}: {e}"[:500]
        r.duration_ms = int((time.monotonic() - started) * 1000)
        if not dry_run:
            try:
                _record(r, now)
            except Exception:
                logger.exception("[feed:%s] could not record result", name)
        summary.feeds.append(r)

    if not dry_run and found:
        summary.new_boards = remember_boards(found, now)
    logger.info("Feed sync: %s; %d new boards",
                ", ".join(f"{f.feed} {f.kept} kept/{f.new} new" + (" FAILED" if f.error else "") for f in summary.feeds),
                len(summary.new_boards))
    return summary


def close_feed_duplicates(session) -> int:
    """Close feed copies of jobs now read from the company's own board (same company + title)."""
    res = session.execute(text("""
        UPDATE jobs f SET closed_at = now()
          FROM jobs b
         WHERE f.source = 'feed' AND f.closed_at IS NULL
           AND b.source <> 'feed' AND b.closed_at IS NULL
           AND lower(btrim(b.company)) = lower(btrim(f.company))
           AND lower(btrim(b.title)) = lower(btrim(f.title))
    """))
    return res.rowcount or 0


def feed_status(session) -> list[dict]:
    runs = {r.company_key: r for r in session.query(JobBoardRun).filter(JobBoardRun.company_key.like("feed:%")).all()}
    open_counts = dict(session.query(Job.site, func.count()).filter(Job.source == SOURCE, Job.closed_at.is_(None))
                       .group_by(Job.site).all())
    out = []
    for name in FEEDS:
        r = runs.get(f"feed:{name}")
        out.append({"feed": name, "open_jobs": open_counts.get(name, 0),
                    "last_run_at": r.last_run_at.isoformat() if r else None,
                    "last_error": r.last_error if r else None, "last_new": r.new if r else 0})
    return out
