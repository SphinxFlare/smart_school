# transport/repositories/tracking/transport_notification_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from repositories.base import SchoolScopedRepository
from transport.models.tracking import TransportNotification


class TransportNotificationRepository(SchoolScopedRepository[TransportNotification]):
    """
    Repository for TransportNotification model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    NOTE: TransportNotification model does NOT have is_deleted - immutable log.
    NO soft-delete filtering applied.
    Zero business logic, zero notification validation, zero authorization decisions.
    Append-only log table - limited status updates for delivery/read flags only.
    """

    def __init__(self):
        super().__init__(TransportNotification)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        school_id: UUID,
        notification_id: UUID
    ) -> Optional[TransportNotification]:
        """
        Retrieve transport notification by ID scoped to school.
        Prevents horizontal privilege escalation.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == notification_id,
                self.model.school_id == school_id
            )
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()
    

    def get_latest_by_parent(
        self,
        db: Session,
        school_id: UUID,
        parent_id: UUID
    ) -> Optional[TransportNotification]:

        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.parent_id == parent_id
            )
            .order_by(
                self.model.sent_at.desc(),
                self.model.id.desc()
            )
            .limit(1)
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
    ) -> List[TransportNotification]:
        """
        List all transport notifications within school tenant.
        Deterministic ordering: sent_at DESC, id DESC.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(self.model.school_id == school_id)
            .order_by(
                self.model.sent_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
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
    ) -> List[TransportNotification]:
        """
        List transport notifications for a student within school tenant.
        Deterministic ordering: sent_at DESC, id DESC.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id
            )
            .order_by(
                self.model.sent_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_parent(
        self,
        db: Session,
        school_id: UUID,
        parent_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransportNotification]:
        """
        List transport notifications for a parent within school tenant.
        Deterministic ordering: sent_at DESC, id DESC.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.parent_id == parent_id
            )
            .order_by(
                self.model.sent_at.desc(),
                self.model.id.desc()
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
    ) -> List[TransportNotification]:
        """
        List transport notifications for a trip within school tenant.
        Deterministic ordering: sent_at DESC, id DESC.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.trip_id == trip_id
            )
            .order_by(
                self.model.sent_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_notification_type(
        self,
        db: Session,
        school_id: UUID,
        notification_type: Any,  # TransportNotificationType enum
        skip: int = 0,
        limit: int = 100
    ) -> List[TransportNotification]:
        """
        List transport notifications by type within school tenant.
        Deterministic ordering: sent_at DESC, id DESC.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.notification_type == notification_type
            )
            .order_by(
                self.model.sent_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_undelivered(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransportNotification]:
        """
        List undelivered transport notifications within school tenant.
        Deterministic ordering: sent_at DESC, id DESC.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.is_delivered.is_(False)
            )
            .order_by(
                self.model.sent_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_unread(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransportNotification]:
        """
        List unread transport notifications within school tenant.
        Deterministic ordering: sent_at DESC, id DESC.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.is_read.is_(False)
            )
            .order_by(
                self.model.sent_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_unread_by_parent(
        self,
        db: Session,
        school_id: UUID,
        parent_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransportNotification]:
        """
        List unread transport notifications for a parent.
        Deterministic ordering: sent_at DESC, id DESC.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.parent_id == parent_id,
                self.model.is_read.is_(False)
            )
            .order_by(
                self.model.sent_at.desc(),
                self.model.id.desc()
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
        notification_id: UUID
    ) -> Optional[TransportNotification]:
        """
        Lock transport notification for update.
        Scoped to school_id for tenant safety.
        NO soft-delete filter (immutable log).
        Used for delivery/read status updates.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == notification_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_by_student_for_update(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID
    ) -> List[TransportNotification]:
        """
        Lock all notifications for a student.
        Used for marking delivered/read operations.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id
            )
            .order_by(
            self.model.sent_at.asc(),
            self.model.id.asc()
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def lock_by_parent_for_update(
        self,
        db: Session,
        school_id: UUID,
        parent_id: UUID
    ) -> List[TransportNotification]:
        """
        Lock all notifications for a parent.
        Used for marking delivered/read operations.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.parent_id == parent_id
            )
            .order_by(
            self.model.sent_at.asc(),
            self.model.id.asc()
        )
            .with_for_update()
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def lock_undelivered_by_trip_for_update(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID
    ) -> List[TransportNotification]:
        """
        Lock all undelivered notifications for a trip.
        Used for batch delivery operations.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.trip_id == trip_id,
                self.model.is_delivered.is_(False)
            )
            .order_by(
            self.model.sent_at.asc(),
            self.model.id.asc()
        )
            .with_for_update()
        )
        result = db.execute(stmt)
        return list(result.scalars().all())
    

    def lock_by_trip_for_update(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID
    ) -> List[TransportNotification]:

        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.trip_id == trip_id
            )
            .order_by(
                self.model.sent_at.asc(),
                self.model.id.asc()
            )
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
        notification_id: UUID
    ) -> bool:
        """
        Efficient existence check for transport notification by ID.
        NO soft-delete filter (immutable log).
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == notification_id,
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
        Count transport notifications within school.
        Null-safe aggregation.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.school_id == school_id)
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
        Count transport notifications for a student within school.
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

    def count_by_parent(
        self,
        db: Session,
        school_id: UUID,
        parent_id: UUID
    ) -> int:
        """
        Count transport notifications for a parent within school.
        Null-safe aggregation.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.parent_id == parent_id
            )
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
        Count transport notifications for a trip within school.
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

    def count_undelivered(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count undelivered transport notifications within school.
        Null-safe aggregation.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.is_delivered.is_(False)
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_unread(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count unread transport notifications within school.
        Null-safe aggregation.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.is_read.is_(False)
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_unread_by_parent(
        self,
        db: Session,
        school_id: UUID,
        parent_id: UUID
    ) -> int:
        """
        Count unread transport notifications for a parent.
        Null-safe aggregation.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.parent_id == parent_id,
                self.model.is_read.is_(False)
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # Status Updates (Delivery/Read Flags Only)
    # -----------------------------------------

    def mark_as_delivered(
        self,
        db: Session,
        school_id: UUID,
        notification_id: UUID,
        delivered_at: datetime
    ) -> bool:
        """
        Mark notification as delivered.
        Used for delivery confirmation workflow.
        Returns True if successful.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            update(self.model)
            .where(
                self.model.id == notification_id,
                self.model.school_id == school_id
            )
            .values(
                is_delivered=True,
                delivered_at=delivered_at
            )
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount > 0

    def mark_as_read(
        self,
        db: Session,
        school_id: UUID,
        notification_id: UUID,
        read_at: datetime
    ) -> bool:
        """
        Mark notification as read.
        Used for read confirmation workflow.
        Returns True if successful.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            update(self.model)
            .where(
                self.model.id == notification_id,
                self.model.school_id == school_id
            )
            .values(
                is_read=True,
                read_at=read_at
            )
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount > 0

    def bulk_mark_as_delivered(
        self,
        db: Session,
        school_id: UUID,
        notification_ids: List[UUID],
        delivered_at: datetime
    ) -> int:
        """
        Bulk mark notifications as delivered.
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Returns count of updated rows.
        NO soft-delete filter (immutable log).
        """
        if not notification_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(notification_ids),
                self.model.is_delivered.is_(False)
            )
            .values(
                is_delivered=True,
                delivered_at=delivered_at
            )
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_mark_as_read(
        self,
        db: Session,
        school_id: UUID,
        notification_ids: List[UUID],
        read_at: datetime
    ) -> int:
        """
        Bulk mark notifications as read.
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Returns count of updated rows.
        NO soft-delete filter (immutable log).
        """
        if not notification_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(notification_ids),
                self.model.is_read.is_(False)
            )
            .values(
                is_read=True,
                read_at=read_at
            )
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_mark_as_read_by_parent(
        self,
        db: Session,
        school_id: UUID,
        parent_id: UUID,
        read_at: datetime
    ) -> int:
        """
        Bulk mark all unread notifications for a parent as read.
        Atomic update statement scoped by school_id and parent_id.
        Returns count of updated rows.
        NO soft-delete filter (immutable log).
        """
        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.parent_id == parent_id,
                self.model.is_read.is_(False)
            )
            .values(
                is_read=True,
                read_at=read_at
            )
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0