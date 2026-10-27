"""Evidence source registry, tailored to the user's role.

The registry itself lives in the `evidence_sources` table (no hardcoded list);
this module decides which sources to *recommend* and which are connected.
"""

from typing import Optional

from sqlalchemy.orm import Session

from careeros.identity.models.connected_account import ConnectedAccount
from careeros.evidence.models.evidence_source import EvidenceSource
from careeros.identity.current_role import CurrentRole, get_current_role
from careeros.knowledge.seeds import load_seed

# Profession category → recommended sources, for roles without a seeded list.
# Same data the seed writes into roles.metadata — one copy, in infra/seeds/v1/evidence_sources.yaml.
_SEED = load_seed("evidence_sources")
CATEGORY_SOURCES: dict[str, list[str]] = _SEED["category_sources"]
DEFAULT_SOURCES: list[str] = _SEED["default_sources"]


def suggested_source_ids(role: Optional[CurrentRole]) -> list[str]:
    """Canonical roles use their seeded list; custom roles use their inferred category; else defaults."""
    if role is not None:
        if not role.is_custom and role.suggested_source_ids:
            return role.suggested_source_ids
        if role.is_custom and role.category in CATEGORY_SOURCES:
            return CATEGORY_SOURCES[role.category]
    return DEFAULT_SOURCES


def present_sources(sources: list, suggested: list[str], connected: set[str]) -> dict:
    """Registry rows → {"all": [...], "recommended": [...] in suggestion order}."""
    all_sources = [
        {
            "id": src.id,
            "label": src.label,
            "icon": src.icon,
            "category": src.category,
            "status": src.status,                 # available | coming_soon
            "connect_kind": src.connect_kind,     # oauth | url | none
            "oauth_provider": src.oauth_provider,
            "connected": (src.oauth_provider or src.id) in connected,
            "suggested": src.id in suggested,
        }
        for src in sources
    ]
    recommended = sorted((s for s in all_sources if s["suggested"]), key=lambda s: suggested.index(s["id"]))
    return {"all": all_sources, "recommended": recommended}


def list_sources(session: Session, user_id: str) -> dict:
    """{recommended, all, connected, role_title} for the connections step."""
    role = get_current_role(session, user_id)
    suggested = suggested_source_ids(role)

    sources = session.query(EvidenceSource).order_by(EvidenceSource.sort_order).all()
    connected = {
        provider for (provider,) in session.query(ConnectedAccount.provider).filter(
            ConnectedAccount.user_id == user_id,
            ConnectedAccount.is_active.is_(True),
        ).all()
    }
    view = present_sources(sources, suggested, connected)
    return {
        "recommended": view["recommended"],
        "all": view["all"],
        "connected": {p: True for p in connected},
        "role_title": role.title if role else None,
    }
