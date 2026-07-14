"""Base event types and metadata."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Event:
    """
    Base class for all domain events.

    All events have:
    - event_id: Unique identifier (UUID)
    - timestamp: When event occurred (UTC)
    - source: Which component emitted the event
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = "unknown"

    def to_dict(self) -> dict:
        """Serialize event to dict (for logging/persistence)."""
        from dataclasses import asdict
        return asdict(self)
