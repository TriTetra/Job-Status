"""CareerPreferences repository — CRUD for user career intent."""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from careeros.identity.models.career_preferences import CareerPreferences


class CareerPreferencesRepository:

    def __init__(self, session: Session):
        self.session = session

    def get_by_user_id(self, user_id: str) -> Optional[CareerPreferences]:
        return self.session.query(CareerPreferences).filter_by(user_id=user_id).first()

    def create(self, user_id: str, **kwargs) -> CareerPreferences:
        prefs = CareerPreferences(user_id=user_id, **kwargs)
        self.session.add(prefs)
        self.session.flush()
        return prefs

    def upsert(self, user_id: str, **kwargs) -> CareerPreferences:
        prefs = self.get_by_user_id(user_id)
        if not prefs:
            return self.create(user_id, **kwargs)
        for key, value in kwargs.items():
            setattr(prefs, key, value)
        prefs.updated_at = datetime.utcnow()
        return prefs

    def patch(self, user_id: str, updates: Dict[str, Any]) -> Optional[CareerPreferences]:
        prefs = self.get_by_user_id(user_id)
        if not prefs:
            return None
        for key, value in updates.items():
            if value is not None and hasattr(prefs, key):
                setattr(prefs, key, value)
        prefs.updated_at = datetime.utcnow()
        return prefs

    def delete(self, user_id: str) -> bool:
        prefs = self.get_by_user_id(user_id)
        if prefs:
            self.session.delete(prefs)
            return True
        return False
