"""Company board sync: fetch → keep relevant titles → upsert into `jobs` → close what disappeared.

Shared by all users. Incremental: an unchanged posting only gets `last_seen_at`
touched; a changed one gets a new content_hash (so scans rescore it); one that
left the board gets `closed_at`. Runs are serialized with a Postgres advisory
lock, so the scheduler and a CLI run never overlap.
"""

import hashlib
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Optional

from sqlalchemy import text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from careeros.db.connection import db
from careeros.jobs.boards import TitleFilter, load_boards
from careeros.jobs.extraction import TextExtractor
from careeros.jobs.models.board_run import JobBoardRun
from careeros.jobs.models.job import Job
from careeros.jobs.sources.ats import FETCHERS, Board, Posting, http_session
from careeros.shared.background import BackgroundJob, JobStore

logger = logging.getLogger(__name__)

WORKERS = 6        # boards fetched in parallel
CHUNK = 200        # rows per upsert statement
_LOCK_KEY = 0x4A0B5  # pg advisory lock id for "job sync"


class SyncBusy(RuntimeError):
    """Another sync holds the lock."""


@dataclass
class BoardResult:
    key: str
    name: str
    ats: str
    fetched: int = 0
    kept: int = 0
    new: int = 0
    updated: int = 0
    unchanged: int = 0
    closed: int = 0
    complete: bool = True
    error: Optional[str] = None
    duration_ms: int = 0


@dataclass
class SyncSummary:
    boards: list[BoardResult] = field(default_factory=list)

    @property
    def totals(self) -> dict:
        keys = ("fetched", "kept", "new", "updated", "unchanged", "closed")
        out = {k: sum(getattr(b, k) for b in self.boards) for k in keys}
        out["failed"] = sum(1 for b in self.boards if b.error)
        return out

    def to_dict(self) -> dict:
        return {"totals": self.totals, "boards": [asdict(b) for b in self.boards]}


def _http(url: Optional[str]) -> Optional[str]:
    """Board data is untrusted: only http(s) links are stored (no javascript:/data: hrefs)."""
    return url if url and url.lower().startswith(("https://", "http://")) else None


def content_hash(p: Posting) -> str:
    raw = "\x1f".join([p.title, p.location, p.description, p.apply_url or ""])
    return hashlib.sha256(raw.encode()).hexdigest()


def to_row(board: Board, p: Posting, extract: TextExtractor) -> dict:
    desc = p.description
    remote = p.remote if p.remote is not None else extract.is_remote(p.location, desc)
    low, high, currency = p.salary_min, p.salary_max, p.salary_currency
    if not (low or high):
        low, high = extract.salary(desc)
        currency = "USD" if low else None
    return {
        "url": p.url,
        "title": p.title[:512],
        "company": board.name,
        "location": p.location[:256],
        "description": desc,
        "department": (p.department or None) and p.department[:256],
        "employment_type": (p.employment_type or None) and p.employment_type[:64],
        "source": board.ats,
        "site": board.ats,
        "company_key": board.key,
        "ats": board.ats,
        "external_id": p.external_id[:128],
        "application_url": _http(p.apply_url) or p.url,
        "salary_min": low,
        "salary_max": high,
        "salary_currency": currency,
        "required_years": extract.required_years(p.title, desc),
        "company_size": extract.company_size(board.name),
        "remote": remote,
        "remote_region": extract.remote_region(p.location, desc) if remote else None,
        "sponsors_visa": extract.sponsors_visa(desc),
        "required_skills": extract.skills(desc, p.title),
        "content_hash": content_hash(p),
        "posted_at": p.posted_at,
    }


def _known(key: str) -> dict[str, tuple[Optional[str], Optional[datetime]]]:
    with db.session_scope() as s:
        rows = s.query(Job.url, Job.content_hash, Job.closed_at).filter(Job.company_key == key).all()
    return {url: (h, closed) for url, h, closed in rows}


