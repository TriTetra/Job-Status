"""Login attempt limits — slows down password guessing.

In process memory, like the rest of the single-worker API state: counters reset
on restart, which is acceptable for a private app with a handful of users.
"""

import threading
import time
from collections import defaultdict, deque

WINDOW_SECONDS = 15 * 60
MAX_FAILURES_PER_EMAIL = 5
MAX_FAILURES_PER_IP = 20


class LoginThrottle:
    def __init__(self, window: float = WINDOW_SECONDS, per_email: int = MAX_FAILURES_PER_EMAIL,
                 per_ip: int = MAX_FAILURES_PER_IP, clock=time.monotonic) -> None:
        self._window, self._per_email, self._per_ip, self._clock = window, per_email, per_ip, clock
        self._failures: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def _recent(self, key: str) -> deque:
        q = self._failures[key]
        cutoff = self._clock() - self._window
        while q and q[0] < cutoff:
            q.popleft()
        return q

    def retry_after(self, email: str, ip: str | None) -> int:
        """Seconds until another attempt is allowed (0 = allowed now)."""
        with self._lock:
            waits = []
            for key, limit in ((f"email:{email.lower()}", self._per_email), (f"ip:{ip}", self._per_ip)):
                q = self._recent(key)
                if len(q) >= limit:
                    waits.append(int(q[0] + self._window - self._clock()) + 1)
            return max(waits, default=0)

    def record_failure(self, email: str, ip: str | None) -> None:
        now = self._clock()
        with self._lock:
            self._failures[f"email:{email.lower()}"].append(now)
            self._failures[f"ip:{ip}"].append(now)

    def record_success(self, email: str) -> None:
        with self._lock:
            self._failures.pop(f"email:{email.lower()}", None)


login_throttle = LoginThrottle()
