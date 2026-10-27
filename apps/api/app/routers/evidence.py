"""Evidence router — evidence items, aggregated skills, portfolio and source registry."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..dependencies import get_db_session, get_user_id

router = APIRouter()

# ─── Custom-role → category inference (title keywords) ────────────────────────
# When a user types a role that isn't in the canonical catalog we infer a
# profession category from the title so connection suggestions stay relevant.
_INFER_KEYWORDS: list[tuple[list[str], str]] = [
    (["doctor", "physician", "surgeon", "nurse", "medic", "clinical", "cardio",
      "oncolo", "radiolo", "dermato", "pediatr", "psychiat", "dentist", "dental",
      "pharmacist", "veterinar", "therapist", "clinician"], "medical"),
    (["professor", "researcher", "scientist", "postdoc", "phd", "academic",
      "lecturer", "scholar", "fellow"], "academic"),
    (["architect", "urban", "landscape architect", "interior designer", "planner"], "architecture"),
    (["artist", "illustrator", "photographer", "animator", "painter", "sculptor",
      "graphic designer", "art director", "creative director"], "visual_art"),
    (["writer", "author", "journalist", "editor", "copywriter", "content",
      "poet", "screenwriter", "blogger"], "writing"),
    (["teacher", "educator", "instructor", "tutor", "coach", "trainer",
      "principal"], "education"),
    (["lawyer", "attorney", "legal", "counsel", "paralegal", "solicitor",
      "barrister", "jurist"], "legal"),
]

# Inlined from seed_evidence_sources to avoid PYTHONPATH issues at runtime
_CATEGORY_SOURCES: dict[str, list[str]] = {
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
_DEFAULT_SOURCES = ["portfolio", "linkedin"]


def _infer_category(title: str | None) -> str | None:
    """Map a free-text role title to an evidence-source category."""
    if not title:
        return None
    t = title.lower()
    for keywords, category in _INFER_KEYWORDS:
        if any(k in t for k in keywords):
            return category
    return None


@router.get("/items")
def get_evidence_items(
    source: Optional[str] = None,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Get user's evidence items with optional source filter, grouped for review UI."""
    from core.db.models.evidence_item import EvidenceItem

    query = session.query(EvidenceItem).filter(
        EvidenceItem.user_id == user_id
    )

    if source:
        query = query.filter(EvidenceItem.source == source)

    items = query.order_by(EvidenceItem.confidence_score.desc()).all()

    # Group by evidence_data type hints or default to skills
    result = {
        "skills": [],
        "projects": [],
        "experiences": [],
        "education": [],
        "certifications": []
    }

    for item in items:
        ed = item.evidence_data or {}
        item_dict = {
            "id": str(item.id),
            "name": item.skill_name,
            "skill_id": item.skill_id,
            "confidence": item.confidence_score,
            "source": item.source,
            "source_url": item.source_url,
            "evidence_text": item.evidence_text,
            "evidence_data": ed,
            "created_at": item.created_at.isoformat() if item.created_at else None
        }

        # Route to correct bucket based on evidence_data.type or default to skills
        item_type = ed.get("type", "skill")
        if item_type == "project":
            result["projects"].append(item_dict)
        elif item_type == "experience":
            result["experiences"].append(item_dict)
        elif item_type == "education":
            result["education"].append(item_dict)
        elif item_type == "certification":
            result["certifications"].append(item_dict)
        else:
            result["skills"].append(item_dict)

    return result


