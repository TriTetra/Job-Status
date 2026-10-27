"""Repository for the users table."""

from typing import Optional

from careeros.db.repository import BaseRepository
from careeros.identity.domain.onboarding import OnboardingState
from careeros.identity.models.user import User


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self.get(id=user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.get(email=email)

    def create_user(
        self,
        *,
        user_id: str,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> User:
        """Insert a new user row. Raises IntegrityError if the id or email already exists."""
        return self.create(
            id=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            onboarding_state=OnboardingState.NOT_STARTED.value,
            profile_data={},
            goals={},
        )

    def advance_onboarding(self, user_id: str) -> Optional[User]:
        user = self.get_by_id(user_id)
        if user is None:
            return None
        user.advance_onboarding()
        self.session.flush()
        return user

    def set_onboarding_state(self, user_id: str, state: OnboardingState) -> Optional[User]:
        user = self.get_by_id(user_id)
        if user is None:
            return None
        user.onboarding_state = state.value
        self.session.flush()
        return user

    def patch_profile_data(self, user_id: str, data: dict) -> Optional[User]:
        user = self.get_by_id(user_id)
        if user is None:
            return None
        user.profile_data = {**(user.profile_data or {}), **data}
        self.session.flush()
        return user

    def patch_goals(self, user_id: str, data: dict) -> Optional[User]:
        user = self.get_by_id(user_id)
        if user is None:
            return None
        user.goals = {**(user.goals or {}), **data}
        self.session.flush()
        return user
