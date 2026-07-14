"""
Thread-safe in-memory event bus.

Features:
- Subscribe/publish pattern
- Type-safe (handlers receive specific event types)
- Error isolation (one handler failure doesn't break others)
- Event history (last N events stored for debugging)
- Singleton pattern (global instance)

Future: Replace internals with Redis Streams for production.
"""

import threading
from collections import defaultdict, deque
from typing import Any, Callable, Deque, Dict, List, Type


class EventBus:
    """
    In-memory event bus with thread-safe pub/sub.

    Usage:
        bus = EventBus()
        bus.subscribe(MyEvent, handler)
        bus.publish(MyEvent(...))
    """

    def __init__(self, history_size: int = 1000) -> None:
        self._subscribers: Dict[Type, List[Callable]] = defaultdict(list)
        self._lock = threading.RLock()  # Reentrant for nested publishes
        self._history: Deque[Any] = deque(maxlen=history_size)
        self._publish_count = 0
        self._error_count = 0

    def subscribe(self, event_type: Type, handler: Callable = None) -> Callable:
        """
        Subscribe handler to event type.

        Two calling styles are supported:

            # Direct:
            event_bus.subscribe(JobScored, my_handler)

            # Decorator:
            @event_bus.subscribe(JobScored)
            def on_job_scored(event): ...
        """
        if handler is None:
            # Decorator mode — return a function that does the actual subscribe
            def decorator(fn: Callable) -> Callable:
                return self.subscribe(event_type, fn)
            return decorator

        with self._lock:
            if handler not in self._subscribers[event_type]:
                self._subscribers[event_type].append(handler)
        return handler

    def unsubscribe(self, event_type: Type, handler: Callable) -> None:
        """Remove handler from event type."""
        with self._lock:
            if handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)

    def publish(self, event: Any) -> int:
        """
        Publish event to all subscribers.

        Returns number of handlers successfully invoked.
        Handler exceptions are caught and logged — they do not propagate.
        """
        event_type = type(event)

        with self._lock:
            handlers = list(self._subscribers.get(event_type, []))
            self._history.append(event)
            self._publish_count += 1

        success_count = 0
        for handler in handlers:
            try:
                handler(event)
                success_count += 1
            except Exception as exc:
                self._error_count += 1
                print(
                    f"[EventBus] Handler error for {event_type.__name__}: "
                    f"{type(exc).__name__}: {exc}"
                )

        return success_count

    def get_history(
        self, event_type: Type = None, limit: int = 100
    ) -> List[Any]:
        """
        Get recent event history, newest first.

        Args:
            event_type: Filter by type (None = all).
            limit: Max events to return.
        """
        with self._lock:
            events = list(self._history)

        if event_type:
            events = [e for e in events if isinstance(e, event_type)]

        return list(reversed(events[-limit:]))

    def clear(self) -> None:
        """Clear all subscribers and history (for testing)."""
        with self._lock:
            self._subscribers.clear()
            self._history.clear()
            self._publish_count = 0
            self._error_count = 0

    def stats(self) -> Dict[str, Any]:
        """Return bus diagnostics."""
        with self._lock:
            return {
                "subscriber_count": sum(
                    len(h) for h in self._subscribers.values()
                ),
                "event_types": len(self._subscribers),
                "publish_count": self._publish_count,
                "error_count": self._error_count,
                "history_size": len(self._history),
            }


# Global singleton
event_bus = EventBus()
