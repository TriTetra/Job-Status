"""
CareerOS Unified CLI — single entry point.

Usage:
    career-os --help            (after `pip install -e .`)
    python -m apps.cli.main --help
    python -m apps.cli.main status
    python -m apps.cli.main scan --hours 720
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


# ---------------------------------------------------------------------------
# scan
# ---------------------------------------------------------------------------

@app.command()
def scan(
    hours: int = typer.Option(72, "--hours", "-h", help="Hours to look back"),
    min_score: int = typer.Option(7, "--min-score", help="Minimum ApplyPilot fit score"),
):
    """Scan jobs from ApplyPilot and store results."""
    try:
        from careeros.jobs.sources.loader import load_job_source_plugin
        plugin = load_job_source_plugin("applypilot")
        jobs = plugin.scan_and_normalize(hours_old=hours, min_score=min_score)
        typer.echo(f"Found {len(jobs)} jobs (last {hours}h, min_score={min_score})")
    except NotImplementedError as e:
        typer.echo(f"[scan] ApplyPilot plugin not yet implemented: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"[scan] Error: {e}", err=True)
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# strategy
# ---------------------------------------------------------------------------

@app.command()
def strategy(
    user_id: str = typer.Option("default", "--user", "-u", help="User ID"),
    hours: int = typer.Option(720, "--hours", help="Hours to look back for jobs"),
    limit: int = typer.Option(50, "--limit", help="Max jobs to score"),
    semantic: bool = typer.Option(False, "--semantic", help="Use semantic matcher (slow, downloads model)"),
):
    """Run full career strategy: scan → score → save → print summary."""
    from careeros.identity.profile_service import ProfileService
    from careeros.jobs.scoring_service import ScoringService

    typer.echo(f"Loading profile for user: {user_id}")
    profile_svc = ProfileService(user_id=user_id)
    profile = profile_svc.get_profile()
    if profile is None:
        typer.echo(
            "  No profile found in DB. Run `career-os track add` or seed user_settings first.",
            err=True,
        )
        raise typer.Exit(code=1)
    typer.echo(f"  Profile: {profile.name or '(unnamed)'}, {profile.years_experience}y experience, {len(profile.skills)} skills")

    typer.echo(f"\nLoading jobs (last {hours}h)...")
    try:
        from careeros.jobs.sources.loader import load_job_source_plugin
        plugin = load_job_source_plugin("applypilot")
        raw_jobs = plugin.scan_and_normalize(hours_old=hours, min_score=7)
    except Exception as e:
        typer.echo(f"  [strategy] Job source error: {e}", err=True)
        raise typer.Exit(code=1)

    from careeros.jobs.domain.job import Job
    jobs = [
        Job(
            id=j["url"],
            title=j.get("title", ""),
            company=j.get("company", ""),
            description=j.get("description", ""),
            url=j["url"],
            location=j.get("location", ""),
            remote=j.get("remote", False),
            required_skills=j.get("required_skills", []),
            required_years=float(j.get("required_years", 2.0)),
        )
        for j in raw_jobs[:limit]
    ]
    typer.echo(f"  Loaded {len(jobs)} jobs")

    typer.echo(f"\nScoring ({'semantic' if semantic else 'fast'})...")
    scoring_svc = ScoringService(user_id=user_id)
    result = scoring_svc.run_pipeline(jobs, profile, semantic=semantic)

    typer.echo("\nResults:")
    typer.echo(f"  Scored:      {result['scored']}")
    typer.echo(f"  Saved to DB: {result['saved_to_db']}")
    typer.echo(f"  APPLY:       {result['apply']}")
    typer.echo(f"  CONSIDER:    {result['consider']}")
    typer.echo(f"  SKIP:        {result['skip']}")


if __name__ == "__main__":
    app()
