"""
CareerOS Event Bus -- domain event pub/sub system.

Phase 1: In-memory implementation
Phase 2: Redis Streams (production)

Usage:
    from events import event_bus
    from events.job_events import JobScored

    event_bus.subscribe(JobScored, handler)
    event_bus.publish(JobScored(job_id="x", score=85, ...))
"""

from .event_bus import EventBus, event_bus
from .event_types import Event

__all__ = ["event_bus", "EventBus", "Event"]
