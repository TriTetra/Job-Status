"""Registry of every ORM model — imported by db.connection and Alembic.

Models live in their feature package; import them from there in code.
"""

from careeros.db.base import Base, TimestampMixin
from careeros.identity.models.user import User
from careeros.identity.models.auth import AuthCredential, AuthSession
from careeros.identity.models.role import Role
from careeros.identity.models.custom_role import CustomRole
from careeros.identity.models.user_role import UserRole
from careeros.identity.models.role_alias import RoleAlias
from careeros.jobs.models.career_score import CareerScore
from careeros.applications.models.application import Application
from careeros.applications.models.email import Email
from careeros.jobs.models.scan_history import ScanHistory
from careeros.db.legacy.evidence import Evidence
from careeros.jobs.models.job import Job
from careeros.identity.models.user_settings import UserSettings
from careeros.identity.models.user_custom_skills import UserCustomSkill
from careeros.companies.models.company import Company
from careeros.companies.models.company_memory import CompanyMemory
from careeros.market.models.market_signal import MarketSignal
from careeros.db.legacy.timeline import TimelineSnapshot, TimelineChange
from careeros.knowledge.models.country import Country
from careeros.knowledge.models.visa import Visa
from careeros.knowledge.models.salary_range import SalaryRange
from careeros.identity.models.career_preferences import CareerPreferences
from careeros.evidence.models.resume_document import ResumeDocument
from careeros.evidence.models.skill import Skill
from careeros.evidence.models.evidence_item import EvidenceItem
from careeros.identity.models.connected_account import ConnectedAccount
from careeros.onboarding.models.career_graph_node import CareerGraphNode
from careeros.onboarding.models.goal import Goal
from careeros.market.models.market_skill import MarketSkill

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "AuthCredential",
    "AuthSession",
    "Role",
    "CustomRole",
    "UserRole",
    "RoleAlias",
    "CareerScore",
    "Application",
    "Email",
    "ScanHistory",
    "Evidence",
    "Job",
    "UserSettings",
    "UserCustomSkill",
    "Company",
    "CompanyMemory",
    "MarketSignal",
    "TimelineSnapshot",
    "TimelineChange",
    "Country",
    "Visa",
    "SalaryRange",
    "CareerPreferences",
    "ResumeDocument",
    "Skill",
    "EvidenceItem",
    "ConnectedAccount",
    "CareerGraphNode",
    "Goal",
    "MarketSkill",
]
