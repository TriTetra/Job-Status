"""Evidence items as the user reviews them: grouped list, delete false positives."""

import logging
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from careeros.evidence.models.evidence_item import EvidenceItem

logger = logging.getLogger(__name__)

# evidence_data.type → review bucket; anything else (incl. no type) is a skill
_BUCKETS = {"project": "projects", "experience": "experiences", "education": "education", "certification": "certifications"}


def group_for_review(items: Iterable[EvidenceItem]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {"skills": [], "projects": [], "experiences": [], "education": [], "certifications": []}
    for item in items:
        data = item.evidence_data or {}
        groups[_BUCKETS.get(data.get("type", "skill"), "skills")].append({
            "id": str(item.id),
            "name": item.skill_name,
            "skill_id": item.skill_id,
            "confidence": item.confidence_score,
            "source": item.source,
            "source_url": item.source_url,
            "evidence_text": item.evidence_text,
            "evidence_data": data,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        })
    return groups


def list_for_review(session: Session, user_id: str, source: Optional[str] = None) -> dict[str, list[dict]]:
    """The user's items (optionally one source), most confident first, grouped by kind."""
    query = session.query(EvidenceItem).filter(EvidenceItem.user_id == user_id)
    if source:
        query = query.filter(EvidenceItem.source == source)
    return group_for_review(query.order_by(EvidenceItem.confidence_score.desc()).all())


def delete_item(session: Session, user_id: str, item_id: int) -> bool:
    """Remove one of the user's items (a false positive). False if it is not theirs / not found."""
    item = session.query(EvidenceItem).filter(EvidenceItem.id == item_id, EvidenceItem.user_id == user_id).first()
    if not item:
        return False
    session.delete(item)
    session.commit()
    logger.info("User %s deleted evidence item %s", user_id, item_id)
    return True


def count_for_user(session: Session, user_id: str) -> int:
    return session.query(EvidenceItem).filter(EvidenceItem.user_id == user_id).count()
