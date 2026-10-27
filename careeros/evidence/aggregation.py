"""Multi-source evidence aggregation for skill confidence scoring."""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from careeros.evidence.models.evidence_item import EvidenceItem
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

# Source weights (GitHub en güvenilir, resume en düşük)
SOURCE_WEIGHTS = {
    "github": 0.5,      # Gerçek kod, commit history
    "portfolio": 0.3,   # Kullanıcının seçtiği projeler
    "resume": 0.2       # Claim, evidence değil
}


def aggregate_user_skills(user_id: str, session: Session) -> List[Dict[str, Any]]:
    """
    Aggregate evidence items by skill across all sources.
    
    Groups all evidence items by skill_name, calculates weighted confidence
    across sources, and returns aggregated skill list.
    
    Args:
        user_id: Clerk user ID
        session: Database session
        
    Returns:
        List of aggregated skills with confidence scores and source breakdown
    """
    # Fetch all evidence items for user
    evidence_items = session.query(EvidenceItem).filter(
        EvidenceItem.user_id == user_id
    ).all()
    
    if not evidence_items:
        return []
    
    # Filter only "skill" type items in Python (type defaults to "skill" if not specified)
    skill_evidence = [
        item for item in evidence_items 
        if (item.evidence_data or {}).get("type", "skill") == "skill"
    ]
    
    if not skill_evidence:
        return []
    
    # Group by skill_name
    skill_groups = defaultdict(list)
    for item in skill_evidence:
        skill_groups[item.skill_name].append(item)
    
    # Aggregate each skill
    aggregated_skills = []
    
    for skill_name, items in skill_groups.items():
        # Group by source_type (item.source)
        source_groups = defaultdict(list)
        for item in items:
            source_groups[item.source].append(item)
        
        # Calculate source breakdown
        sources = []
        weighted_sum = 0.0
        total_weight = 0.0
        
        for source_type, source_items in source_groups.items():
            # Average confidence for this source
            avg_confidence = sum(item.confidence_score for item in source_items) / len(source_items)
            count = len(source_items)
            weight = SOURCE_WEIGHTS.get(source_type, 0.1)
            
            sources.append({
                "type": source_type,
                "confidence": round(avg_confidence, 3),
                "count": count
            })
            
            # Weighted contribution
            weighted_sum += avg_confidence * weight * count
            total_weight += weight * count
        
        # Calculate aggregated confidence
        aggregated_confidence = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # Get canonical_id (skill_id) from first item (they should all match)
        canonical_id = items[0].skill_id if items else None
        
        aggregated_skills.append({
            "skill_name": skill_name,
            "canonical_id": canonical_id,
            "aggregated_confidence": round(aggregated_confidence, 3),
            "sources": sources,
            "total_evidence_count": len(items)
        })
    
    logger.info(f"Aggregated {len(aggregated_skills)} skills from {len(skill_evidence)} evidence items")
    return aggregated_skills


def ranked_user_skills(user_id: str, session: Session) -> List[Dict[str, Any]]:
    """aggregate_user_skills, most confident first."""
    return sorted(aggregate_user_skills(user_id, session), key=lambda s: s["aggregated_confidence"], reverse=True)
