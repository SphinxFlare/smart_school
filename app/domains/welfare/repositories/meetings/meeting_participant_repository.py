# welfare/repositories/meetings/meeting_participant_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from repositories.base import BaseRepository
from welfare.models.meetings import MeetingParticipant


class MeetingParticipantRepository(BaseRepository[MeetingParticipant]):
    """
    Repository for MeetingParticipant model operations.
    Extends BaseRepository - model does NOT contain school_id.
    Tenant isolation enforced through meeting_id scoping at service layer.
    NO soft-delete filtering (model lacks is_deleted).
    Zero business logic, zero validation, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(MeetingParticipant)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        participant_id: UUID
    ) -> Optional[MeetingParticipant]:
        """
        Retrieve participant by ID.
        NO soft-delete filter (model lacks is_deleted).
        """
        stmt = (
            select(self.model)
            .where(self.model.id == participant_id)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_id_meeting_scoped(
        self,
        db: Session,
        participant_id: UUID,
        meeting_id: UUID
    ) -> Optional[MeetingParticipant]:
        """
        Retrieve participant by ID scoped to meeting.
        Prevents unauthorized access across meetings.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == participant_id,
                self.model.meeting_id == meeting_id
            )
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_meeting_and_user(
        self,
        db: Session,
        meeting_id: UUID,
        user_id: UUID
    ) -> Optional[MeetingParticipant]:
        """
        Retrieve participant by meeting and user.
        Respects unique constraint (meeting_id, user_id).
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.meeting_id == meeting_id,
                self.model.user_id == user_id
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
    ) -> List[MeetingParticipant]:
        """
        List participants for a meeting.
        Deterministic ordering: invited_at DESC, id DESC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.meeting_id == meeting_id)
            .order_by(
                self.model.invited_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_user(
        self,
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[MeetingParticipant]:
        """
        List participants for a user across all meetings.
        Deterministic ordering: invited_at DESC, id DESC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(
                self.model.invited_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_invitation_status(
        self,
        db: Session,
        meeting_id: UUID,
        invitation_status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[MeetingParticipant]:
        """
        List participants by invitation status for a meeting.
        Deterministic ordering: invited_at DESC, id DESC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.meeting_id == meeting_id,
                self.model.invitation_status == invitation_status
            )
            .order_by(
                self.model.invited_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_attendance_status(
        self,
        db: Session,
        meeting_id: UUID,
        attendance_status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[MeetingParticipant]:
        """
        List participants by attendance status for a meeting.
        Deterministic ordering: invited_at DESC, id DESC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.meeting_id == meeting_id,
                self.model.attendance_status == attendance_status
            )
            .order_by(
                self.model.invited_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_pending_invitations(
        self,
        db: Session,
        meeting_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[MeetingParticipant]:
        """
        List participants with pending invitations for a meeting.
        Deterministic ordering: invited_at ASC, id ASC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.meeting_id == meeting_id,
                self.model.invitation_status == 'pending'
            )
            .order_by(
                self.model.invited_at.asc(),
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
        participant_id: UUID
    ) -> Optional[MeetingParticipant]:
        """
        Lock participant for update.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.id == participant_id)
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_for_update_meeting_scoped(
        self,
        db: Session,
        participant_id: UUID,
        meeting_id: UUID
    ) -> Optional[MeetingParticipant]:
        """
        Lock participant for update scoped to meeting.
        Maximum concurrency safety for sensitive mutation.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == participant_id,
                self.model.meeting_id == meeting_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_by_meeting_and_user_for_update(
        self,
        db: Session,
        meeting_id: UUID,
        user_id: UUID
    ) -> Optional[MeetingParticipant]:
        """
        Lock participant by meeting and user for update.
        Respects unique constraint (meeting_id, user_id).
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.meeting_id == meeting_id,
                self.model.user_id == user_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_all_by_meeting_for_update(
        self,
        db: Session,
        meeting_id: UUID
    ) -> List[MeetingParticipant]:
        """
        Lock all participants for a meeting.
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
        participant_id: UUID
    ) -> bool:
        """
        Efficient existence check for participant by ID.
        NO soft-delete filter.
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(self.model.id == participant_id)
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_by_meeting_and_user(
        self,
        db: Session,
        meeting_id: UUID,
        user_id: UUID,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for participant by meeting and user.
        Respects unique constraint (meeting_id, user_id).
        Optional exclude_id for update operations.
        NO soft-delete filter.
        Uses select(id).limit(1) pattern.
        """
        stmt = select(self.model.id).where(
            self.model.meeting_id == meeting_id,
            self.model.user_id == user_id
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
        Count participants for a meeting.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.meeting_id == meeting_id)
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_user(
        self,
        db: Session,
        user_id: UUID
    ) -> int:
        """
        Count participants for a user across all meetings.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.user_id == user_id)
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_invitation_status(
        self,
        db: Session,
        meeting_id: UUID,
        invitation_status: str
    ) -> int:
        """
        Count participants by invitation status for a meeting.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.meeting_id == meeting_id,
                self.model.invitation_status == invitation_status
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_attendance_status(
        self,
        db: Session,
        meeting_id: UUID,
        attendance_status: str
    ) -> int:
        """
        Count participants by attendance status for a meeting.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.meeting_id == meeting_id,
                self.model.attendance_status == attendance_status
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_invitation_status_pending(
        self,
        db: Session,
        meeting_id: UUID,
        invitation_status: str
    ) -> int:
        """
        Count pending invitations for a meeting.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.meeting_id == meeting_id,
                self.model.invitation_status == invitation_status
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # Bulk Operations (Atomic, Empty Guards)
    # -----------------------------------------

    def bulk_update_invitation_status(
        self,
        db: Session,
        participant_ids: List[UUID],
        invitation_status: str
    ) -> int:
        """
        Bulk update invitation status for multiple participants.
        Atomic update statement.
        Empty-list guard included.
        Returns count of updated rows.
        NO soft-delete filter.
        """
        if not participant_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.id.in_(participant_ids)
            )
            .values(invitation_status=invitation_status)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_attendance_status(
        self,
        db: Session,
        participant_ids: List[UUID],
        attendance_status: str
    ) -> int:
        """
        Bulk update attendance status for multiple participants.
        Atomic update statement.
        Empty-list guard included.
        Returns count of updated rows.
        NO soft-delete filter.
        """
        if not participant_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.id.in_(participant_ids)
            )
            .values(attendance_status=attendance_status)
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
        Bulk update participants for a meeting.
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

    def bulk_set_attendance_status(
        self,
        db: Session,
        participant_ids: List[UUID],
        attendance_confirmed_at: datetime,
        attendance_status: str
    ) -> int:
        """
        Bulk confirm attendance for multiple participants.
        Atomic update statement.
        Empty-list guard included.
        Returns count of updated rows.
        NO soft-delete filter.
        """
        if not participant_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.id.in_(participant_ids)
            )
            .values(
                attendance_status=attendance_status,
                attendance_confirmed_at=attendance_confirmed_at
            )
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0