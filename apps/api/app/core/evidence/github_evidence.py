"""Create evidence items from GitHub repository analysis."""

from sqlalchemy.orm import Session
from core.db.models.evidence_item import EvidenceItem
from core.db.models.skill import Skill
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)


# Source weight for GitHub evidence (higher than resume)
GITHUB_CONFIDENCE_BASE = 0.85
GITHUB_CONFIDENCE_BOOST_STARS = 0.05  # per 10 stars
GITHUB_CONFIDENCE_BOOST_COMMITS = 0.02  # per 100 commits


def _find_canonical_skill(name: str, db: Session) -> tuple[str | None, str | None]:
    """Find canonical skill ID for a language/technology name."""
    name_lower = name.lower().strip()
    
    # Exact match
    skill = db.query(Skill).filter(Skill.name.ilike(name_lower)).first()
    if skill:
        return skill.id, skill.name
    
    # Alias match
    all_skills = db.query(Skill).all()
    for skill in all_skills:
        aliases = skill.aliases or []
        for alias in aliases:
            if alias.lower() == name_lower:
                return skill.id, skill.name
    
    # Fuzzy match
    best_match = None
    best_score = 0
    for skill in all_skills:
        ratio = SequenceMatcher(None, skill.name.lower(), name_lower).ratio()
        if ratio > best_score and ratio >= 0.8:
            best_score = ratio
            best_match = skill
    
    if best_match:
        return best_match.id, best_match.name
    
    return None, None


def _calculate_confidence(repo: dict, total_bytes: int, lang_bytes: int) -> float:
    """Calculate confidence score for a language in a repo."""
    # Base confidence
    confidence = GITHUB_CONFIDENCE_BASE
    
    # Language proportion in repo (higher = stronger signal)
    if total_bytes > 0:
        proportion = lang_bytes / total_bytes
        confidence += proportion * 0.1  # up to +0.1
    
    # Stars boost
    stars = repo.get("stars", 0)
    confidence += min(0.1, (stars // 10) * GITHUB_CONFIDENCE_BOOST_STARS)
    
    # Commits boost
    commits = repo.get("commits_count", 0)
    confidence += min(0.1, (commits // 100) * GITHUB_CONFIDENCE_BOOST_COMMITS)
    
    return min(0.99, confidence)


def create_github_evidence(
    user_id: str,
    repos: list[dict],
    source_id: str,
    session: Session,
) -> dict:
    """Create evidence items from GitHub repos.
    
    Returns:
        {"skills_created": int, "projects_created": int}
    """
    # Clear existing GitHub evidence (re-sync)
    session.query(EvidenceItem).filter(
        EvidenceItem.user_id == user_id,
        EvidenceItem.source == "github"
    ).delete()
    
    skills_created = 0
    projects_created = 0
    
    # Aggregate languages across all repos
    language_agg: dict[str, dict] = {}
    
    for repo in repos:
        languages = repo.get("languages", {})
        total_bytes = sum(languages.values())
        
        # Create project evidence
        if repo.get("name"):
            project_item = EvidenceItem(
                user_id=user_id,
                skill_name=repo["name"],
                source="github",
                source_url=repo.get("url"),
                confidence_score=0.85,
                evidence_data={
                    "type": "project",
                    "description": repo.get("description", ""),
                    "technologies": list(languages.keys()),
                    "stars": repo.get("stars", 0),
                    "url": repo.get("url"),
                }
            )
            session.add(project_item)
            projects_created += 1
        
        # Aggregate language bytes
        for lang, bytes_count in languages.items():
            if lang not in language_agg:
                language_agg[lang] = {
                    "total_bytes": 0,
                    "repo_count": 0,
                    "repos": [],
                }
            language_agg[lang]["total_bytes"] += bytes_count
            language_agg[lang]["repo_count"] += 1
            language_agg[lang]["repos"].append(repo)
    
    # Create skill evidence for each language
    for lang, data in language_agg.items():
        canonical_id, canonical_name = _find_canonical_skill(lang, session)
        
        avg_confidence = sum(
            _calculate_confidence(
                r,
                sum(r.get("languages", {}).values()),
                r.get("languages", {}).get(lang, 0)
            )
            for r in data["repos"]
        ) / len(data["repos"])
        
        skill_item = EvidenceItem(
            user_id=user_id,
            skill_name=canonical_name or lang,
            skill_id=int(canonical_id) if canonical_id and str(canonical_id).isdigit() else None,
            source="github",
            confidence_score=round(avg_confidence, 3),
            evidence_data={
                "type": "skill",
                "bytes_written": data["total_bytes"],
                "repo_count": data["repo_count"],
                "matched_canonical": canonical_name,
            }
        )
        session.add(skill_item)
        skills_created += 1
    
    session.commit()
    
    logger.info(
        f"GitHub evidence: {skills_created} skills, {projects_created} projects"
    )
    
    return {
        "skills_created": skills_created,
        "projects_created": projects_created,
    }
