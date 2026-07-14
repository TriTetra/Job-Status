"""CLI for Market Intelligence."""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from dotenv import load_dotenv
    for _env in [Path(".env"), Path("services/hiring-agent/.env")]:
        if _env.exists():
            load_dotenv(_env)
            break
except ImportError:
    pass

import typer

from core.db.connection import db
from core.db.repositories import MarketSignalRepository
from plugins.market_signals.hackernews.signal_extractor import HNSignalExtractor
from plugins.market_signals.techcrunch.signal_extractor import TechCrunchSignalExtractor

app = typer.Typer(help="Market Intelligence commands")


@app.command("scan-hn")
def scan_hn(
    year: int = typer.Option(None),
    month: int = typer.Option(None),
):
    """Scan HN Who is Hiring thread."""
    now = datetime.utcnow()
    year = year or now.year
    month = month or now.month
    count = HNSignalExtractor().extract_monthly_signals(year, month)
    typer.echo(f"Created {count} signals from HN {year}-{month:02d}")


@app.command("scan-techcrunch")
def scan_techcrunch(
    hours: int = typer.Option(168, help="Hours back (default: 7 days)"),
):
    """Scan TechCrunch for funding/layoff news."""
    count = TechCrunchSignalExtractor().extract_signals(hours=hours)
    typer.echo(f"Created {count} signals from TechCrunch")


@app.command()
def recent(
    days: int = typer.Option(7),
    limit: int = typer.Option(20),
):
    """Show recent market signals."""
    with db.session_scope() as session:
        repo = MarketSignalRepository(session)
        signals = repo.get_recent(days=days, limit=limit)

    if not signals:
        typer.echo("No signals found.")
        return

    typer.echo(f"\nMarket Signals — last {days} days:\n")
    _IMPACT_ICON = {"critical": "[!!]", "high": "[!]", "medium": "[ ]", "low": "[-]"}
    for s in signals:
        icon = _IMPACT_ICON.get(s.impact, "[ ]")
        typer.echo(f"  {icon} [{s.signal_type:<16}] {s.title[:60]}")


@app.command()
def trend(skill: str = typer.Argument(...), days: int = typer.Option(30)):
    """Show skill demand trend."""
    with db.session_scope() as session:
        repo = MarketSignalRepository(session)
        t = repo.get_skill_trend(skill, days=days)

    arrow = {"up": "^", "down": "v", "stable": "-"}.get(t["direction"], "?")
    typer.echo(f"\n{arrow} {skill} ({days}d): {t['current_count']} mentions "
               f"({t['change_percent']:+.1f}% vs prev period)")


@app.command()
def summary(days: int = typer.Option(7)):
    """Show market summary."""
    with db.session_scope() as session:
        repo = MarketSignalRepository(session)
        s = repo.get_market_summary(days=days)

    typer.echo(f"\nMarket Summary — last {days} days:")
    typer.echo(f"  Signals: {s['signal_counts']}")
    typer.echo(f"  Top companies: {[c['company'] for c in s['top_companies'][:5]]}")
    typer.echo(f"  Top skills: {[x['skill'] for x in s['top_skills'][:5]]}")


if __name__ == "__main__":
    app()