def _write(board: Board, rows: list[dict], touched: list[str], to_close: list[str], now: datetime) -> None:
    with db.session_scope() as s:
        for i in range(0, len(rows), CHUNK):
            chunk = [{**r, "discovered_at": now, "last_seen_at": now, "closed_at": None} for r in rows[i:i + CHUNK]]
            stmt = pg_insert(Job).values(chunk)
            keep_first_seen = {"url", "discovered_at", "created_at"}
            stmt = stmt.on_conflict_do_update(
                index_elements=["url"],
                set_={k: stmt.excluded[k] for k in chunk[0] if k not in keep_first_seen} | {"updated_at": now},
            )
            s.execute(stmt)
        for i in range(0, len(touched), 1000):
            s.execute(update(Job).where(Job.url.in_(touched[i:i + 1000])).values(last_seen_at=now, closed_at=None))
        for i in range(0, len(to_close), 1000):
            s.execute(update(Job).where(Job.url.in_(to_close[i:i + 1000])).values(closed_at=now))


def _record(r: BoardResult, now: datetime) -> None:
    values = {
        "last_run_at": now, "last_error": r.error, "fetched": r.fetched, "kept": r.kept,
        "new": r.new, "updated": r.updated, "closed": r.closed, "duration_ms": r.duration_ms,
    }
    if not r.error:
        values["last_success_at"] = now
    with db.session_scope() as s:
        stmt = pg_insert(JobBoardRun).values(company_key=r.key, **values)
        s.execute(stmt.on_conflict_do_update(index_elements=["company_key"], set_=values))


def sync_board(board: Board, titles: TitleFilter, *, dry_run: bool = False,
               extract: Optional[TextExtractor] = None) -> BoardResult:
    """Sync one board. Never raises: failures are recorded on the result (and in job_board_runs)."""
    started, now = time.monotonic(), datetime.now(timezone.utc)
    result = BoardResult(key=board.key, name=board.name, ats=board.ats)
    extract = extract or TextExtractor()
    try:
        known = {} if dry_run else _known(board.key)
        fetched = FETCHERS[board.ats](board, http_session(), set(known), titles.keeps)
        seen = {p.url for p in fetched.postings} | fetched.seen_urls
        result.fetched, result.complete = len(seen), fetched.complete

        rows, touched = [], []
        for p in fetched.postings:
            if not (_http(p.url) and p.title and titles.keeps(p.title)):
                continue
            row = to_row(board, p, extract)
            old = known.get(p.url)
            if old is None:
                result.new += 1
                rows.append(row)
            elif old[0] != row["content_hash"] or old[1] is not None:
                result.updated += 1
                rows.append(row)
            else:
                result.unchanged += 1
                touched.append(p.url)
        # Workday: stored postings are listed but not re-fetched — still open, unchanged
        handled = {r["url"] for r in rows} | set(touched)
        relisted = [u for u in fetched.seen_urls if u in known and u not in handled]
        touched += relisted
        result.unchanged += len(relisted)
        result.kept = result.new + result.updated + result.unchanged

        to_close = []
        if fetched.complete:
            to_close = [u for u, (_, closed) in known.items() if closed is None and u not in seen]
        result.closed = len(to_close)
        if not dry_run:
            _write(board, rows, touched, to_close, now)
    except Exception as e:
        logger.warning("[%s] sync failed: %s", board.key, e)
        result.error = f"{type(e).__name__}: {e}"[:500]
    result.duration_ms = int((time.monotonic() - started) * 1000)
    if not dry_run:
        try:
            _record(result, now)
        except Exception:
            logger.exception("[%s] could not record sync result", board.key)
    return result


@contextmanager
def _sync_lock():
    with db.engine.connect() as conn:
        if not conn.execute(text("SELECT pg_try_advisory_lock(:k)"), {"k": _LOCK_KEY}).scalar():
            raise SyncBusy("A job sync is already running")
        try:
            yield
        finally:
            conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": _LOCK_KEY})


def sync_all(keys: Optional[Iterable[str]] = None, *, dry_run: bool = False,
             workers: int = WORKERS) -> SyncSummary:
    """Sync every configured board (or just `keys`). Raises SyncBusy if a sync is running."""
    config = load_boards()
    boards = config.select(keys)
    titles = config.titles
    if not dry_run:
        from careeros.jobs.targeting import role_terms
        with db.session_scope() as s:
            titles = titles.with_terms(role_terms(s))

    extract = TextExtractor()
    run = lambda b: sync_board(b, titles, dry_run=dry_run, extract=extract)  # noqa: E731

    def _run_all() -> SyncSummary:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            summary = SyncSummary(boards=list(pool.map(run, boards)))
        t = summary.totals
        logger.info("Job sync: %d boards, %d kept, %d new, %d updated, %d closed, %d failed",
                    len(boards), t["kept"], t["new"], t["updated"], t["closed"], t["failed"])
        return summary

    if dry_run:
        return _run_all()
    with _sync_lock():
        return _run_all()


