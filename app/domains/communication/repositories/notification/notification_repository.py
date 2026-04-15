# communication/repositories/notification/notification_repository.py


from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from repositories.base import BaseRepository, SchoolScopedRepository
from communication.models.notifications import (
    Notification,
    NotificationPreference,
    CommunicationLog
)


# ==========================================================
# Notification Repository
# ==========================================================

class NotificationRepository(BaseRepository[Notification]):
    """
    Repository for Notification model operations.
    User-scoped (extends BaseRepository), NOT school-scoped.
    All queries use SQLAlchemy 2.0 select() style with deterministic ordering.
    """

    def __init__(self):
        super().__init__(Notification)

    # -----------------------------------------
    # Notification Listing
    # -----------------------------------------

    def list_by_user(
        self,
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        List notifications per user ordered by sent_at DESC, id DESC.
        Uses index on user_id and sent_at.
        Pagination applied after ordering for stability.
        """
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(
                self.model.sent_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_unread_notifications(
        self,
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Filter unread notifications for a user.
        Uses index on is_read.
        Deterministic ordering: sent_at DESC, id DESC.
        Pagination applied after ordering.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
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

    def filter_by_notification_type(
        self,
        db: Session,
        user_id: UUID,
        notification_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Filter notifications by notification_type.
        Uses index on notification_type.
        Deterministic ordering: sent_at DESC, id DESC.
        Pagination applied after ordering.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
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

    def filter_active_notifications(
        self,
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Filter active (non-expired) notifications.
        Enforces: sent_at <= now AND (expires_at IS NULL OR expires_at > now).
        Prevents future-scheduled records from appearing.
        Deterministic ordering: sent_at DESC, id DESC.
        Pagination applied after ordering.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.sent_at <= now,
                (self.model.expires_at.is_(None)) | (self.model.expires_at > now)
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
    # Count Operations
    # -----------------------------------------

    def count_unread_notifications(
        self,
        db: Session,
        user_id: UUID
    ) -> int:
        """
        Count unread notifications efficiently using indexed fields only.
        Null-safe aggregation (scalar() or 0).
        No unnecessary joins.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.user_id == user_id,
                self.model.is_read.is_(False)
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # Read Status (Row Locking with Ownership Validation)
    # -----------------------------------------

    def mark_as_read(
        self,
        db: Session,
        notification_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Mark single notification as read using row locking.
        Strict ownership validation: scopes with_for_update() to both notification_id AND user_id.
        Prevents cross-user mutation.
        Updates is_read and read_at atomically.
        Flushes without committing.
        Returns True if successful.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.id == notification_id,
                self.model.user_id == user_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        notification = result.scalar_one_or_none()

        if notification:
            notification.is_read = True
            notification.read_at = now
            db.flush()
            return True
        return False

    def bulk_mark_as_read(
        self,
        db: Session,
        user_id: UUID,
        notification_ids: List[UUID]
    ) -> int:
        """
        Bulk mark notifications as read for a user.
        Single update() statement filtered by user_id, id.in_(notification_ids), is_read=False.
        Updates both is_read and read_at atomically.
        Returns rowcount or 0.
        Idempotent and safe under concurrent calls.
        """
        now = datetime.utcnow()
        stmt = (
            update(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.id.in_(notification_ids),
                self.model.is_read.is_(False)
            )
            .values(is_read=True, read_at=now)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0


# ==========================================================
# Notification Preference Repository
# ==========================================================

class NotificationPreferenceRepository(BaseRepository[NotificationPreference]):
    """
    Repository for NotificationPreference model operations.
    User-scoped (extends BaseRepository).
    Enforces one-row-per-user integrity via unique user_id constraint.
    """

    def __init__(self):
        super().__init__(NotificationPreference)

    # -----------------------------------------
    # User Preference Retrieval
    # -----------------------------------------

    def get_by_user(
        self,
        db: Session,
        user_id: UUID
    ) -> Optional[NotificationPreference]:
        """
        Get notification preferences by user.
        Uses unique constraint on user_id.
        Returns scalar_one_or_none() for single-row integrity.
        """
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Row Locking for Updates
    # -----------------------------------------

    def lock_for_update(
        self,
        db: Session,
        user_id: UUID
    ) -> Optional[NotificationPreference]:
        """
        Lock for update when modifying preferences.
        Uses with_for_update() scoped to user_id.
        Prevents concurrent preference modifications.
        """
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Safe Update Operations
    # -----------------------------------------

    def update_preferences(
        self,
        db: Session,
        user_id: UUID,
        preferences: dict
    ) -> Optional[NotificationPreference]:
        """
        Safe update operations without business logic.
        Locks row first, validates attribute existence with hasattr before assignment.
        Avoids silent attribute injection.
        Flushes changes safely.
        Returns updated entity or None if not found.
        """
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .with_for_update()
        )
        result = db.execute(stmt)
        preference = result.scalar_one_or_none()

        if preference:
            for key, value in preferences.items():
                if hasattr(preference, key):
                    setattr(preference, key, value)
                # Silent skip for invalid attributes - no injection
            db.flush()
            return preference
        return None


# ==========================================================
# Communication Log Repository
# ==========================================================

class CommunicationLogRepository(SchoolScopedRepository[CommunicationLog]):
    """
    Repository for CommunicationLog model operations.
    School-scoped (extends SchoolScopedRepository) because model includes school_id.
    NOTE: CommunicationLog model does NOT have is_deleted, so NO soft-delete filtering.
    All queries use SQLAlchemy 2.0 select() style with deterministic ordering.
    """

    def __init__(self):
        super().__init__(CommunicationLog)

    # -----------------------------------------
    # Log Listing
    # -----------------------------------------

    def list_by_school(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[CommunicationLog]:
        """
        List logs by school ordered by created_at DESC, id DESC.
        Uses index on school_id and created_at.
        Pagination applied after ordering for stability.
        NO soft-delete filter (model lacks is_deleted).
        """
        stmt = (
            select(self.model)
            .where(self.model.school_id == school_id)
            .order_by(
                self.model.created_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        # NO soft-delete filter (model lacks is_deleted)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def filter_by_communication_type(
        self,
        db: Session,
        school_id: UUID,
        communication_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[CommunicationLog]:
        """
        Filter logs by communication_type.
        Uses index on communication_type.
        Deterministic ordering: created_at DESC, id DESC.
        Pagination applied after ordering.
        NO soft-delete filter (model lacks is_deleted).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.communication_type == communication_type
            )
            .order_by(
                self.model.created_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def filter_by_status(
        self,
        db: Session,
        school_id: UUID,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[CommunicationLog]:
        """
        Filter logs by status.
        Uses index on status.
        Deterministic ordering: created_at DESC, id DESC.
        Pagination applied after ordering.
        NO soft-delete filter (model lacks is_deleted).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.status == status
            )
            .order_by(
                self.model.created_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def filter_by_channel(
        self,
        db: Session,
        school_id: UUID,
        channel: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[CommunicationLog]:
        """
        Filter logs by channel.
        Deterministic ordering: created_at DESC, id DESC.
        Pagination applied after ordering.
        NO soft-delete filter (model lacks is_deleted).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.channel == channel
            )
            .order_by(
                self.model.created_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def filter_by_date_range(
        self,
        db: Session,
        school_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[CommunicationLog]:
        """
        Date-range filtering preserving index usage on created_at.
        No functions on indexed columns.
        Deterministic ordering: created_at DESC, id DESC.
        Pagination applied after ordering.
        NO soft-delete filter (model lacks is_deleted).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.created_at >= start_date,
                self.model.created_at <= end_date
            )
            .order_by(
                self.model.created_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_by_entity_reference(
        self,
        db: Session,
        school_id: UUID,
        entity_type: str,
        entity_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[CommunicationLog]:
        """
        Retrieve logs by entity reference.
        Deterministic ordering: created_at DESC, id DESC.
        Pagination applied after ordering.
        NO soft-delete filter (model lacks is_deleted).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.entity_type == entity_type,
                self.model.entity_id == entity_id
            )
            .order_by(
                self.model.created_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Aggregation (Null-Safe)
    # -----------------------------------------

    def count_by_status(
        self,
        db: Session,
        school_id: UUID
    ) -> Dict[str, int]:
        """
        Count by status grouped safely.
        Filters by school_id.
        Excludes null status values at SQL level.
        Returns dict of {status: count} with null-safe counts.
        No business logic, pure aggregation.
        """
        stmt = (
            select(self.model.status, func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.status.is_not(None)
            )
            .group_by(self.model.status)
        )
        result = db.execute(stmt)
        counts: Dict[str, int] = {}
        for row in result.all():
            status = row[0]
            count = row[1] or 0
            if status:
                counts[status] = count
        return counts