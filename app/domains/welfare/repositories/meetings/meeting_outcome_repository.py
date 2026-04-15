# welfare/repositories/meetings/meeting_outcome_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update, delete

from repositories.base import BaseRepository
from welfare.models.meetings import MeetingOutcome


class MeetingOutcomeRepository(BaseRepository[MeetingOutcome]):
    """
    Repository for MeetingOutcome model operations.
    Extends BaseRepository - model does NOT contain school_id.
    Tenant isolation enforced through meeting_id scoping at service layer.
    NO soft-delete filtering (model lacks is_deleted).
    Zero business logic, zero validation, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(MeetingOutcome)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        outcome_id: UUID
    ) -> Optional[MeetingOutcome]:
        """
        Retrieve outcome by ID.
        NO soft-delete filter (model lacks is_deleted).
        """
        stmt = (
            select(self.model)
            .where(self.model.id == outcome_id)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_id_meeting_scoped(
        self,
        db: Session,
        outcome_id: UUID,
        meeting_id: UUID
    ) -> Optional[MeetingOutcome]:
        """
        Retrieve outcome by ID scoped to meeting.
        Prevents unauthorized access across meetings.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == outcome_id,
                self.model.meeting_id == meeting_id
            )
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_one_by_meeting(
        self,
        db: Session,
        meeting_id: UUID
    ) -> Optional[MeetingOutcome]:
        """
        Retrieve outcome for a meeting (typically one per meeting).
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.meeting_id == meeting_id)
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
    ) -> List[MeetingOutcome]:
        """
        List outcomes for a meeting.
        Deterministic ordering: recorded_at DESC, id DESC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.meeting_id == meeting_id)
            .order_by(
                self.model.recorded_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_recorder(
        self,
        db: Session,
        recorded_by_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[MeetingOutcome]:
        """
        List outcomes recorded by a user.
        Deterministic ordering: recorded_at DESC, id DESC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.recorded_by_id == recorded_by_id)
            .order_by(
                self.model.recorded_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_requiring_follow_up(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[MeetingOutcome]:
        """
        List outcomes requiring follow-up.
        Deterministic ordering: follow_up_date ASC, id ASC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.follow_up_required.is_(True),
                self.model.follow_up_date.is_not(None)
            )
            .order_by(
                self.model.follow_up_date.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_upcoming_follow_ups(
        self,
        db: Session,
        reference_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[MeetingOutcome]:
        """
        List outcomes with upcoming follow-ups.
        follow_up_date >= reference_date and follow_up_required = True.
        Deterministic ordering: follow_up_date ASC, id ASC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.follow_up_required.is_(True),
                self.model.follow_up_date >= reference_date,
                self.model.follow_up_date.is_not(None)
            )
            .order_by(
                self.model.follow_up_date.asc(),
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
        outcome_id: UUID
    ) -> Optional[MeetingOutcome]:
        """
        Lock outcome for update.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.id == outcome_id)
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_for_update_meeting_scoped(
        self,
        db: Session,
        outcome_id: UUID,
        meeting_id: UUID
    ) -> Optional[MeetingOutcome]:
        """
        Lock outcome for update scoped to meeting.
        Maximum concurrency safety for sensitive mutation.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == outcome_id,
                self.model.meeting_id == meeting_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_by_meeting_for_update(
        self,
        db: Session,
        meeting_id: UUID
    ) -> Optional[MeetingOutcome]:
        """
        Lock outcome by meeting for update.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.meeting_id == meeting_id)
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_follow_up_for_update(
        self,
        db: Session,
        outcome_id: UUID
    ) -> Optional[MeetingOutcome]:
        """
        Lock outcome for follow-up update operations.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == outcome_id,
                self.model.follow_up_required.is_(True)
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Existence Checks
    # -----------------------------------------

    def exists_by_id(
        self,
        db: Session,
        outcome_id: UUID
    ) -> bool:
        """
        Efficient existence check for outcome by ID.
        NO soft-delete filter.
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(self.model.id == outcome_id)
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_by_meeting(
        self,
        db: Session,
        meeting_id: UUID
    ) -> bool:
        """
        Existence check for outcome by meeting.
        NO soft-delete filter.
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(self.model.meeting_id == meeting_id)
            .limit(1)
        )
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
        Count outcomes for a meeting.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.meeting_id == meeting_id)
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_recorder(
        self,
        db: Session,
        recorded_by_id: UUID
    ) -> int:
        """
        Count outcomes recorded by a user.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.recorded_by_id == recorded_by_id)
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_requiring_follow_up(
        self,
        db: Session
    ) -> int:
        """
        Count outcomes requiring follow-up.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.follow_up_required.is_(True),
                self.model.follow_up_date.is_not(None)
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_upcoming_follow_ups(
        self,
        db: Session,
        reference_date: datetime
    ) -> int:
        """
        Count outcomes with upcoming follow-ups.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.follow_up_required.is_(True),
                self.model.follow_up_date >= reference_date,
                self.model.follow_up_date.is_not(None)
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # Bulk Operations (Atomic, Empty Guards)
    # -----------------------------------------

    def bulk_update_follow_up(
        self,
        db: Session,
        outcome_ids: List[UUID],
        follow_up_required: bool,
        follow_up_date: Optional[datetime] = None
    ) -> int:
        """
        Bulk update follow-up status for multiple outcomes.
        Atomic update statement.
        Empty-list guard included.
        Returns count of updated rows.
        NO soft-delete filter.
        """
        if not outcome_ids:
            return 0

        values = {'follow_up_required': follow_up_required}
        if follow_up_date is not None:
            values['follow_up_date'] = follow_up_date

        stmt = (
            update(self.model)
            .where(
                self.model.id.in_(outcome_ids)
            )
            .values(**values)
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
        Bulk update outcomes for a meeting.
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
        Bulk delete all outcomes for a meeting.
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