# welfare/repositories/meetings/meeting_agenda_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update, case, delete

from repositories.base import BaseRepository
from welfare.models.meetings import MeetingAgenda


class MeetingAgendaRepository(BaseRepository[MeetingAgenda]):
    """
    Repository for MeetingAgenda model operations.
    Extends BaseRepository - model does NOT contain school_id.
    Tenant isolation enforced through meeting_id scoping at service layer.
    NO soft-delete filtering (model lacks is_deleted).
    Zero business logic, zero validation, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(MeetingAgenda)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        agenda_id: UUID
    ) -> Optional[MeetingAgenda]:
        """
        Retrieve agenda item by ID.
        NO soft-delete filter (model lacks is_deleted).
        """
        stmt = (
            select(self.model)
            .where(self.model.id == agenda_id)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_id_meeting_scoped(
        self,
        db: Session,
        agenda_id: UUID,
        meeting_id: UUID
    ) -> Optional[MeetingAgenda]:
        """
        Retrieve agenda item by ID scoped to meeting.
        Prevents unauthorized access across meetings.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == agenda_id,
                self.model.meeting_id == meeting_id
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
    ) -> List[MeetingAgenda]:
        """
        List agenda items for a meeting.
        Deterministic ordering: item_order ASC, id ASC (sequence matters).
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.meeting_id == meeting_id)
            .order_by(
                self.model.item_order.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_meeting_ordered(
        self,
        db: Session,
        meeting_id: UUID
    ) -> List[MeetingAgenda]:
        """
        List all agenda items for a meeting ordered by sequence.
        No pagination - returns all items for meeting processing.
        Deterministic ordering: item_order ASC, id ASC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.meeting_id == meeting_id)
            .order_by(
                self.model.item_order.asc(),
                self.model.id.asc()
            )
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_status(
        self,
        db: Session,
        meeting_id: UUID,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[MeetingAgenda]:
        """
        List agenda items by status for a meeting.
        Deterministic ordering: item_order ASC, id ASC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.meeting_id == meeting_id,
                self.model.status == status
            )
            .order_by(
                self.model.item_order.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_assigned_to(
        self,
        db: Session,
        assigned_to_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[MeetingAgenda]:
        """
        List agenda items assigned to a user.
        Deterministic ordering: created_at DESC, id DESC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.assigned_to_id == assigned_to_id)
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
    # Row Locking
    # -----------------------------------------

    def lock_for_update(
        self,
        db: Session,
        agenda_id: UUID
    ) -> Optional[MeetingAgenda]:
        """
        Lock agenda item for update.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.id == agenda_id)
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_for_update_meeting_scoped(
        self,
        db: Session,
        agenda_id: UUID,
        meeting_id: UUID
    ) -> Optional[MeetingAgenda]:
        """
        Lock agenda item for update scoped to meeting.
        Maximum concurrency safety for sensitive mutation.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == agenda_id,
                self.model.meeting_id == meeting_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_all_by_meeting_for_update(
        self,
        db: Session,
        meeting_id: UUID
    ) -> List[MeetingAgenda]:
        """
        Lock all agenda items for a meeting.
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

    def lock_by_meeting_and_order_for_update(
        self,
        db: Session,
        meeting_id: UUID,
        item_order: int
    ) -> Optional[MeetingAgenda]:
        """
        Lock agenda item by meeting and item_order for update.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.meeting_id == meeting_id,
                self.model.item_order == item_order
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
        agenda_id: UUID
    ) -> bool:
        """
        Efficient existence check for agenda item by ID.
        NO soft-delete filter.
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(self.model.id == agenda_id)
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_by_meeting_and_order(
        self,
        db: Session,
        meeting_id: UUID,
        item_order: int,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for agenda item by meeting and item_order.
        Optional exclude_id for update operations.
        NO soft-delete filter.
        Uses select(id).limit(1) pattern.
        """
        stmt = select(self.model.id).where(
            self.model.meeting_id == meeting_id,
            self.model.item_order == item_order
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
        Count agenda items for a meeting.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.meeting_id == meeting_id)
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_status(
        self,
        db: Session,
        meeting_id: UUID,
        status: str
    ) -> int:
        """
        Count agenda items by status for a meeting.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.meeting_id == meeting_id,
                self.model.status == status
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_assigned_to(
        self,
        db: Session,
        assigned_to_id: UUID
    ) -> int:
        """
        Count agenda items assigned to a user.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.assigned_to_id == assigned_to_id)
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def get_max_item_order(
        self,
        db: Session,
        meeting_id: UUID
    ) -> int:
        """
        Get maximum item_order for a meeting.
        Returns 0 if no items exist.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.max(self.model.item_order))
            .where(self.model.meeting_id == meeting_id)
        )
        result = db.execute(stmt)
        value = result.scalar()
        return value if value is not None else 0

    # -----------------------------------------
    # Bulk Operations (Atomic, Empty Guards)
    # -----------------------------------------

    def bulk_update_status(
        self,
        db: Session,
        agenda_ids: List[UUID],
        new_status: str
    ) -> int:
        """
        Bulk update status for multiple agenda items.
        Atomic update statement.
        Empty-list guard included.
        Returns count of updated rows.
        NO soft-delete filter.
        """
        if not agenda_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.id.in_(agenda_ids)
            )
            .values(status=new_status)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_item_order(
        self,
        db: Session,
        meeting_id: UUID,
        order_updates: List[Dict[str, Any]]
    ) -> int:
        """
        Bulk update item_order for multiple agenda items.
        Uses CASE expression for atomic update.
        order_updates: [{'id': UUID, 'item_order': int}]
        Returns count of updated rows.
        """

        if not order_updates:
            return 0

        ids = [item["id"] for item in order_updates]

        case_stmt = case(
            {item["id"]: item["item_order"] for item in order_updates},
            value=self.model.id,
        )

        stmt = (
            update(self.model)
            .where(
                self.model.meeting_id == meeting_id,
                self.model.id.in_(ids),
            )
            .values(item_order=case_stmt)
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
        Bulk update agenda items for a meeting.
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
        Bulk delete all agenda items for a meeting.
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