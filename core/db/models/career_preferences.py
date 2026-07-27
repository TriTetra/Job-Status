"""CareerPreferences model — user's career intent vector."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from core.db.models.base import Base


class CareerPreferences(Base):
    __tablename__ = 'career_preferences'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default='gen_random_uuid()')
    user_id = Column(String(128), ForeignKey('users.clerk_id'), nullable=False, unique=True)

    goal_ids = Column(JSONB, server_default='[]')
    preferred_role_ids = Column(JSONB, server_default='[]')
    preferred_country_codes = Column(JSONB, server_default='[]')
    work_arrangements = Column(JSONB, server_default='[]')

    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    salary_currency = Column(String(3), nullable=True)
    salary_period = Column(String(10), server_default='year')
    salary_negotiable = Column(Boolean, server_default='true')
    requires_sponsorship = Column(Boolean, nullable=True)
    contract_types = Column(JSONB, server_default='[]')      # ["full_time","contract"]
    availability = Column(String(30), nullable=True)         # immediately|2_weeks|1_month|3_months_plus
    target_seniority = Column(String(20), nullable=True)     # junior|mid|senior|staff|principal

    pref_metadata = Column(JSONB, server_default='{}')

    created_at = Column(DateTime(timezone=True), server_default='now()')
    updated_at = Column(DateTime(timezone=True), server_default='now()', onupdate=datetime.utcnow)

    user = relationship('User', backref='career_preferences', uselist=False)

    def __repr__(self):
        return (
            f"<CareerPreferences(user_id={self.user_id}, "
            f"goals={len(self.goal_ids or [])}, "
            f"roles={len(self.preferred_role_ids or [])})>"
        )
