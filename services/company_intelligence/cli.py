"""CLI for Company Intelligence."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import typer

from core.db.connection import db
from core.db.repositories import CompanyRepository

from .application.company_enricher import CompanyEnricher
from .application.company_memory import CompanyMemoryService

app = typer.Typer(help="Company Intelligence commands")


@app.command()
def seed():
    """Seed companies from knowledge YAML."""
    count = CompanyEnricher().seed_from_knowledge()
    typer.echo(f"Seeded {count} companies from knowledge YAML.")


@app.command("list")
def list_companies(
    tier: str = typer.Option(None, "--tier", "-t", help="Filter by tier"),
):
    """List companies in the DB."""
    with db.session_scope() as session:
        repo = CompanyRepository(session)
        companies = repo.get_by_tier(tier) if tier else repo.get_all()

    if not companies:
        typer.echo("No companies found. Run: python -m services.company_intelligence.cli seed")
        return

    typer.echo(f"\nCompanies ({len(companies)}):\n")
    for c in companies[:50]:
        tech = ", ".join((c.tech_stack or [])[:4])
        typer.echo(f"  [{c.tier:<10}] {c.name:<20} {tech}")


@app.command()
def show(company_name: str):
    """Show full company profile."""
    with db.session_scope() as session:
        repo = CompanyRepository(session)
        company = repo.get(name=company_name)

    if not company:
        typer.echo(f"Company '{company_name}' not found.")
        raise typer.Exit(code=1)

    typer.echo(f"\n{company.name} [{company.tier}]")
    typer.echo(f"  Industry:   {company.industry}")
    typer.echo(f"  HQ:         {company.headquarters}")
    typer.echo(f"  Employees:  {company.employee_count}")
    typer.echo(f"  Visa:       {company.sponsors_visa}")
    typer.echo(f"  Remote:     {company.remote_friendly}")
    typer.echo(f"\n  Tech Stack: {', '.join(company.tech_stack or [])}")
    typer.echo(f"\n  Interview Rounds:")
    for r in (company.interview_rounds or []):
        typer.echo(f"    Round {r.get('round')}: {r.get('type')} ({r.get('duration_min')} min)")
    typer.echo(f"\n  Culture: {', '.join(company.culture_signals or [])}")
    if company.red_flags:
        typer.echo(f"\n  Red Flags: {company.red_flags}")


@app.command()
def memory(
    company_name: str,
    user_id: str = typer.Option("default", "--user"),
):
    """Show per-user memory about a company."""
    service = CompanyMemoryService(user_id=user_id)
    advice = service.get_advice_for_company(company_name)

    typer.echo(f"\nMemory: {company_name} (user={user_id})")
    typer.echo(f"\n  Summary: {advice['summary']}")

    for outcome in advice["previous_outcomes"]:
        typer.echo(
            f"  - {outcome.get('stage')}: {outcome.get('outcome')} "
            f"({outcome.get('job_title', '')})"
        )

    topics = service.get_topics_to_study(company_name)
    if topics:
        typer.echo(f"\n  Topics to study: {', '.join(topics)}")

    typer.echo(f"\n  Recommendation: {advice['recommendation']}")


if __name__ == "__main__":
    app()
