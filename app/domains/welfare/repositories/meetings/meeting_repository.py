# welfare/repositories/meetings/meeting_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from repositories.base import SchoolScopedRepository
from welfare.models.meetings import Meeting


class MeetingRepository(SchoolScopedRepository[Meeting]):
    """
    Repository for Meeting model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    Soft-delete aware (Meeting model has is_deleted).
    Zero business logic, zero validation, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(Meeting)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        school_id: UUID,
        meeting_id: UUID
    ) -> Optional[Meeting]:
        """
        Retrieve meeting by ID scoped to school.
        Prevents horizontal privilege escalation.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == meeting_id,
                self.model.school_id == school_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Listing Methods
    # -----------------------------------------

    def list_meetings_by_school(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Meeting]:
        """
        List all meetings within school tenant.
        Deterministic ordering: scheduled_at DESC, id DESC.
        Soft-delete filtered (excludes deleted).
        """
        stmt = (
            select(self.model)
            .where(self.model.school_id == school_id)
            .order_by(
                self.model.scheduled_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_status(
        self,
        db: Session,
        school_id: UUID,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Meeting]:
        """
        List meetings by status within school tenant.
        Uses index on status.
        Deterministic ordering: scheduled_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.status == status
            )
            .order_by(
                self.model.scheduled_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_meeting_type(
        self,
        db: Session,
        school_id: UUID,
        meeting_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Meeting]:
        """
        List meetings by type within school tenant.
        Deterministic ordering: scheduled_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.meeting_type == meeting_type
            )
            .order_by(
                self.model.scheduled_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_creator(
        self,
        db: Session,
        school_id: UUID,
        created_by_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Meeting]:
        """
        List meetings by creator within school tenant.
        Uses index on created_by_id.
        Deterministic ordering: scheduled_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.created_by_id == created_by_id
            )
            .order_by(
                self.model.scheduled_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
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
    ) -> List[Meeting]:
        """
        List meetings within date range.
        Index-friendly filtering on scheduled_at.
        Deterministic ordering: scheduled_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.scheduled_at >= start_date,
                self.model.scheduled_at <= end_date
            )
            .order_by(
                self.model.scheduled_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_upcoming_meetings(
        self,
        db: Session,
        school_id: UUID,
        reference_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[Meeting]:
        """
        List upcoming meetings (scheduled_at >= reference_date).
        Deterministic ordering: scheduled_at ASC, id ASC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.scheduled_at >= reference_date
            )
            .order_by(
                self.model.scheduled_at.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_deleted(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Meeting]:
        """
        List soft-deleted meetings within school tenant.
        Does NOT apply soft-delete filter (explicitly includes deleted).
        Deterministic ordering: scheduled_at DESC, id DESC.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
            .order_by(
                self.model.scheduled_at.desc(),
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
        meeting_id: UUID
    ) -> Optional[Meeting]:
        """
        Lock meeting for update.
        Scoped to school_id for tenant safety.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == meeting_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_for_status_update(
        self,
        db: Session,
        school_id: UUID,
        meeting_id: UUID
    ) -> Optional[Meeting]:
        """
        Lock meeting for status update operations.
        Maximum concurrency safety for sensitive mutation.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == meeting_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_by_creator_for_update(
        self,
        db: Session,
        school_id: UUID,
        created_by_id: UUID
    ) -> List[Meeting]:
        """
        Lock all meetings by a creator.
        Used for batch operations.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.created_by_id == created_by_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Existence Checks
    # -----------------------------------------

    def exists_by_id(
        self,
        db: Session,
        school_id: UUID,
        meeting_id: UUID
    ) -> bool:
        """
        Efficient existence check for meeting by ID.
        Soft-delete filtered.
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == meeting_id,
                self.model.school_id == school_id
            )
            .limit(1)
        )
        stmt = self._apply_soft_delete_filter(stmt)
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
        Count meetings within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.school_id == school_id)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_status(
        self,
        db: Session,
        school_id: UUID,
        status: str
    ) -> int:
        """
        Count meetings by status within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.status == status
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_meeting_type(
        self,
        db: Session,
        school_id: UUID,
        meeting_type: str
    ) -> int:
        """
        Count meetings by type within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.meeting_type == meeting_type
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_creator(
        self,
        db: Session,
        school_id: UUID,
        created_by_id: UUID
    ) -> int:
        """
        Count meetings by creator within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.created_by_id == created_by_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_deleted(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count soft-deleted meetings within school.
        Null-safe aggregation.
        Does NOT apply soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # Soft Delete Operations
    # -----------------------------------------

    def soft_delete(
        self,
        db: Session,
        school_id: UUID,
        meeting_id: UUID
    ) -> bool:
        """
        Soft delete meeting record.
        Scoped to school_id for tenant safety.
        Returns True if successful.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.id == meeting_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        meeting = result.scalar_one_or_none()

        if meeting:
            meeting.is_deleted = True
            meeting.deleted_at = now
            db.flush()
            return True
        return False

    def restore(
        self,
        db: Session,
        school_id: UUID,
        meeting_id: UUID
    ) -> bool:
        """
        Restore soft-deleted meeting record.
        Scoped to school_id.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == meeting_id,
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        meeting = result.scalar_one_or_none()

        if meeting:
            meeting.is_deleted = False
            meeting.deleted_at = None
            db.flush()
            return True
        return False

    # -----------------------------------------
    # Bulk Operations (Atomic, Empty Guards)
    # -----------------------------------------

    def bulk_update_status(
        self,
        db: Session,
        school_id: UUID,
        meeting_ids: List[UUID],
        new_status: str
    ) -> int:
        """
        Bulk update status for multiple meetings.
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not meeting_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(meeting_ids),
                self.model.is_deleted.is_(False)
            )
            .values(status=new_status)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_by_creator(
        self,
        db: Session,
        school_id: UUID,
        created_by_id: UUID,
        updates: Dict[str, Any]
    ) -> int:
        """
        Bulk update meetings for a creator.
        Atomic update statement scoped by school_id and created_by_id.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not updates:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.created_by_id == created_by_id,
                self.model.is_deleted.is_(False)
            )
            .values(**updates)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_soft_delete_by_creator(
        self,
        db: Session,
        school_id: UUID,
        created_by_id: UUID
    ) -> int:
        """
        Bulk soft delete all meetings for a creator.
        Atomic update statement scoped by school_id.
        Returns count of updated rows.
        """
        now = datetime.utcnow()
        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.created_by_id == created_by_id,
                self.model.is_deleted.is_(False)
            )
            .values(is_deleted=True, deleted_at=now)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_restore_by_creator(
        self,
        db: Session,
        school_id: UUID,
        created_by_id: UUID
    ) -> int:
        """
        Bulk restore all soft-deleted meetings for a creator.
        Atomic update statement scoped by school_id.
        Returns count of updated rows.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.created_by_id == created_by_id,
                self.model.is_deleted.is_(True)
            )
            .values(is_deleted=False, deleted_at=None)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0