"""What each user is looking for, as title terms (from preferred and current roles)."""

from typing import Iterable, Optional

from sqlalchemy import cast, or_, String
from sqlalchemy.orm import Session

from careeros.identity.models.career_preferences import CareerPreferences
from careeros.identity.models.custom_role import CustomRole
from careeros.identity.models.role import Role
from careeros.identity.models.user_role import UserRole
from careeros.jobs.boards import TitleFilter, load_boards


def role_terms(session: Session, user_ids: Optional[Iterable[str]] = None) -> list[str]:
    """Titles and aliases of the roles these users target or hold (all users when None)."""
    prefs = session.query(CareerPreferences.preferred_role_ids)
    current = session.query(UserRole.role_id, UserRole.custom_role_id).filter(UserRole.is_current.is_(True))
    if user_ids is not None:
        ids = list(user_ids)
        prefs = prefs.filter(CareerPreferences.user_id.in_(ids))
        current = current.filter(UserRole.user_id.in_(ids))

    refs: set[str] = set()  # role ids or slugs
    for (role_ids,) in prefs.all():
        refs.update(str(r) for r in role_ids or [])
    custom_ids = []
    for role_id, custom_id in current.all():
        if role_id:
            refs.add(str(role_id))
        if custom_id:
            custom_ids.append(custom_id)

    terms: list[str] = []
    if refs:
        roles = session.query(Role.title, Role.aliases).filter(
            or_(cast(Role.id, String).in_(refs), Role.slug.in_(refs))
        ).all()
        for title, aliases in roles:
            terms.append(title)
            terms.extend(aliases or [])
    if custom_ids:
        terms.extend(t for (t,) in session.query(CustomRole.title).filter(CustomRole.id.in_(custom_ids)).all())
    return list(dict.fromkeys(t.strip() for t in terms if t and t.strip()))


def user_title_filter(session: Session, user_id: str) -> TitleFilter:
    """The user's own roles; the board-wide list when they haven't picked any."""
    config = load_boards().titles
    terms = role_terms(session, [user_id])
    return TitleFilter(tuple(terms), config.exclude) if terms else config