@router.delete("/items/{item_id}")
def delete_evidence_item(
    item_id: int,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Delete evidence item (user removes false positive)."""
    from core.db.models.evidence_item import EvidenceItem
    import logging
    logger = logging.getLogger(__name__)

    evidence_item = session.query(EvidenceItem).filter(
        EvidenceItem.id == item_id,
        EvidenceItem.user_id == user_id
    ).first()

    if not evidence_item:
        raise HTTPException(status_code=404, detail="Evidence item not found")

    session.delete(evidence_item)
    session.commit()

    logger.info(f"User {user_id} deleted evidence item {item_id}")

    return {"status": "deleted", "item_id": str(item_id)}


@router.get("/skills/aggregated")
def get_aggregated_skills(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Get aggregated skill evidence across all sources.

    Aggregates evidence items from resume, GitHub, portfolio into
    unified skill list with weighted confidence scores.
    """
    from services.evidence.aggregation import aggregate_user_skills

    skills = aggregate_user_skills(user_id, session)

    # Sort by aggregated confidence descending
    skills.sort(key=lambda s: s["aggregated_confidence"], reverse=True)

    return {"skills": skills}


class PortfolioCrawlRequest(BaseModel):
    url: str


@router.post("/portfolio/crawl")
def crawl_portfolio(
    request: PortfolioCrawlRequest,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Crawl portfolio website and create evidence items."""
    from services.evidence.portfolio import PortfolioCrawlError, sync_portfolio_evidence

    try:
        return sync_portfolio_evidence(user_id, request.url, session)
    except PortfolioCrawlError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/portfolio/status")
def get_portfolio_status(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Check if user has connected portfolio."""
    from core.db.models.connected_account import ConnectedAccount

    account = session.query(ConnectedAccount).filter(
        ConnectedAccount.user_id == user_id,
        ConnectedAccount.provider == "portfolio"
    ).first()

    if not account:
        return {"connected": False}

    return {
        "connected": True,
        "url": account.provider_username,
        "last_synced_at": account.last_synced_at.isoformat() if account.last_synced_at else None
    }


@router.delete("/portfolio")
def disconnect_portfolio(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Disconnect portfolio and remove evidence."""
    from core.db.models.connected_account import ConnectedAccount
    from core.db.models.evidence_item import EvidenceItem

    # Remove connected account
    account = session.query(ConnectedAccount).filter(
        ConnectedAccount.user_id == user_id,
        ConnectedAccount.provider == "portfolio"
    ).first()

    if account:
        session.delete(account)

    # Remove portfolio evidence
    session.query(EvidenceItem).filter(
        EvidenceItem.user_id == user_id,
        EvidenceItem.source == "portfolio"
    ).delete()

    session.commit()

    return {"status": "disconnected"}


@router.get("/sources")
def get_evidence_sources(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """Metadata-driven connection sources, recommended by the user's current role.

    Returns:
      recommended: role'ün suggested_source_ids'indeki kaynaklar (öneri sırasıyla)
      all:         tüm kaynaklar (sort_order)
      connected:   kullanıcının bağlı provider'ları
      role_title:  "Recommended for {role}" başlığı için
    """
    import sqlalchemy as sa
    from core.db.models.evidence_source import EvidenceSource
    from core.db.models.connected_account import ConnectedAccount

    # 1) Kullanıcının current role'ü → suggested_source_ids
    user_row = session.execute(
        sa.text(
            "SELECT current_role_id, current_custom_role_id "
            "FROM users WHERE clerk_id = :uid"
        ),
        {"uid": user_id},
    ).fetchone()

    suggested_ids: list[str] = []
    role_title: str | None = None
    canonical_id = user_row[0] if user_row else None
    custom_id    = user_row[1] if user_row else None

    if canonical_id:
        # Canonical role → read its seeded suggestion list
        role_row = session.execute(
            sa.text(
                "SELECT title, metadata->'suggested_source_ids' "
                "FROM roles WHERE id = :rid"
            ),
            {"rid": str(canonical_id)},
        ).fetchone()
        if role_row:
            role_title = role_row[0]
            suggested_ids = role_row[1] or []
    elif custom_id:
        # Custom role → infer category from the free-text title
        custom_row = session.execute(
            sa.text("SELECT title FROM custom_roles WHERE id = :cid"),
            {"cid": str(custom_id)},
        ).fetchone()
        if custom_row:
            role_title = custom_row[0]
            inferred = _infer_category(role_title)
            if inferred:
                suggested_ids = _CATEGORY_SOURCES.get(inferred, [])

    # Final fallback
    if not suggested_ids:
        suggested_ids = _DEFAULT_SOURCES

    # 2) Tüm kaynaklar (registry'den — hardcoded değil)
    sources = session.query(EvidenceSource).order_by(EvidenceSource.sort_order).all()

    # 3) Bağlı hesaplar
    connected_rows = session.query(ConnectedAccount.provider).filter(
        ConnectedAccount.user_id == user_id,
        ConnectedAccount.is_active.is_(True),
    ).all()
    connected_providers = {r[0] for r in connected_rows}

    # 4) Birleştir
    def serialize(src: EvidenceSource) -> dict:
        provider_key = src.oauth_provider or src.id
        return {
            "id": src.id,
            "label": src.label,
            "icon": src.icon,
            "category": src.category,
            "status": src.status,                 # available | coming_soon
            "connect_kind": src.connect_kind,     # oauth | url | none
            "oauth_provider": src.oauth_provider,
            "connected": provider_key in connected_providers,
            "suggested": src.id in suggested_ids,
        }

    all_sources = [serialize(s) for s in sources]
    recommended = sorted(
        (s for s in all_sources if s["suggested"]),
        key=lambda s: suggested_ids.index(s["id"]) if s["id"] in suggested_ids else 999,
    )

    return {
        "recommended": recommended,
        "all": all_sources,
        "connected": {p: True for p in connected_providers},
        "role_title": role_title,
    }
