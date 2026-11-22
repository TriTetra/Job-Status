"""Canonical role ids → titles (for sentences like "Looking for AI Engineer roles")."""

from uuid import UUID

from sqlalchemy.orm import Session

from careeros.identity.models.role import Role


def role_titles(session: Session, ids: list[str]) -> list[str]:
    """Titles in the given order; ids that aren't canonical role UUIDs (custom roles) are skipped."""
    valid: list[UUID] = []
    for i in ids:
        try:
            valid.append(UUID(str(i)))
        except ValueError:
            continue
    if not valid:
        return []
    titles = {str(r.id): r.title for r in session.query(Role).filter(Role.id.in_(valid)).all()}
    return [titles[str(u)] for u in valid if str(u) in titles]
