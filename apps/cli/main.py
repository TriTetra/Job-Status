"""
CareerOS Unified CLI — single entry point.

Usage:
    career-os --help            (after `pip install -e .`)
    python -m apps.cli.main --help
    python -m apps.cli.main status
    python -m apps.cli.main jobs sync
    python -m apps.cli.main track list
    python -m apps.cli.main resume generate -c Google -t "ML Engineer"
    python -m apps.cli.main company list
    python -m apps.cli.main market signals
"""

import sys

import typer

from careeros.shared.logging import configure_logging

# Rich output uses box-drawing chars and arrows; Windows consoles/pipes default
# to cp1252 and crash on them. Force UTF-8 for this process's own streams.
for _stream in (sys.stdout, sys.stderr):
    if (_stream.encoding or "").lower() != "utf-8":
        _stream.reconfigure(encoding="utf-8", errors="replace")

configure_logging()

app = typer.Typer(
    name="career-os",
    help="AI-native career operating system",
    no_args_is_help=True,
)


# ---------------------------------------------------------------------------
# Mount existing service CLIs as sub-command groups
# ---------------------------------------------------------------------------

_SUB_CLIS = [
    # (module, Typer attribute, command name, help)
    ("careeros.identity.cli", "app", "user", "Manage who can sign in"),
    ("careeros.jobs.cli", "app", "jobs", "Company boards, sync and scoring"),
    ("careeros.applications.cli", "app", "track", "Application tracking pipeline"),
    ("careeros.resume.cli", "app", "resume", "Target-aware resume generation"),
    ("careeros.companies.cli", "app", "company", "Company intelligence and memory"),
    ("careeros.market.cli", "app", "market", "Market signals and skill trends"),
]


def _mount_existing_clis() -> None:
    """Mount feature CLIs. A broken one is reported (not silently dropped) and the rest still load."""
    import importlib
    import logging

    for module, attr, name, help_text in _SUB_CLIS:
        try:
            app.add_typer(getattr(importlib.import_module(module), attr), name=name, help=help_text)
        except Exception as e:
            logging.getLogger(__name__).warning("CLI group '%s' unavailable: %s", name, e)


_mount_existing_clis()


# ---------------------------------------------------------------------------
# version / status
# ---------------------------------------------------------------------------

@app.command()
def version():
    """Show CareerOS version."""
    typer.echo("CareerOS v1.0.0")


@app.command()
def status():
    """Show counts for all DB tables."""
    from careeros.db.connection import db
    from careeros.companies.models.company import Company
    from careeros.market.models.market_signal import MarketSignal
    from careeros.jobs.models.career_score import CareerScore
    from careeros.applications.models.application import Application
    from careeros.evidence.models.evidence_item import EvidenceItem
    from sqlalchemy import func, select

    with db.session_scope() as session:
        def count(model):
            return session.execute(select(func.count()).select_from(model)).scalar() or 0

        rows = {
            "Career Scores":  count(CareerScore),
            "Applications":   count(Application),
            "Evidence":       count(EvidenceItem),
            "Companies":      count(Company),
            "Market Signals": count(MarketSignal),
        }

    typer.echo("\nCareerOS Status:\n")
    for label, n in rows.items():
        typer.echo(f"  {label:<18} {n}")
    typer.echo("\n  DB: healthy")


@app.command()
def seed(
    targets: list[str] = typer.Argument(None, help="reference | skills | roles | goals | sources (default: all)"),
):
    """Load reference data from infra/seeds/v1/*.yaml (idempotent)."""
    from careeros.knowledge.seeds import SEEDS, run

    try:
        counts = run(targets or None)
    except ValueError as e:
        raise typer.BadParameter(str(e)) from e
    for name in SEEDS:
        if name in counts:
            typer.echo(f"  {name:<10} {counts[name]}")


@app.command("llm-usage")
def llm_usage(days: int = typer.Option(7, "--days", help="How many days back")):
    """LLM calls, tokens and cost per day and task, against today's budget."""
    from careeros.db.connection import db
    from careeros.shared.llm_usage import budget_status, usage_report

    with db.session_scope() as s:
        status, rows = budget_status(s), usage_report(s, days)
    budget = status["daily_budget_usd"]
    typer.echo(f"Today: ${status['spent_today_usd']:.4f}" + (f" of ${budget:.4f}" if budget else " (no daily budget)")
               + f" · resets {status['resets_at'][:16]} UTC\n")
    typer.echo(f"{'day':<12}{'task':<14}{'calls':>6}{'errors':>7}{'refused':>8}{'tokens':>10}{'cost $':>10}")
    for r in rows:
        typer.echo(f"{r['day']:<12}{r['task']:<14}{r['calls']:>6}{r['errors']:>7}{r['refused']:>8}"
                   f"{r['tokens']:>10}{r['cost_usd']:>10.4f}")
    if not rows:
        typer.echo("(no LLM calls)")


if __name__ == "__main__":
    app()
