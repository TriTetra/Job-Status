"""`career-os user …` — the only way accounts are created (there is no sign-up page)."""

from typing import Optional

import typer

from careeros.db.connection import db
from careeros.identity.auth import accounts, sessions
from careeros.identity.auth.passwords import MIN_LENGTH, WeakPassword
from careeros.identity.repositories.user_repo import UserRepository

app = typer.Typer(help="Manage who can sign in", no_args_is_help=True)


def _ask_password() -> str:
    return typer.prompt(f"Password (min {MIN_LENGTH} chars)", hide_input=True, confirmation_prompt=True)


def _fail(message: str) -> None:
    typer.secho(f"✗ {message}", fg=typer.colors.RED, err=True)
    raise typer.Exit(1)


@app.command()
def add(
    email: str = typer.Argument(..., help="Sign-in email"),
    first_name: Optional[str] = typer.Option(None, "--first-name"),
    last_name: Optional[str] = typer.Option(None, "--last-name"),
):
    """Create an account (asks for the password)."""
    password = _ask_password()
    try:
        with db.session_scope() as s:
            user = accounts.create_account(s, email, password, first_name, last_name)
            user_id = user.id
    except (accounts.AccountError, WeakPassword) as e:
        _fail(str(e))
    typer.secho(f"✓ {email} can sign in (id {user_id})", fg=typer.colors.GREEN)


@app.command()
def passwd(email: str = typer.Argument(..., help="Account email")):
    """Set or reset a password — also how accounts created under Clerk get one. Signs out everywhere."""
    password = _ask_password()
    try:
        with db.session_scope() as s:
            accounts.set_password(s, email, password)
    except (accounts.AccountError, WeakPassword) as e:
        _fail(str(e))
    typer.secho(f"✓ Password set for {email}; existing sessions signed out", fg=typer.colors.GREEN)


@app.command("list")
def list_users():
    """Everyone with a users row, and whether they can sign in."""
    with db.session_scope() as s:
        rows = accounts.list_accounts(s)
    if not rows:
        typer.echo("No users yet — create one with: career-os user add you@example.com")
        return
    for a in rows:
        status = "active" if a.is_active else "disabled"
        login = "password set" if a.has_password else "NO PASSWORD (run: career-os user passwd)"
        typer.echo(f"  {a.email:<36} {a.name:<24} {status:<9} {login:<40} {a.onboarding_state}")


@app.command()
def disable(email: str = typer.Argument(...)):
    """Block sign-in and end all sessions (data is kept)."""
    try:
        with db.session_scope() as s:
            accounts.set_active(s, email, False)
    except accounts.AccountError as e:
        _fail(str(e))
    typer.secho(f"✓ {email} disabled", fg=typer.colors.GREEN)


@app.command()
def enable(email: str = typer.Argument(...)):
    """Allow sign-in again."""
    try:
        with db.session_scope() as s:
            accounts.set_active(s, email, True)
    except accounts.AccountError as e:
        _fail(str(e))
    typer.secho(f"✓ {email} enabled", fg=typer.colors.GREEN)


@app.command()
def signout(email: str = typer.Argument(...)):
    """End every session of one user (e.g. a lost laptop)."""
    with db.session_scope() as s:
        user = UserRepository(s).get_by_email(accounts.normalize_email(email))
        if user is None:
            _fail(f"No user with email {email}")
        n = sessions.revoke_all(s, user.id)
    typer.secho(f"✓ {n} session(s) ended for {email}", fg=typer.colors.GREEN)
