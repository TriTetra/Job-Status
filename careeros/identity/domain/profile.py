"""User profile domain entities."""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

from careeros.identity.domain.skill import Skill, SkillLevel


@dataclass
class Experience:
    """Work or project experience entry."""

    title: str
    company: str
    description: str
    start_date: datetime
    end_date: Optional[datetime] = None
    achievements: List[str] = field(default_factory=list)
    skills_used: List[str] = field(default_factory=list)

    @property
    def duration_months(self) -> int:
        end = self.end_date or datetime.now()
        return int((end - self.start_date).days / 30)

    @property
    def is_current(self) -> bool:
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
    preferred_industries: List[str] = field(default_factory=list)
    work_visa_required: bool = True


@dataclass
class UserProfile:
    """Complete user profile for job matching."""

    name: str
    email: str
    skills: List[Skill] = field(default_factory=list)
    experience: List[Experience] = field(default_factory=list)
    years_experience: float = 0.0
    education: List[str] = field(default_factory=list)
    ai_proficiency: float = 0.7
    preferences: UserPreferences = field(default_factory=UserPreferences)
    target_roles: List[str] = field(default_factory=list)
    target_domains: List[str] = field(default_factory=list)
    resume_text: str = ""

    def get_skill(self, skill_name: str) -> Optional[Skill]:
        for skill in self.skills:
            if skill.name.lower() == skill_name.lower():
                return skill
        return None

    def has_skill(self, skill_name: str, min_level: SkillLevel = SkillLevel.AI_ASSISTED) -> bool:
        skill = self.get_skill(skill_name)
        return skill is not None and skill.level >= min_level

    def skill_names(self) -> List[str]:
        return [s.name for s in self.skills]

    def high_proficiency_skills(self, min_level: SkillLevel = SkillLevel.INDEPENDENT) -> List[Skill]:
        return [s for s in self.skills if s.level >= min_level]

    def update_skill(self, skill_name: str, level: SkillLevel) -> None:
        existing = self.get_skill(skill_name)
        if existing:
            existing.level = level
        else:
            self.skills.append(Skill(name=skill_name, level=level))
