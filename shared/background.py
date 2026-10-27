"""In-process tracking for long-running background work (scan, CV extraction, graph build).

A job is created by a request handler, filled in by a background task and
polled by the client. State lives in process memory: it is lost on restart and
is not shared between workers — swap JobStore for a Redis-backed one before
running more than one API worker.
"""

import threading
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional


class JobNotFound(LookupError):
    pass


class JobForbidden(PermissionError):
    pass


class BackgroundJob:
    def __init__(self, owner_id: str, label: str = "") -> None:
        self.job_id = str(uuid.uuid4())
        self.owner_id = owner_id
        self.label = label
        self.status = "pending"
        self.progress = 0
        self.logs: list[dict] = []
        self.result: Any = None
        self.error: Optional[str] = None
        self.created_at = datetime.utcnow()

    def log(self, message: str, type: str = "info") -> None:
        self.logs.append({"timestamp": datetime.utcnow().isoformat(), "message": message, "type": type})

    def update(self, **fields: Any) -> None:
        for key, value in fields.items():
            setattr(self, key, value)

    def fail(self, error: Exception | str, message: Optional[str] = None) -> None:
        self.status = "failed"
        self.error = str(error)
        self.log(message or f"✗ {error}", "error")

    def to_dict(self) -> dict:
        """Wire format polled by the web client."""
        return {
            "job_id": self.job_id,
            "status": self.status,
            "progress": self.progress,
            "logs": self.logs,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
        }


class JobStore:
    def __init__(self, max_age: timedelta = timedelta(hours=6)) -> None:
        self._jobs: dict[str, BackgroundJob] = {}
        self._lock = threading.Lock()
        self._max_age = max_age

    def create(self, owner_id: str, label: str = "") -> BackgroundJob:
        job = BackgroundJob(owner_id, label)
        with self._lock:
            self._prune()
            self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> BackgroundJob:
        job = self._jobs.get(job_id)
        if job is None:
            raise JobNotFound(job_id)
        return job

    def get_owned(self, job_id: str, owner_id: str) -> BackgroundJob:
        job = self.get(job_id)
        if job.owner_id != owner_id:
            raise JobForbidden(job_id)
        return job

    def __len__(self) -> int:
        return len(self._jobs)

    def _prune(self) -> None:
        """Forget finished jobs older than max_age so the store does not grow forever."""
        cutoff = datetime.utcnow() - self._max_age
        stale = [
            jid for jid, j in self._jobs.items()
            if j.created_at < cutoff and j.status in ("completed", "failed")
        ]
        for jid in stale:
            del self._jobs[jid]
