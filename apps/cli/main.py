"""
CareerOS Unified CLI — single entry point.

Usage:
    python -m apps.cli.main --help
    python -m apps.cli.main status
    python -m apps.cli.main scan --hours 720
    python -m apps.cli.main track list
    python -m apps.cli.main resume generate -c Google -t "ML Engineer"
    python -m apps.cli.main company list
    python -m apps.cli.main market signals
"""

import typer

app = typer.Typer(
    name="career-os",
    help="AI-native career operating system",
    no_args_is_help=True,
)


# ---------------------------------------------------------------------------
# Mount existing service CLIs as sub-command groups
# ---------------------------------------------------------------------------

def _mount_existing_clis() -> None:
    try:
        from services.application_engine.cli import app as track_app
        app.add_typer(track_app, name="track", help="Application tracking pipeline")
    except Exception:
        pass

    try:
        from services.resume_intelligence.cli import app as resume_app
        app.add_typer(resume_app, name="resume", help="Target-aware resume generation")
    except Exception:
        pass

    try:
        from services.company_intelligence.cli import app as company_app
        app.add_typer(company_app, name="company", help="Company intelligence and memory")
    except Exception:
        pass

    try:
        from services.market_intelligence.cli import app as market_app
        app.add_typer(market_app, name="market", help="Market signals and skill trends")
    except Exception:
        pass


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
    from core.db.connection import db
    from core.db.models import Company, MarketSignal
    from core.db.models.career_score import CareerScore
    from core.db.models.application import Application
    from core.db.models.evidence import Evidence
    from sqlalchemy import func, select

    with db.session_scope() as session:
        def count(model):
            return session.execute(select(func.count()).select_from(model)).scalar() or 0

        rows = {
            "Career Scores":  count(CareerScore),
            "Applications":   count(Application),
            "Evidence":       count(Evidence),
            "Companies":      count(Company),
            "Market Signals": count(MarketSignal),
        }

    typer.echo("\nCareerOS Status:\n")
    for label, n in rows.items():
        typer.echo(f"  {label:<18} {n}")
    typer.echo("\n  DB: healthy")


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
        from plugins.plugin_loader import load_job_source_plugin
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
    from services.identity_service.application.profile_service import ProfileService
    from services.job_intelligence.application.scoring_service import ScoringService

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
        from plugins.plugin_loader import load_job_source_plugin
        plugin = load_job_source_plugin("applypilot")
        raw_jobs = plugin.scan_and_normalize(hours_old=hours, min_score=7)
    except Exception as e:
        typer.echo(f"  [strategy] Job source error: {e}", err=True)
        raise typer.Exit(code=1)

    from core.domain import Job
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
