# transport/repositories/tracking/transport_event_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from repositories.base import SchoolScopedRepository
from transport.models.tracking import TransportEvent


class TransportEventRepository(SchoolScopedRepository[TransportEvent]):
    """
    Repository for TransportEvent model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    NOTE: TransportEvent model does NOT have is_deleted - immutable audit log.
    NO soft-delete filtering applied.
    Zero business logic, zero event validation, zero authorization decisions.
    Append-only log table - avoid update-heavy APIs.
    """

    def __init__(self):
        super().__init__(TransportEvent)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        school_id: UUID,
        event_id: UUID
    ) -> Optional[TransportEvent]:
        """
        Retrieve transport event by ID scoped to school.
        Prevents horizontal privilege escalation.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == event_id,
                self.model.school_id == school_id
            )
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Listing Methods
    # -----------------------------------------

    def list_by_school(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransportEvent]:
        """
        List all transport events within school tenant.
        Deterministic ordering: timestamp ASC, id ASC (sequence matters).
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(self.model.school_id == school_id)
            .order_by(
                self.model.timestamp.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_trip(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransportEvent]:
        """
        List transport events for a trip within school tenant.
        Deterministic ordering: timestamp ASC, id ASC (sequence matters).
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.trip_id == trip_id
            )
            .order_by(
                self.model.timestamp.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_trip_ordered(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID
    ) -> List[TransportEvent]:
        """
        List all transport events for a trip ordered by sequence.
        No pagination - returns all events for trip processing.
        Deterministic ordering: timestamp ASC, id ASC (sequence matters).
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.trip_id == trip_id
            )
            .order_by(
                self.model.timestamp.asc(),
                self.model.id.asc()
            )
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransportEvent]:
        """
        List transport events for a student within school tenant.
        Deterministic ordering: timestamp ASC, id ASC (sequence matters).
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id
            )
            .order_by(
                self.model.timestamp.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_event_type(
        self,
        db: Session,
        school_id: UUID,
        event_type: Any,  # TransportEventType enum
        skip: int = 0,
        limit: int = 100
    ) -> List[TransportEvent]:
        """
        List transport events by event type within school tenant.
        Uses index on event_type.
        Deterministic ordering: timestamp ASC, id ASC (sequence matters).
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.event_type == event_type
            )
            .order_by(
                self.model.timestamp.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_date_range(
        self,
        db: Session,
        school_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransportEvent]:
        """
        List transport events within datetime range.
        Index-friendly filtering on timestamp.
        Deterministic ordering: timestamp ASC, id ASC (sequence matters).
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.timestamp >= start_date,
                self.model.timestamp <= end_date
            )
            .order_by(
                self.model.timestamp.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_trip_and_event_type(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID,
        event_type: Any,  # TransportEventType enum
        skip: int = 0,
        limit: int = 100
    ) -> List[TransportEvent]:
        """
        List transport events for a trip filtered by event type.
        Deterministic ordering: timestamp ASC, id ASC (sequence matters).
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.trip_id == trip_id,
                self.model.event_type == event_type
            )
            .order_by(
                self.model.timestamp.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Row Locking
    # -----------------------------------------

    def lock_for_update(
        self,
        db: Session,
        school_id: UUID,
        event_id: UUID
    ) -> Optional[TransportEvent]:
        """
        Lock transport event for update.
        Scoped to school_id for tenant safety.
        NO soft-delete filter (immutable log).
        Note: Events are typically immutable, but lock provided for edge cases.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == event_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_events_by_trip_for_update(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID
    ) -> List[TransportEvent]:
        """
        Lock all events for a trip.
        Used for event sequence operations.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.trip_id == trip_id
            )
            .order_by(self.model.timestamp.asc(), self.model.id.asc())
            .with_for_update()
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Existence Checks
    # -----------------------------------------

    def exists_by_id(
        self,
        db: Session,
        school_id: UUID,
        event_id: UUID
    ) -> bool:
        """
        Efficient existence check for transport event by ID.
        NO soft-delete filter (immutable log).
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == event_id,
                self.model.school_id == school_id
            )
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    # -----------------------------------------
    # Aggregations (Null-Safe)
    # -----------------------------------------

    def count_by_school(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count transport events within school.
        Null-safe aggregation.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.school_id == school_id)
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_trip(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID
    ) -> int:
        """
        Count transport events for a trip within school.
        Null-safe aggregation.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.trip_id == trip_id
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID
    ) -> int:
        """
        Count transport events for a student within school.
        Null-safe aggregation.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_event_type(
        self,
        db: Session,
        school_id: UUID,
        event_type: Any  # TransportEventType enum
    ) -> int:
        """
        Count transport events by event type within school.
        Null-safe aggregation.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.event_type == event_type
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_trip_and_event_type(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID,
        event_type: Any  # TransportEventType enum
    ) -> int:
        """
        Count transport events for a trip by event type.
        Null-safe aggregation.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.trip_id == trip_id,
                self.model.event_type == event_type
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # Insert-Safe Reads
    # -----------------------------------------

    def get_latest_event_by_trip(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID
    ) -> Optional[TransportEvent]:
        """
        Get the latest event for a trip.
        Used for insert-safe reads before appending new events.
        Deterministic ordering: timestamp DESC, id DESC.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.trip_id == trip_id
            )
            .order_by(
                self.model.timestamp.desc(),
                self.model.id.desc()
            )
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_latest_event_by_trip_and_type(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID,
        event_type: Any  # TransportEventType enum
    ) -> Optional[TransportEvent]:
        """
        Get the latest event for a trip filtered by event type.
        Used for insert-safe reads before appending new events.
        Deterministic ordering: timestamp DESC, id DESC.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.trip_id == trip_id,
                self.model.event_type == event_type
            )
            .order_by(
                self.model.timestamp.desc(),
                self.model.id.desc()
            )
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()
    

    def lock_latest_event_by_trip_for_update(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID
    ) -> Optional[TransportEvent]:

        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.trip_id == trip_id
            )
            .order_by(
                self.model.timestamp.desc(),
                self.model.id.desc()
            )
            .limit(1)
            .with_for_update()
        )

        result = db.execute(stmt)
        return result.scalar_one_or_none()
    

    def list_latest_by_trip(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID,
        limit: int = 50
    ) -> List[TransportEvent]:

        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.trip_id == trip_id
            )
            .order_by(
                self.model.timestamp.desc(),
                self.model.id.desc()
            )
            .limit(limit)
        )

        result = db.execute(stmt)
        return list(result.scalars().all())
    

    def list_latest_by_trip(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID,
        limit: int = 50
    ) -> List[TransportEvent]:

        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.trip_id == trip_id
            )
            .order_by(
                self.model.timestamp.desc(),
                self.model.id.desc()
            )
            .limit(limit)
        )

        result = db.execute(stmt)
        return list(result.scalars().all())