def import_rows(normalized: list[dict]) -> int:
    """Upsert jobs from an import source (ApplyPilot's normalized dicts). Never auto-closed."""
    now = datetime.now(timezone.utc)
    rows = []
    for j in normalized:
        if not j.get("url"):
            continue
        desc = j.get("description") or ""
        rows.append({
            "url": j["url"][:2048],
            "title": (j.get("title") or "")[:512],
            "company": (j.get("company") or "")[:256],
            "location": (j.get("location") or "")[:256],
            "description": desc,
            "source": "applypilot",
            "site": j.get("source"),
            "application_url": j.get("application_url"),
            "fit_score": j.get("fit_score"),
            "score_reasoning": j.get("score_reasoning"),
            "salary_min": j.get("salary_min"),
            "salary_max": j.get("salary_max"),
            "required_years": j.get("required_years"),
            "company_size": j.get("company_size"),
            "remote": j.get("remote"),
            "remote_region": j.get("remote_region"),
            "sponsors_visa": j.get("sponsors_visa"),
            "required_skills": j.get("required_skills") or [],
            "content_hash": hashlib.sha256(f"{j.get('title')}\x1f{j.get('location')}\x1f{desc}".encode()).hexdigest(),
        })
    with db.session_scope() as s:
        for i in range(0, len(rows), CHUNK):
            chunk = [{**r, "discovered_at": now, "last_seen_at": now} for r in rows[i:i + CHUNK]]
            stmt = pg_insert(Job).values(chunk)
            s.execute(stmt.on_conflict_do_update(
                index_elements=["url"],
                set_={k: stmt.excluded[k] for k in chunk[0] if k not in ("url", "discovered_at")},
            ))
    return len(rows)


# ── status + on-demand runs (API) ─────────────────────────────────────────

sync_jobs = JobStore()
SYNC_LABEL = "job-sync"


def board_status(session) -> list[dict]:
    """Every configured board with its open postings and last sync outcome."""
    from sqlalchemy import func

    runs = {r.company_key: r for r in session.query(JobBoardRun).all()}
    open_counts = dict(
        session.query(Job.company_key, func.count()).filter(Job.closed_at.is_(None)).group_by(Job.company_key).all()
    )
    out = []
    for b in load_boards().boards:
        r = runs.get(b.key)
        out.append({
            "key": b.key, "name": b.name, "ats": b.ats,
            "open_jobs": open_counts.get(b.key, 0),
            "last_run_at": r.last_run_at.isoformat() if r else None,
            "last_success_at": r.last_success_at.isoformat() if r and r.last_success_at else None,
            "last_error": r.last_error if r else None,
            "last_new": r.new if r else 0,
        })
    return out


def run_sync_job(job: BackgroundJob, user_id: str) -> None:
    """Background task: sync all boards, then rescore the user who asked."""
    from careeros.jobs.scan import run_scan, scan_jobs

    try:
        job.update(status="syncing", progress=10)
        job.log("Reading company career boards…")
        totals = sync_all().totals
        job.log(f"✓ {totals['new']} new · {totals['updated']} updated · {totals['closed']} closed"
                + (f" · {totals['failed']} boards failed" if totals["failed"] else ""))
        job.update(status="scoring", progress=70)
        scan = scan_jobs.create(user_id, label="scan after sync")
        run_scan(scan, user_id)
        for line in scan.logs:
            job.log(line["message"], line.get("type", "info"))
        if scan.status != "completed":
            job.update(status="failed", error=scan.error, result={"sync": totals})
            return
        job.update(status="completed", progress=100, result={"sync": totals, "scan": scan.result})
    except SyncBusy as e:
        job.fail(e, "Another sync is already running — try again in a few minutes.")
    except Exception as e:
        logger.exception("Job sync failed")
        job.fail(e)
