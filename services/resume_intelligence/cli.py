"""
CLI for resume generation.

Usage:
    python -m services.resume_intelligence.cli generate \\
        --company Google \\
        --title "ML Engineer" \\
        --template ml_research
"""

from pathlib import Path

import typer


from services.resume_intelligence.application.resume_generator import generate_resume

app = typer.Typer(help="Target-aware resume generation")


@app.command()
def generate(
    company: str = typer.Option(..., "--company", "-c", help="Target company"),
    title: str = typer.Option(..., "--title", "-t", help="Target role title"),
    template: str = typer.Option(
        "ml_research", "--template", "-T", help="Template: ml_research, backend"
    ),
    description: str = typer.Option("", "--description", "-d", help="Optional job description"),
    user_id: str = typer.Option("default", "--user", help="User ID"),
):
    """Generate a target-aware resume."""
    try:
        output = generate_resume(
            target_company=company,
            target_title=title,
            template_name=template,
            job_description=description,
            user_id=user_id,
        )
        typer.echo(f"\nSuccess! Resume saved to: {output}")
    except Exception as e:
        typer.echo(f"\nError: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def templates():
    """List available templates."""
    templates_dir = Path(__file__).parent / "templates" / "resume"
    typer.echo("\nAvailable Resume Templates:\n")
    for t in templates_dir.glob("*.md.jinja"):
        name = t.stem.replace(".md", "")
        typer.echo(f"  - {name}")
    typer.echo("")


if __name__ == "__main__":
    app()
