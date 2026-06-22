"""
User profile and job models.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
from .skill import Skill, SkillLevel


@dataclass
class Experience:
    """Work or project experience."""

    title: str
    company: str
    description: str
    start_date: datetime
    end_date: Optional[datetime] = None
    achievements: List[str] = field(default_factory=list)
    skills_used: List[str] = field(default_factory=list)

    @property
    def duration_months(self) -> int:
        """Calculate duration in months."""
        end = self.end_date or datetime.now()
        delta = end - self.start_date
        return int(delta.days / 30)

    @property
    def is_current(self) -> bool:
        """Is this ongoing?"""
        return self.end_date is None


@dataclass
class UserPreferences:
    """Job search preferences."""

    remote: bool = True
    hybrid_acceptable: bool = True
    onsite_acceptable: bool = False

    willing_to_relocate: bool = False
    preferred_locations: List[str] = field(default_factory=list)

    min_salary: Optional[int] = None
    max_salary: Optional[int] = None

    preferred_company_sizes: List[str] = field(default_factory=lambda: ["startup", "midsize"])
    """Options: startup, midsize, large, big_tech"""

    preferred_industries: List[str] = field(default_factory=list)

    work_visa_required: bool = True


@dataclass
class UserProfile:
    """
    Complete user profile for job matching.
    """

    # Identity
    name: str
    email: str

    # Skills (with proficiency levels)
    skills: List[Skill] = field(default_factory=list)

    # Experience
    experience: List[Experience] = field(default_factory=list)
    years_experience: float = 0.0

    # Education
    education: List[str] = field(default_factory=list)

    # AI proficiency
    ai_proficiency: float = 0.7
    """
    How effectively you leverage AI tools (0.0-1.0).
    0.3 = basic ChatGPT usage
    0.5 = regular Copilot user
    0.7 = proficient with Cursor/Claude
    0.9 = AI-native developer, advanced prompting
    """

    # Preferences
    preferences: UserPreferences = field(default_factory=UserPreferences)

    # Target roles
    target_roles: List[str] = field(default_factory=list)
    target_domains: List[str] = field(default_factory=list)

    # Resume text (for semantic matching)
    resume_text: str = ""

    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """Find skill by name."""
        for skill in self.skills:
            if skill.name.lower() == skill_name.lower():
                return skill
        return None

    def has_skill(self, skill_name: str, min_level: SkillLevel = SkillLevel.AI_ASSISTED) -> bool:
        """Check if user has skill at minimum level."""
        skill = self.get_skill(skill_name)
        return skill is not None and skill.level >= min_level

    def skill_names(self) -> List[str]:
        """Get list of all skill names."""
        return [s.name for s in self.skills]

    def high_proficiency_skills(self, min_level: SkillLevel = SkillLevel.INDEPENDENT) -> List[Skill]:
        """Get skills at or above proficiency level."""
        return [s for s in self.skills if s.level >= min_level]

    def update_skill(self, skill_name: str, level: SkillLevel):
        """Update or add skill."""
        existing = self.get_skill(skill_name)
        if existing:
            existing.level = level
        else:
            self.skills.append(Skill(name=skill_name, level=level))


@dataclass
class Job:
    """
    Job posting data.
    """

    # Basic info
    id: str
    title: str
    company: str
    description: str
    url: str

    # Location
    location: str
    remote: bool = False
    hybrid: bool = False

    # Requirements
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    required_years: float = 0.0

    # Compensation
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "USD"

    # Company info
    company_size: str = "unknown"
    """Options: startup, midsize, large, big_tech"""

    industry: str = "unknown"
    funding_stage: str = "unknown"

    # Logistics
    sponsors_visa: bool = False
    posted_date: Optional[datetime] = None
    source: str = "unknown"  # linkedin, indeed, etc.

    # Metadata
    fit_score: Optional[float] = None
    """Semantic fit score (0-100)"""

    acceptance_probability: Optional[float] = None
    """Estimated chance of getting the job (0-100)"""

    career_score: Optional[float] = None
    """Overall career value score (0-100)"""

    def days_since_posted(self) -> int:
        """Days since job was posted."""
        if not self.posted_date:
            return 0
        delta = datetime.now() - self.posted_date
        return delta.days

    def salary_range_str(self) -> str:
        """Formatted salary range."""
        if self.salary_min and self.salary_max:
            return f"${self.salary_min:,} - ${self.salary_max:,}"
        elif self.salary_min:
            return f"${self.salary_min:,}+"
        elif self.salary_max:
            return f"Up to ${self.salary_max:,}"
        return "Not specified"

    def all_skills(self) -> List[str]:
        """Combined required + preferred skills."""
        return list(set(self.required_skills + self.preferred_skills))


@dataclass
class MatchResult:
    """
    Result of matching user to job.
    """

    job: Job
    overall_score: float
    """Overall match score (0-100)"""

    breakdown: Dict[str, float]
    """
    Score breakdown by dimension:
    - technical_skills
    - domain_experience
    - seniority_level
    - work_mode
    - ai_capability
    """

    skill_gaps: List[str]
    """Skills required but not possessed"""

    confidence: float
    """Confidence in this match (0-1)"""

    explanation: str = ""
    """Human-readable explanation of the match"""

    def summary(self) -> str:
        """Generate summary text."""
        lines = [
            f"Match Score: {self.overall_score:.1f}/100",
            f"Confidence: {self.confidence:.0%}",
            "",
            "Breakdown:",
        ]

        for dimension, score in self.breakdown.items():
            lines.append(f"  {dimension}: {score:.1f}")

        if self.skill_gaps:
            lines.append("")
            lines.append(f"Missing {len(self.skill_gaps)} skills: {', '.join(self.skill_gaps[:5])}")

        return "\n".join(lines)


@dataclass
class OpportunityScore:
    """
    Comprehensive opportunity evaluation.
    """

    job: Job

    # Component scores (0-100)
    fit_score: float
    """How well you match the requirements"""

    acceptance_probability: float
    """Estimated chance of getting the job"""

    career_value: float
    """Long-term career benefit"""

    market_demand: float
    """Market demand for this role/skills"""

    # Combined score
    career_score: float
    """Weighted combination of all factors"""

    expected_value: float
    """fit × acceptance × career_value"""

    # Recommendation
    recommendation: str = ""
    """Apply, Consider, or Skip"""

    def should_apply(self, threshold: float = 60.0) -> bool:
        """Should apply to this job?"""
        return self.career_score >= threshold

    def priority_tier(self) -> str:
        """Priority tier for application."""
        if self.career_score >= 80:
            return "HIGH"
        elif self.career_score >= 60:
            return "MEDIUM"
        else:
            return "LOW"
