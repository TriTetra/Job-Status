"""
Application Engine CLI.

Commands:
  add              -- add a job to track (status: to_apply)
  update           -- advance a job's status + optional notes
  list             -- list jobs filtered by status
  summary          -- pipeline count table
  stale            -- jobs with no update in N days
  migrate-from-markdown  -- import rows from docs/tracking/JOB_APPLICATIONS.md
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

_ROOT = Path(__file__).parents[2]

from core.db.connection import db
from core.db.repositories import ApplicationRepository

app = typer.Typer(help="Track job applications through the hiring pipeline.")
console = Console()

VALID_STATUSES = {
    "to_apply",
    "applied",
    "phone_screen",
    "technical",
    "onsite",
    "offer",
    "rejected",
    "ghosted",
    "withdrawn",
}

STATUS_LABEL = {
    "to_apply":    "to_apply",
    "applied":     "applied",
    "phone_screen": "phone_screen",
    "technical":   "technical",
    "onsite":      "onsite",
    "offer":       "OFFER",
    "rejected":    "rejected",
    "ghosted":     "ghosted",
    "withdrawn":   "withdrawn",
}


def _validate_status(status: str) -> str:
    if status not in VALID_STATUSES:
        console.print(f"[red]Invalid status '{status}'.[/red]")
        console.print(f"Valid: {', '.join(sorted(VALID_STATUSES))}")
        raise typer.Exit(1)
    return status


@app.command()
def add(
    url: str = typer.Argument(..., help="Job posting URL (used as primary key)"),
    title: str = typer.Option(..., "--title", "-t", help="Job title"),
    company: Optional[str] = typer.Option(None, "--company", "-c", help="Company name"),
    status: str = typer.Option("to_apply", "--status", "-s", help="Initial status"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="Free-form notes"),
):
    """Add a job to the pipeline."""
    _validate_status(status)
    msg = None
    warn = None
    with db.session_scope() as session:
        repo = ApplicationRepository(session)
        existing = repo.get(url=url)
        if existing:
            warn = f"Already tracked: {existing.title} @ {existing.company} ({existing.status})"
        else:
            obj = repo.create(url=url, title=title, company=company, status=status, notes=notes)
            session.flush()
            msg = f"Added: {obj.title} @ {obj.company or '?'} -> {STATUS_LABEL.get(status, status)}"

    if warn:
        console.print(f"[yellow]{warn}[/yellow]")
    if msg:
        console.print(f"[green]{msg}[/green]")


@app.command()
def update(
    url: str = typer.Argument(..., help="Job posting URL"),
    status: str = typer.Option(..., "--status", "-s", help="New status"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="Notes to append"),
    salary: Optional[int] = typer.Option(None, "--salary", help="Salary offered (numbers only)"),
):
    """Update status (and optionally notes/salary) for a tracked job."""
    _validate_status(status)
    msg = None
    err = None
    with db.session_scope() as session:
        repo = ApplicationRepository(session)
        obj = repo.get(url=url)
        if not obj:
            err = f"Not found: {url}"
        else:
            kwargs: dict = {"status": status}
            if status == "applied" and not obj.applied_at:
                kwargs["applied_at"] = datetime.now(timezone.utc)
            if notes:
                existing_notes = obj.notes or ""
                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                kwargs["notes"] = f"{existing_notes}\n[{timestamp}] {notes}".strip()
            if salary is not None:
                kwargs["salary_offered"] = salary
            repo.update(obj, **kwargs)
            msg = f"Updated: {obj.title} -> {STATUS_LABEL.get(status, status)}"

    if err:
        console.print(f"[red]{err}[/red]")
        raise typer.Exit(1)
    if msg:
        console.print(f"[green]{msg}[/green]")


@app.command("list")
def list_jobs(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    limit: int = typer.Option(50, "--limit", "-l", help="Max rows to show"),
):
    """List tracked jobs, optionally filtered by status."""
    if status:
        _validate_status(status)

    with db.session_scope() as session:
        repo = ApplicationRepository(session)
        if status:
            jobs = repo.get_by_status(status)[:limit]
        else:
            jobs = repo.get_all()[:limit]

        rows = [
            (
                STATUS_LABEL.get(j.status, j.status),
                j.company or "-",
                j.title,
                j.applied_at.strftime("%Y-%m-%d") if j.applied_at else "-",
                (j.notes or "")[:40].replace("\n", " "),
            )
            for j in jobs
        ]
        total = len(rows)

    if not rows:
        console.print("[dim]No applications found.[/dim]")
        return

    table = Table(title=f"Applications ({total})", show_lines=False)
    table.add_column("Status", width=14)
    table.add_column("Company", width=20)
    table.add_column("Title", width=40)
    table.add_column("Applied", width=12)
    table.add_column("Notes", width=30, overflow="fold")

    for row in rows:
        table.add_row(*row)

    console.print(table)


@app.command()
def summary():
    """Show pipeline counts by status."""
    with db.session_scope() as session:
        repo = ApplicationRepository(session)
        counts = repo.get_pipeline_summary()

    total = sum(counts.values())
    table = Table(title=f"Pipeline Summary (total: {total})")
    table.add_column("Status", width=16)
    table.add_column("Count", justify="right", width=8)
    table.add_column("Bar", width=30)

    ordered = [
        "to_apply", "applied", "phone_screen", "technical",
        "onsite", "offer", "rejected", "ghosted", "withdrawn",
    ]
    for s in ordered:
        n = counts.get(s, 0)
        if n == 0:
            continue
        bar = "#" * min(n * 2, 30)
        table.add_row(STATUS_LABEL.get(s, s), str(n), bar)

    console.print(table)


@app.command()
def stale(
    days: int = typer.Option(14, "--days", "-d", help="Flag jobs not updated in this many days"),
    statuses: str = typer.Option(
        "applied,phone_screen,technical,onsite",
        "--statuses",
        help="Comma-separated statuses to check",
    ),
):
    """List active jobs with no status change in N days (likely ghosted)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    check_statuses = [s.strip() for s in statuses.split(",")]

    with db.session_scope() as session:
        repo = ApplicationRepository(session)
        stale_jobs = repo.get_stale(check_statuses, cutoff)
        rows = [
            (
                STATUS_LABEL.get(j.status, j.status),
                j.company or "-",
                j.title,
                j.updated_at.strftime("%Y-%m-%d") if j.updated_at else "-",
            )
            for j in stale_jobs
        ]

    if not rows:
        console.print(f"[green]No stale applications (>{days} days) found.[/green]")
        return

    table = Table(title=f"Stale Applications (>{days} days, {len(rows)} found)")
    table.add_column("Status", width=14)
    table.add_column("Company", width=20)
    table.add_column("Title", width=40)
    table.add_column("Last Updated", width=14)

    for row in rows:
        table.add_row(*row)

    console.print(table)
    console.print("\nTip: run [bold]update --status ghosted[/bold] for these.")


