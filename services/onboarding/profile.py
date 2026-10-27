"""User record, identity step, goals step and the onboarding state machine."""

import re
import uuid
from datetime import date
from typing import Any, Optional

import sqlalchemy as sa
from sqlalchemy.orm import Session

from core.db.models.custom_role import CustomRole
from core.db.models.user import User
from core.db.repositories.career_preferences_repo import CareerPreferencesRepository
from core.db.repositories.user_repo import UserRepository
from core.domain.identity.onboarding import OnboardingState

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)


class OnboardingInputError(ValueError):
    """The submitted onboarding data is inconsistent (maps to HTTP 400)."""


# ── user record ───────────────────────────────────────────────────────────

def ensure_user(session: Session, clerk_id: str) -> User:
    """The user's row, created with placeholders if the Clerk webhook has not run yet."""
    repo = UserRepository(session)
    user = repo.get_by_clerk_id(clerk_id)
    if not user:
        user = repo.upsert_from_clerk(
            clerk_id=clerk_id,
            email=f"{clerk_id}@placeholder-applypilot.com",
            first_name="New",
            last_name="User",
        )
        session.commit()
    return user


def _preferences_view(prefs) -> Optional[dict]:
    if not prefs:
        return None
    has_salary = prefs.salary_min is not None or prefs.salary_max is not None
    return {
        "goal_ids": prefs.goal_ids or [],
        "preferred_role_ids": prefs.preferred_role_ids or [],
        "preferred_country_codes": prefs.preferred_country_codes or [],
        "work_arrangements": prefs.work_arrangements or [],
        "requires_sponsorship": prefs.requires_sponsorship,
        "contract_types": prefs.contract_types or [],
        "availability": prefs.availability,
        "target_seniority": prefs.target_seniority,
        "salary": {
            "min": prefs.salary_min,
            "max": prefs.salary_max,
            "currency": prefs.salary_currency,
            "period": prefs.salary_period,
            "negotiable": prefs.salary_negotiable,
        } if has_salary else None,
    }


def get_state(session: Session, clerk_id: str) -> dict:
    user = ensure_user(session, clerk_id)
    prefs = CareerPreferencesRepository(session).get_by_user_id(clerk_id)
    return {
        "state": user.onboarding_state,
        "profile_data": user.profile_data or {},
        "preferences": _preferences_view(prefs),
        "next_step": OnboardingState.next_state(user.onboarding_state),
    }


# ── identity step ─────────────────────────────────────────────────────────

def classify_role_id(role_id: str) -> str:
    """'uuid' (canonical role id) | 'custom' (custom_ prefix) | 'slug' (static catalog key)."""
    if _UUID_RE.match(role_id):
        return "uuid"
    if role_id.startswith("custom_"):
        return "custom"
    return "slug"


def _resolve_role(session: Session, clerk_id: str, role_id: str, role_title: str) -> tuple[Optional[str], Optional[str]]:
    """(canonical role id, custom role id) — exactly one is set."""
    kind = classify_role_id(role_id)
    if kind == "uuid":
        return role_id, None
    if kind == "slug":
        row = session.execute(sa.text("SELECT id FROM roles WHERE slug = :slug LIMIT 1"), {"slug": role_id}).fetchone()
        if row:
            return str(row[0]), None
        # unknown slug → treat as a custom role

    # Custom role: idempotent per (user, title)
    existing = session.execute(
        sa.text("SELECT id FROM custom_roles WHERE user_id = :uid AND title = :title LIMIT 1"),
        {"uid": clerk_id, "title": role_title},
    ).fetchone()
    if existing:
        return None, str(existing[0])
    custom = CustomRole(id=uuid.uuid4(), user_id=clerk_id, title=role_title)
    session.add(custom)
    session.flush()
    return None, str(custom.id)


def save_identity(session: Session, clerk_id: str, identity: dict[str, Any]) -> str:
    """Persist the identity step, record the role in history, advance the state. Returns new state."""
    user = ensure_user(session, clerk_id)
    role_id, custom_role_id = _resolve_role(
        session, clerk_id, identity["current_role_id"], identity["current_role_title"]
    )

    user.current_role_id = role_id
    user.current_custom_role_id = custom_role_id
    user.years_in_role = identity["years_in_role"]
    user.career_level = identity.get("career_level")
    user.career_level_origin = identity.get("career_level_origin", "system")
    user.profile_data = {
        "first_name": identity["first_name"],
        "last_name": identity.get("last_name"),
        "country": identity["country"],
        "current_role_title": identity["current_role_title"],
        "total_years": identity.get("total_years"),
        "languages": identity.get("languages") or [],
        "education_level": identity.get("education_level"),
    }

    # Role history: close the previous current role, open the new one
    today = date.today()
    session.execute(
        sa.text("UPDATE user_roles SET is_current = false, ended_at = :today "
                "WHERE user_id = :user_id AND is_current = true"),
        {"user_id": clerk_id, "today": today},
    )
    session.execute(
        sa.text("INSERT INTO user_roles (id, user_id, role_id, custom_role_id, started_at, is_current, source) "
                "VALUES (:id, :user_id, :role_id, :custom_role_id, :started_at, true, :source)"),
        {
            "id": str(uuid.uuid4()),
            "user_id": clerk_id,
            "role_id": role_id,
            "custom_role_id": custom_role_id,
            "started_at": today,
            "source": "canonical" if role_id else "custom",
        },
    )

    if user.onboarding_state in (OnboardingState.NOT_STARTED.value, OnboardingState.IDENTITY.value):
        user.onboarding_state = OnboardingState.GOALS.value
    session.commit()
    return user.onboarding_state


# ── goals step ────────────────────────────────────────────────────────────

def validate_goals(goals: dict[str, Any]) -> None:
    lo, hi = goals.get("salary_min"), goals.get("salary_max")
    if lo is not None and hi is not None and lo > hi:
        raise OnboardingInputError("salary_min cannot be greater than salary_max")


def save_goals(session: Session, clerk_id: str, goals: dict[str, Any]) -> str:
    """Persist career preferences and advance GOALS → EVIDENCE. Returns new state."""
    validate_goals(goals)
    CareerPreferencesRepository(session).upsert(user_id=clerk_id, **goals)

    user = ensure_user(session, clerk_id)
    if user.onboarding_state == OnboardingState.GOALS.value:
        user.onboarding_state = OnboardingState.EVIDENCE.value
    session.commit()
    return user.onboarding_state


# ── state machine ─────────────────────────────────────────────────────────

def advance(session: Session, clerk_id: str) -> str:
    user = ensure_user(session, clerk_id)
    nxt = OnboardingState.next_state(user.onboarding_state)
    if nxt:
        user.onboarding_state = nxt
    return user.onboarding_state


def complete(session: Session, clerk_id: str) -> str:
    user = ensure_user(session, clerk_id)
    user.onboarding_state = OnboardingState.READY.value
    return user.onboarding_state


def get_career_graph(session: Session, clerk_id: str) -> dict:
    user = ensure_user(session, clerk_id)
    return (user.profile_data or {}).get("career_graph") or {"nodes": [], "edges": [], "stats": {}}
