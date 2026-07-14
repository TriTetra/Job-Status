"""
Timeline — track and query entity changes over time.

Usage:
    from packages.timeline import Timeline

    tl = Timeline()

    tl.track_snapshot(
        entity_type="job",
        entity_id="https://example.com/job/123",
        data={"career_score": 87, "company": "Google"},
    )

    history = tl.get_entity_history("job", "https://example.com/job/123", days=30)
    changes = tl.detect_changes("job", "https://example.com/job/123", field="career_score")
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import sqlalchemy as sa
from sqlalchemy.orm import Session

from packages.db.connection import db
from packages.db.models import TimelineChange, TimelineSnapshot


@dataclass
class EntityChange:
    entity_type: str
    entity_id: str
    field_name: str
    old_value: Any
    new_value: Any
    changed_at: datetime
    change_type: str

    def format_for_display(self) -> str:
        if self.change_type == "created":
            return f"{self.field_name}: created -> {self.new_value}"
        if self.change_type == "deleted":
            return f"{self.field_name}: deleted (was {self.old_value})"
        try:
            old_num = float(self.old_value)
            new_num = float(self.new_value)
            if old_num > 0:
                pct = ((new_num - old_num) / old_num) * 100
                arrow = "^" if pct > 0 else "v"
                return f"{self.field_name}: {old_num:.1f} -> {new_num:.1f} ({arrow}{abs(pct):.1f}%)"
        except (ValueError, TypeError):
            pass
        return f"{self.field_name}: {self.old_value} -> {self.new_value}"


class Timeline:
    """Track and query entity state changes over time."""

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def track_snapshot(
        self,
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any],
        snapshot_at: Optional[datetime] = None,
        detect_changes: bool = True,
    ) -> TimelineSnapshot:
        """
        Persist an entity snapshot and optionally auto-detect field changes
        by diffing against the most recent previous snapshot.
        """
        snapshot_at = snapshot_at or datetime.utcnow()

        with db.session_scope() as session:
            snapshot = TimelineSnapshot(
                entity_type=entity_type,
                entity_id=entity_id,
                snapshot_at=snapshot_at,
                snapshot_data=data,
            )
            session.add(snapshot)
            session.flush()

            if detect_changes:
                self._record_changes(session, entity_type, entity_id, data, snapshot_at)

        return snapshot

    def _record_changes(
        self,
        session: Session,
        entity_type: str,
        entity_id: str,
        new_data: Dict[str, Any],
        snapshot_at: datetime,
    ) -> None:
        prev = session.execute(
            sa.select(TimelineSnapshot)
            .where(
                TimelineSnapshot.entity_type == entity_type,
                TimelineSnapshot.entity_id == entity_id,
                TimelineSnapshot.snapshot_at < snapshot_at,
            )
            .order_by(TimelineSnapshot.snapshot_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        if prev is None:
            for field, value in new_data.items():
                session.add(TimelineChange(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    changed_at=snapshot_at,
                    field_name=field,
                    old_value=None,
                    new_value=self._serialize(value),
                    change_type="created",
                ))
            return

        old_data = prev.snapshot_data or {}

        for field, new_val in new_data.items():
            old_val = old_data.get(field)
            if old_val != new_val:
                session.add(TimelineChange(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    changed_at=snapshot_at,
                    field_name=field,
                    old_value=self._serialize(old_val),
                    new_value=self._serialize(new_val),
                    change_type="created" if field not in old_data else "updated",
                ))

        for field, old_val in old_data.items():
            if field not in new_data:
                session.add(TimelineChange(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    changed_at=snapshot_at,
                    field_name=field,
                    old_value=self._serialize(old_val),
                    new_value=None,
                    change_type="deleted",
                ))

    @staticmethod
    def _serialize(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, (str, int, float, bool, list, dict)):
            return value
        return str(value)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_entity_history(
        self,
        entity_type: str,
        entity_id: str,
        days: int = 30,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Return snapshots for an entity, newest first."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        with db.session_scope() as session:
            rows = session.execute(
                sa.select(TimelineSnapshot)
                .where(
                    TimelineSnapshot.entity_type == entity_type,
                    TimelineSnapshot.entity_id == entity_id,
                    TimelineSnapshot.snapshot_at >= cutoff,
                )
                .order_by(TimelineSnapshot.snapshot_at.desc())
                .limit(limit)
            ).scalars().all()

        return [{"snapshot_at": s.snapshot_at, "data": s.snapshot_data} for s in rows]

    def detect_changes(
        self,
        entity_type: str,
        entity_id: str,
        field: Optional[str] = None,
        days: int = 30,
        limit: int = 50,
    ) -> List[EntityChange]:
        """Return recorded field-level changes for an entity, newest first."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        with db.session_scope() as session:
            stmt = (
                sa.select(TimelineChange)
                .where(
                    TimelineChange.entity_type == entity_type,
                    TimelineChange.entity_id == entity_id,
                    TimelineChange.changed_at >= cutoff,
                )
            )
            if field:
                stmt = stmt.where(TimelineChange.field_name == field)
            stmt = stmt.order_by(TimelineChange.changed_at.desc()).limit(limit)
            rows = session.execute(stmt).scalars().all()

        return [self._to_entity_change(r) for r in rows]

    def get_trending_entities(
        self,
        entity_type: str,
        field: str,
        days: int = 30,
        limit: int = 10,
        direction: str = "up",
    ) -> List[Dict[str, Any]]:
        """Return entities with the biggest numeric change in a field."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        with db.session_scope() as session:
            rows = session.execute(
                sa.select(TimelineChange)
                .where(
                    TimelineChange.entity_type == entity_type,
                    TimelineChange.field_name == field,
                    TimelineChange.changed_at >= cutoff,
                    TimelineChange.change_type == "updated",
                )
            ).scalars().all()

        # Aggregate per entity: first old_value, last new_value
        buckets: Dict[str, Dict] = {}
        for r in sorted(rows, key=lambda x: x.changed_at):
            eid = r.entity_id
            if eid not in buckets:
                buckets[eid] = {"first": r.old_value, "last": r.new_value}
            else:
                buckets[eid]["last"] = r.new_value

        results = []
        for eid, v in buckets.items():
            try:
                first = float(v["first"])
                last = float(v["last"])
                if first > 0:
                    pct = ((last - first) / first) * 100
                    results.append({
                        "entity_id": eid,
                        "old_value": first,
                        "new_value": last,
                        "change": last - first,
                        "change_pct": pct,
                    })
            except (ValueError, TypeError):
                continue

        results.sort(key=lambda x: x["change_pct"], reverse=(direction == "up"))
        return results[:limit]

    def get_recent_changes(
        self,
        entity_type: Optional[str] = None,
        days: int = 7,
        limit: int = 50,
    ) -> List[EntityChange]:
        """Return all recent changes, optionally filtered by entity_type."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        with db.session_scope() as session:
            stmt = (
                sa.select(TimelineChange)
                .where(TimelineChange.changed_at >= cutoff)
            )
            if entity_type:
                stmt = stmt.where(TimelineChange.entity_type == entity_type)
            stmt = stmt.order_by(TimelineChange.changed_at.desc()).limit(limit)
            rows = session.execute(stmt).scalars().all()

        return [self._to_entity_change(r) for r in rows]

    @staticmethod
    def _to_entity_change(r: TimelineChange) -> EntityChange:
        return EntityChange(
            entity_type=r.entity_type,
            entity_id=r.entity_id,
            field_name=r.field_name,
            old_value=r.old_value,
            new_value=r.new_value,
            changed_at=r.changed_at,
            change_type=r.change_type or "updated",
        )
