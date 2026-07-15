"""CareerOS Domain Entities — pure business objects, no external dependencies."""

from .identity.user import User, OnboardingState
from .identity.skill import Skill, SkillLevel, SKILL_CATEGORIES, categorize_skill
from .identity.profile import UserProfile, UserPreferences, Experience
from .job.job import Job
from .intelligence.match import MatchResult
from .intelligence.scoring import OpportunityScore
from .company.company import Company, TechHub
from .resume.resume import Resume, ResumeSection
from .resume.evidence import Evidence
from .market.market_signal import MarketSignal
from .application.application import Application, ApplicationStatus
from .learning.skill_gap import SkillGap, LearningTask, LearningRoadmap
from .learning.roi import SkillROI
from .analytics.funnel import ApplicationFunnel, FunnelStage
from .analytics.metrics import AnalyticsMetrics

__all__ = [
    # Identity
    "User", "OnboardingState",
    "Skill", "SkillLevel", "SKILL_CATEGORIES", "categorize_skill",
    "UserProfile", "UserPreferences", "Experience",
    # Job
    "Job",
    # Intelligence
    "MatchResult", "OpportunityScore",
    # Company
    "Company", "TechHub",
    # Resume
    "Resume", "ResumeSection", "Evidence",
    # Market
    "MarketSignal",
    # Application
    "Application", "ApplicationStatus",
    # Learning
    "SkillGap", "LearningTask", "LearningRoadmap", "SkillROI",
    # Analytics
    "ApplicationFunnel", "FunnelStage", "AnalyticsMetrics",
]