@app.command("migrate-from-markdown")
def migrate_from_markdown(
    path: Path = typer.Option(
        Path("docs/tracking/JOB_APPLICATIONS.md"),
        "--path",
        "-p",
        help="Path to JOB_APPLICATIONS.md",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing to DB"),
):
    """
    Import jobs from the markdown tracker into the applications table.

    Parses table rows with a URL in the Link column. Skips placeholder
    rows (e.g. '[Apply](link)') and rows with no real URL.
    """
    import re

    md_path = _ROOT / path if not path.is_absolute() else path
    if not md_path.exists():
        console.print(f"[red]File not found:[/red] {md_path}")
        raise typer.Exit(1)

    text = md_path.read_text(encoding="utf-8")

    _MD_STATUS_MAP = {
        "to apply": "to_apply",
        "applied": "applied",
        "response received": "phone_screen",
        "interview scheduled": "phone_screen",
        "offers": "offer",
        "rejected": "rejected",
    }

    current_status = "to_apply"
    skipped = 0
    rows_to_import: list[dict] = []

    for line in text.splitlines():
        heading = re.match(r"^###\s+(.+)", line)
        if heading:
            h = heading.group(1).strip().lower()
            current_status = _MD_STATUS_MAP.get(h, "to_apply")
            continue

        url_match = re.search(r"\[.*?\]\((.+?)\)", line)
        if not url_match:
            continue
        url = url_match.group(1).strip()
        if url in ("link", "#", "") or url.startswith("link"):
            skipped += 1
            continue

        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        title = cols[1] if len(cols) > 1 else "Unknown"
        company = cols[2] if len(cols) > 2 else None
        if not title or title in ("-", "Job Title"):
            skipped += 1
            continue

        rows_to_import.append(
            {"url": url, "title": title, "company": company, "status": current_status}
        )

    if not rows_to_import:
        console.print(f"[dim]No importable rows found (skipped {skipped} placeholders).[/dim]")
        return

    console.print(f"Found [bold]{len(rows_to_import)}[/bold] rows to import ({skipped} skipped).")
    for r in rows_to_import:
        console.print(f"  {r['status']:15} {r['company'] or '?':20} {r['title']}")

    if dry_run:
        console.print("\n[yellow]Dry run -- nothing written.[/yellow]")
        return

    imported = 0
    already = 0
    with db.session_scope() as session:
        repo = ApplicationRepository(session)
        for r in rows_to_import:
            existing = repo.get(url=r["url"])
            if existing:
                already += 1
            else:
                repo.create(**r)
                imported += 1

    console.print(f"\n[green]Imported {imported} rows.[/green] ({already} already existed)")


if __name__ == "__main__":
    from shared.logging import configure_logging

    configure_logging()
    app()
