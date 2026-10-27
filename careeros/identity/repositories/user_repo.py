"""Repository for the users table (Clerk-backed identities)."""

from typing import Optional

from sqlalchemy.dialects.postgresql import insert

from careeros.identity.models.user import User
from careeros.identity.domain.onboarding import OnboardingState
from careeros.db.repository import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_clerk_id(self, clerk_id: str) -> Optional[User]:
        return self.get(clerk_id=clerk_id)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.get(email=email)

    def create_user(
        self,
        *,
        clerk_id: str,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> User:
        """Insert a new user row. Raises IntegrityError if clerk_id already exists."""
        return self.create(
            clerk_id=clerk_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            image_url=image_url,
            onboarding_state=OnboardingState.NOT_STARTED.value,
            profile_data={},
            goals={},
        )

    def upsert_from_clerk(
        self,
        *,
        clerk_id: str,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> User:
        """Create or update from a Clerk webhook payload. Idempotent."""
        stmt = (
            insert(User)
            .values(
                clerk_id=clerk_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                image_url=image_url,
                onboarding_state=OnboardingState.NOT_STARTED.value,
                profile_data={},
                goals={},
            )
            .on_conflict_do_update(
                index_elements=["clerk_id"],
                set_={
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "image_url": image_url,
                },
            )
            .returning(User)
        )
        result = self.session.execute(stmt)
        self.session.flush()
        return result.scalar_one()

    def advance_onboarding(self, clerk_id: str) -> Optional[User]:
        user = self.get_by_clerk_id(clerk_id)
        if user is None:
            return None
        user.advance_onboarding()
        self.session.flush()
        return user

    def set_onboarding_state(self, clerk_id: str, state: OnboardingState) -> Optional[User]:
        user = self.get_by_clerk_id(clerk_id)
        if user is None:
            return None
        user.onboarding_state = state.value
        self.session.flush()
        return user

    def patch_profile_data(self, clerk_id: str, data: dict) -> Optional[User]:
        user = self.get_by_clerk_id(clerk_id)
        if user is None:
            return None
        user.profile_data = {**(user.profile_data or {}), **data}
        self.session.flush()
        return user

    def patch_goals(self, clerk_id: str, data: dict) -> Optional[User]:
        user = self.get_by_clerk_id(clerk_id)
        if user is None:
            return None
        user.goals = {**(user.goals or {}), **data}
        self.session.flush()
        return user
