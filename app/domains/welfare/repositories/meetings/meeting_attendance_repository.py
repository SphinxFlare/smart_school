# welfare/repositories/meetings/meeting_attendance_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update, delete

from repositories.base import BaseRepository
from welfare.models.meetings import MeetingAttendance


class MeetingAttendanceRepository(BaseRepository[MeetingAttendance]):
    """
    Repository for MeetingAttendance model operations.
    Extends BaseRepository - model does NOT contain school_id.
    Tenant isolation enforced through meeting_id/participant_id scoping at service layer.
    NO soft-delete filtering (model lacks is_deleted).
    Zero business logic, zero validation, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(MeetingAttendance)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        attendance_id: UUID
    ) -> Optional[MeetingAttendance]:
        """
        Retrieve attendance record by ID.
        NO soft-delete filter (model lacks is_deleted).
        """
        stmt = (
            select(self.model)
            .where(self.model.id == attendance_id)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_id_meeting_scoped(
        self,
        db: Session,
        attendance_id: UUID,
        meeting_id: UUID
    ) -> Optional[MeetingAttendance]:
        """
        Retrieve attendance record by ID scoped to meeting.
        Prevents unauthorized access across meetings.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == attendance_id,
                self.model.meeting_id == meeting_id
            )
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_meeting_and_participant(
        self,
        db: Session,
        meeting_id: UUID,
        participant_id: UUID
    ) -> Optional[MeetingAttendance]:
        """
        Retrieve attendance record by meeting and participant.
        Respects unique constraint (meeting_id, participant_id).
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.meeting_id == meeting_id,
                self.model.participant_id == participant_id
            )
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Listing Methods
    # -----------------------------------------

    def list_by_meeting(
        self,
        db: Session,
        meeting_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[MeetingAttendance]:
        """
        List attendance records for a meeting.
        Deterministic ordering: check_in_time ASC, id ASC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.meeting_id == meeting_id)
            .order_by(
                self.model.check_in_time.asc().nulls_last(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_participant(
        self,
        db: Session,
        participant_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[MeetingAttendance]:
        """
        List attendance records for a participant across all meetings.
        Deterministic ordering: check_in_time DESC, id DESC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.participant_id == participant_id)
            .order_by(
                self.model.check_in_time.desc().nulls_last(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_with_check_in(
        self,
        db: Session,
        meeting_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[MeetingAttendance]:
        """
        List attendance records with check-in for a meeting.
        Deterministic ordering: check_in_time ASC, id ASC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.meeting_id == meeting_id,
                self.model.check_in_time.is_not(None)
            )
            .order_by(
                self.model.check_in_time.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_without_check_in(
        self,
        db: Session,
        meeting_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[MeetingAttendance]:
        """
        List attendance records without check-in for a meeting.
        Deterministic ordering: created_at DESC, id DESC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.meeting_id == meeting_id,
                self.model.check_in_time.is_(None)
            )
            .order_by(
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
        attendance_id: UUID
    ) -> Optional[MeetingAttendance]:
        """
        Lock attendance record for update.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.id == attendance_id)
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_for_update_meeting_scoped(
        self,
        db: Session,
        attendance_id: UUID,
        meeting_id: UUID
    ) -> Optional[MeetingAttendance]:
        """
        Lock attendance record for update scoped to meeting.
        Maximum concurrency safety for sensitive mutation.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == attendance_id,
                self.model.meeting_id == meeting_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_by_meeting_and_participant_for_update(
        self,
        db: Session,
        meeting_id: UUID,
        participant_id: UUID
    ) -> Optional[MeetingAttendance]:
        """
        Lock attendance record by meeting and participant for update.
        Respects unique constraint (meeting_id, participant_id).
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.meeting_id == meeting_id,
                self.model.participant_id == participant_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_all_by_meeting_for_update(
        self,
        db: Session,
        meeting_id: UUID
    ) -> List[MeetingAttendance]:
        """
        Lock all attendance records for a meeting.
        Used for batch operations.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.meeting_id == meeting_id)
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
        attendance_id: UUID
    ) -> bool:
        """
        Efficient existence check for attendance record by ID.
        NO soft-delete filter.
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(self.model.id == attendance_id)
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_by_meeting_and_participant(
        self,
        db: Session,
        meeting_id: UUID,
        participant_id: UUID,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for attendance record by meeting and participant.
        Respects unique constraint (meeting_id, participant_id).
        Optional exclude_id for update operations.
        NO soft-delete filter.
        Uses select(id).limit(1) pattern.
        """
        stmt = select(self.model.id).where(
            self.model.meeting_id == meeting_id,
            self.model.participant_id == participant_id
        )
        
        if exclude_id is not None:
            stmt = stmt.where(self.model.id != exclude_id)
        
        stmt = stmt.limit(1)
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    # -----------------------------------------
    # Aggregations (Null-Safe)
    # -----------------------------------------

    def count_by_meeting(
        self,
        db: Session,
        meeting_id: UUID
    ) -> int:
        """
        Count attendance records for a meeting.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.meeting_id == meeting_id)
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_participant(
        self,
        db: Session,
        participant_id: UUID
    ) -> int:
        """
        Count attendance records for a participant across all meetings.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.participant_id == participant_id)
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_with_check_in(
        self,
        db: Session,
        meeting_id: UUID
    ) -> int:
        """
        Count attendance records with check-in for a meeting.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.meeting_id == meeting_id,
                self.model.check_in_time.is_not(None)
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_without_check_in(
        self,
        db: Session,
        meeting_id: UUID
    ) -> int:
        """
        Count attendance records without check-in for a meeting.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.meeting_id == meeting_id,
                self.model.check_in_time.is_(None)
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def get_total_attendance_duration(
        self,
        db: Session,
        meeting_id: UUID
    ) -> int:
        """
        Get total attendance duration in minutes for a meeting.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.sum(self.model.attendance_duration_minutes))
            .where(self.model.meeting_id == meeting_id)
        )
        result = db.execute(stmt)
        value = result.scalar()
        return int(value) if value is not None else 0

    # -----------------------------------------
    # Bulk Operations (Atomic, Empty Guards)
    # -----------------------------------------

    def bulk_update_check_in(
        self,
        db: Session,
        attendance_ids: List[UUID],
        check_in_time: datetime
    ) -> int:
        """
        Bulk update check-in time for multiple attendance records.
        Atomic update statement.
        Empty-list guard included.
        Returns count of updated rows.
        NO soft-delete filter.
        """
        if not attendance_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.id.in_(attendance_ids)
            )
            .values(check_in_time=check_in_time)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_check_out(
        self,
        db: Session,
        attendance_ids: List[UUID],
        check_out_time: datetime
    ) -> int:
        """
        Bulk update check-out time for multiple attendance records.
        Atomic update statement.
        Empty-list guard included.
        Returns count of updated rows.
        NO soft-delete filter.
        """
        if not attendance_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.id.in_(attendance_ids)
            )
            .values(check_out_time=check_out_time)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_by_meeting(
        self,
        db: Session,
        meeting_id: UUID,
        updates: Dict[str, Any]
    ) -> int:
        """
        Bulk update attendance records for a meeting.
        Atomic update statement scoped by meeting_id.
        Empty-list guard included.
        Returns count of updated rows.
        NO soft-delete filter.
        """
        if not updates:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.meeting_id == meeting_id
            )
            .values(**updates)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_delete_by_meeting(
        self,
        db: Session,
        meeting_id: UUID
    ) -> int:
        """
        Bulk delete all attendance records for a meeting.
        Atomic delete statement scoped by meeting_id.
        Returns count of deleted rows.
        NO soft-delete filter (hard delete).
        """
        stmt = (
            delete(self.model)
            .where(self.model.meeting_id == meeting_id)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0