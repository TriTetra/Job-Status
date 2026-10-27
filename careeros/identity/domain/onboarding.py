"""Onboarding wizard states — pure domain enum (persisted as a string on users)."""

from enum import Enum
from typing import Optional


class OnboardingState(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IDENTITY = "IDENTITY"
    GOALS = "GOALS"
    EVIDENCE = "EVIDENCE"
    CONNECTIONS = "CONNECTIONS"
    BUILDING = "BUILDING"
    READY = "READY"

    @staticmethod
    def next_state(current: str) -> Optional[str]:
        order = [s.value for s in OnboardingState]
        try:
            idx = order.index(current)
        except ValueError:
            return None
        return order[idx + 1] if idx + 1 < len(order) else None

    def next(self) -> Optional["OnboardingState"]:
        nxt = OnboardingState.next_state(self.value)
        return OnboardingState(nxt) if nxt else None

    @property
    def is_complete(self) -> bool:
        return self == OnboardingState.READY
