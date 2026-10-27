"""Evidence source registry, tailored to the user's role.

The registry itself lives in the `evidence_sources` table (no hardcoded list);
this module decides which sources to *recommend* and which are connected.
"""

from typing import Optional

from sqlalchemy.orm import Session

from careeros.identity.models.connected_account import ConnectedAccount
from careeros.evidence.models.evidence_source import EvidenceSource
from careeros.identity.current_role import CurrentRole, get_current_role

# Profession category → recommended sources, for roles without a seeded list
CATEGORY_SOURCES: dict[str, list[str]] = {
    "Engineering":   ["github", "portfolio", "stackoverflow"],
    "AI/ML":         ["github", "kaggle", "portfolio"],
    "Data":          ["kaggle", "github", "portfolio"],
    "Design":        ["dribbble", "behance", "portfolio"],
    "Product":       ["linkedin", "portfolio"],
    "Management":    ["linkedin", "portfolio"],
    "DevOps":        ["github", "portfolio"],
    "Security":      ["github", "portfolio"],
    "Research":      ["scholar", "researchgate", "github"],
    "QA":            ["github", "portfolio"],
    "medical":       ["pubmed", "orcid", "scholar", "doximity"],
    "academic":      ["scholar", "researchgate", "orcid", "portfolio"],
    "architecture":  ["archinect", "houzz", "behance", "portfolio"],
    "visual_art":    ["artstation", "behance", "dribbble", "portfolio"],
    "writing":       ["medium", "substack", "portfolio"],
    "education":     ["linkedin", "scholar", "portfolio"],
    "legal":         ["linkedin", "portfolio"],
}
DEFAULT_SOURCES = ["portfolio", "linkedin"]


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
