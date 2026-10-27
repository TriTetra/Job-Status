"""Onboarding request/response schemas."""

from typing import Optional

from pydantic import BaseModel, Field


class IdentityPayload(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    current_role_id: str = Field(..., min_length=1, max_length=200)
    current_role_title: str = Field(..., min_length=1, max_length=150)
    years_in_role: float = Field(..., ge=0, le=50)
    career_level: Optional[str] = Field(None, pattern="^(entry|mid|senior|lead|expert)$")
    career_level_origin: str = Field("system", pattern="^(user|system|ai_estimated)$")
    country: str = Field(..., min_length=1, max_length=100)
    total_years: Optional[float] = Field(None, ge=0, le=50)
    languages: list[dict] = Field(default_factory=list)        # [{"code":"English","level":"C1"}]
    education_level: Optional[str] = Field(None, pattern="^(none|bachelor|master|phd)$")


class GoalsPayload(BaseModel):
    goal_ids: list[str] = Field(..., min_length=1, max_length=5)
    preferred_role_ids: list[str] = Field(..., min_length=1, max_length=5)
    preferred_country_codes: list[str] = Field(..., min_length=1, max_length=5)
    work_arrangements: list[str] = Field(default_factory=list, max_length=3)
    requires_sponsorship: Optional[bool] = Field(None)
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    salary_currency: Optional[str] = Field(None, max_length=3)
    salary_period: str = Field("year", pattern="^(year|month|hour|day|project)$")
    salary_negotiable: bool = Field(True)
    contract_types: list[str] = Field(default_factory=list, max_length=4)
    availability: Optional[str] = Field(None, pattern="^(immediately|2_weeks|1_month|3_months_plus)$")
    target_seniority: Optional[str] = Field(None, pattern="^(entry|mid|senior|lead|expert)$")


class OnboardingStateOut(BaseModel):
    state: str
    profile_data: dict
    preferences: Optional[dict] = None
    next_step: Optional[str]
