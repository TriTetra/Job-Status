"""`career-os jobs …` — company boards, sync, scoring."""

from datetime import datetime, timezone
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
