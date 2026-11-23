"""`career-os jobs …` — company boards, sync, scoring."""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import typer

app = typer.Typer(help="Company boards, sync and scoring", no_args_is_help=True)


@app.command()
def sync(
    company: Optional[List[str]] = typer.Option(None, "--company", "-c", help="Company key (repeatable); default all"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Fetch and filter only; no database writes"),
):
    """Fetch every company board, store relevant postings, close the ones that are gone."""
    from careeros.jobs.boards import BoardConfigError
    from careeros.jobs.ingest import SyncBusy, sync_all

    try:
        summary = sync_all(company, dry_run=dry_run)
    except (BoardConfigError, SyncBusy) as e:
        typer.echo(f"✗ {e}", err=True)
        raise typer.Exit(1)

    typer.echo(f"\n{'company':<16}{'ats':<11}{'board':>6}{'kept':>6}{'new':>5}{'upd':>5}{'closed':>7}  time")
    for b in sorted(summary.boards, key=lambda b: (b.error is None, b.key)):
        if b.error:
            typer.echo(f"{b.key:<16}{b.ats:<11}  ✗ {b.error[:90]}")
            continue
        partial = "" if b.complete else "  (partial)"
        typer.echo(f"{b.key:<16}{b.ats:<11}{b.fetched:>6}{b.kept:>6}{b.new:>5}{b.updated:>5}{b.closed:>7}"
                   f"  {b.duration_ms / 1000:.1f}s{partial}")
    t = summary.totals
    typer.echo(f"\n{len(summary.boards)} boards · {t['kept']} relevant · {t['new']} new · {t['updated']} updated · "
               f"{t['closed']} closed · {t['failed']} failed" + ("  [dry run]" if dry_run else ""))


@app.command()
def feeds(
    feed: Optional[List[str]] = typer.Option(None, "--feed", "-f", help="Feed key (repeatable); default all"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Fetch and filter only; no database writes"),
):
    """Read the job feeds (Hacker News, Arbeitnow, Remotive, Himalayas, Jobicy) and remember the
    company boards they link to. Remotive allows ~4 requests a day: don't loop this."""
    from careeros.jobs.feeds import sync_feeds
    from careeros.jobs.sources.feeds import FEEDS

    unknown = set(feed or []) - set(FEEDS)
    if unknown:
        typer.echo(f"✗ Unknown feed(s): {', '.join(sorted(unknown))} (use {', '.join(FEEDS)})", err=True)
        raise typer.Exit(1)
    summary = sync_feeds(feed, dry_run=dry_run)
    typer.echo(f"\n{'feed':<12}{'fetched':>8}{'kept':>6}{'new':>5}{'dup':>5}{'boards':>7}{'closed':>7}  time")
    for f in summary.feeds:
        if f.error:
            typer.echo(f"{f.feed:<12}  ✗ {f.error[:90]}")
            continue
        typer.echo(f"{f.feed:<12}{f.fetched:>8}{f.kept:>6}{f.new:>5}{f.duplicates:>5}{f.boards_found:>7}{f.closed:>7}"
                   f"  {f.duration_ms / 1000:.1f}s")
    if summary.new_boards:
        typer.echo(f"\nNew company boards: {', '.join(summary.new_boards)}")
    typer.echo("  [dry run]" if dry_run else "")


@app.command()
def boards():
    """Configured boards with the outcome of their last sync."""
    from careeros.db.connection import db
    from careeros.jobs.ingest import board_status

    with db.session_scope() as s:
        rows = board_status(s)
    now = datetime.now(timezone.utc)
    typer.echo(f"\n{'company':<16}{'ats':<11}{'open':>6}  last sync")
    for b in rows:
        if b["last_run_at"] is None:
            status = "never"
        elif b["last_error"]:
            status = f"✗ {b['last_error'][:70]}"
        else:
            age = (now - datetime.fromisoformat(b["last_run_at"])).total_seconds() / 3600
            status = f"✓ {age:.1f} h ago"
        typer.echo(f"{b['key']:<16}{b['ats']:<11}{b['open_jobs']:>6}  {status}")
    typer.echo(f"\n{sum(b['open_jobs'] for b in rows)} open postings on {len(rows)} boards")


@app.command()
def scan(
    email: str = typer.Argument(..., help="Whose opportunities to score"),
    limit: int = typer.Option(2000, "--limit", help="Max jobs to score in this run"),
):
    """Score open jobs for one user (only the ones that changed since their last scan)."""
    from careeros.db.connection import db
    from careeros.identity.auth.accounts import normalize_email
    from careeros.identity.repositories.user_repo import UserRepository
    from careeros.jobs.scan import ALL_TIME_HOURS, run_scan, scan_jobs

    with db.session_scope() as s:
        user = UserRepository(s).get_by_email(normalize_email(email))
        user_id = user.id if user else None
    if not user_id:
        typer.echo(f"✗ No account for {email}", err=True)
        raise typer.Exit(1)
    job = scan_jobs.create(user_id, label="cli scan")
    run_scan(job, user_id, ALL_TIME_HOURS, limit)
    for line in job.logs:
        typer.echo(line["message"])
    if job.status != "completed":
        typer.echo(f"✗ {job.error}", err=True)
        raise typer.Exit(1)


def _user_id(email: str) -> str:
    from careeros.db.connection import db
    from careeros.identity.auth.accounts import normalize_email
    from careeros.identity.repositories.user_repo import UserRepository

    with db.session_scope() as s:
        user = UserRepository(s).get_by_email(normalize_email(email))
        if not user:
            typer.echo(f"✗ No account for {email}", err=True)
            raise typer.Exit(1)
        return user.id


@app.command("eval")
def evaluate_ranking(
    email: str = typer.Argument(..., help="Whose ranking to measure"),
    labels: Optional[Path] = typer.Option(None, "--labels", help="Filled label sheet (CSV with url,label)"),
):
    """How well the scores rank jobs this person liked above jobs they didn't (decisions + optional sheet)."""
    from careeros.db.connection import db
    from careeros.jobs.evaluation import evaluate, labels_from_decisions, read_label_sheet

    user_id = _user_id(email)
    with db.session_scope() as s:
        lab = labels_from_decisions(s, user_id)
        if labels:
            lab.update(read_label_sheet(labels))  # the sheet wins where both say something
        r = evaluate(s, user_id, lab)
    typer.echo(f"{r.labelled} labelled ({r.good} good, {r.bad} bad) · {r.scored} have a score")
    typer.echo(f"AUC {r.auc:.3f}" if r.auc is not None else "AUC — needs at least one good and one bad job")
    if r.precision_at_10 is not None:
        typer.echo(f"Good in the top 10: {r.precision_at_10:.0%}")
    for url, score, good in r.top:
        typer.echo(f"  {'✓' if good else '✗'} {score:5.1f}  {url[:90]}")


@app.command("eval-sheet")
def evaluation_sheet(
    email: str = typer.Argument(..., help="Whose jobs to put on the sheet"),
    out: Path = typer.Option(Path("label_sheet.csv"), "--out", help="Where to write the CSV"),
    n: int = typer.Option(50, "--n", help="How many jobs"),
):
    """Write a sheet of jobs to label good/bad (half the current top, half random) for `eval --labels`."""
    from careeros.db.connection import db
    from careeros.jobs.evaluation import export_label_sheet

    user_id = _user_id(email)
    with db.session_scope() as s:
        count = export_label_sheet(s, user_id, out, n)
    typer.echo(f"✓ {count} jobs written to {out}. Fill the 'label' column with good / bad, then run "
               f"`career-os jobs eval {email} --labels {out}`.")


@app.command()
def enrich(limit: int = typer.Option(300, "--limit", help="Max postings to read (0 = all pending)")):
    """Let the LLM read new or changed postings that match someone's roles (cached per posting)."""
    from careeros.jobs.llm_extract import enrich_jobs

    s = enrich_jobs(limit)
    typer.echo(f"✓ {s.extracted} of {s.candidates} postings read · {s.failed} failed")
    if s.stopped:
        typer.echo(f"  stopped: {s.stopped}")


@app.command("import-applypilot")
def import_applypilot(hours: int = typer.Option(0, "--hours", help="Only jobs found in the last N hours (0 = all)")):
    """Copy jobs from a local ApplyPilot database into CareerOS (they are scored like any other job)."""
    from careeros.jobs.ingest import import_rows
    from careeros.jobs.sources.loader import load_job_source_plugin

    try:
        rows = load_job_source_plugin("applypilot").scan_and_normalize(hours_old=hours, min_score=0)
    except Exception as e:
        typer.echo(f"✗ ApplyPilot: {e}", err=True)
        raise typer.Exit(1)
    typer.echo(f"✓ Imported {import_rows(rows)} jobs from ApplyPilot")
