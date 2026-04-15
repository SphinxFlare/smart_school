# welfare/repositories/complaints/escalation_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from repositories.base import BaseRepository
from welfare.models.complaints import Escalation


class EscalationRepository(BaseRepository[Escalation]):
    """
    Repository for Escalation model operations.
    Extends BaseRepository - model does NOT contain school_id.
    Tenant isolation enforced through concern_id scoping at service layer.
    NO soft-delete filtering (model lacks is_deleted).
    Zero business logic, zero validation, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(Escalation)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        escalation_id: UUID
    ) -> Optional[Escalation]:
        """
        Retrieve escalation by ID.
        NO soft-delete filter (model lacks is_deleted).
        """
        stmt = (
            select(self.model)
            .where(self.model.id == escalation_id)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_id_concern_scoped(
        self,
        db: Session,
        escalation_id: UUID,
        concern_id: UUID
    ) -> Optional[Escalation]:
        """
        Retrieve escalation by ID scoped to concern.
        Prevents unauthorized access across concerns.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == escalation_id,
                self.model.concern_id == concern_id
            )
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_concern(
        self,
        db: Session,
        concern_id: UUID
    ) -> Optional[Escalation]:
        """
        Retrieve one escalation for a concern if exists.
        Does not guarantee single record.
        """
        stmt = (
            select(self.model)
            .where(self.model.concern_id == concern_id)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Listing Methods
    # -----------------------------------------

    def list_by_concern(
        self,
        db: Session,
        concern_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Escalation]:
        """
        List escalations for a concern.
        Deterministic ordering: escalated_at DESC, id DESC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.concern_id == concern_id)
            .order_by(
                self.model.escalated_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_escalated_to(
        self,
        db: Session,
        escalated_to_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Escalation]:
        """
        List escalations to a user across all concerns.
        Deterministic ordering: escalated_at DESC, id DESC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.escalated_to_id == escalated_to_id)
            .order_by(
                self.model.escalated_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_status(
        self,
        db: Session,
        concern_id: UUID,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Escalation]:
        """
        List escalations by status for a concern.
        Uses index on status.
        Deterministic ordering: escalated_at DESC, id DESC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.concern_id == concern_id,
                self.model.status == status
            )
            .order_by(
                self.model.escalated_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_priority(
        self,
        db: Session,
        concern_id: UUID,
        priority: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Escalation]:
        """
        List escalations by priority for a concern.
        Deterministic ordering: escalated_at DESC, id DESC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.concern_id == concern_id,
                self.model.priority == priority
            )
            .order_by(
                self.model.escalated_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_pending_escalations(
        self,
        db: Session,
        escalated_to_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Escalation]:
        """
        List pending escalations to a user.
        Deterministic ordering: due_date ASC, id ASC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.escalated_to_id == escalated_to_id,
                self.model.status == 'pending'
            )
            .order_by(
                self.model.due_date.asc().nulls_last(),
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
        concern_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[Escalation]:
        """
        List escalations within date range for a concern.
        Index-friendly filtering on escalated_at.
        Deterministic ordering: escalated_at DESC, id DESC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.concern_id == concern_id,
                self.model.escalated_at >= start_date,
                self.model.escalated_at <= end_date
            )
            .order_by(
                self.model.escalated_at.desc(),
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
        escalation_id: UUID
    ) -> Optional[Escalation]:
        """
        Lock escalation for update.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.id == escalation_id)
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_for_update_concern_scoped(
        self,
        db: Session,
        escalation_id: UUID,
        concern_id: UUID
    ) -> Optional[Escalation]:
        """
        Lock escalation for update scoped to concern.
        Maximum concurrency safety for sensitive mutation.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == escalation_id,
                self.model.concern_id == concern_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_by_concern_for_update(
        self,
        db: Session,
        concern_id: UUID
    ) -> Optional[Escalation]:
        """
        Lock escalation by concern for update.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.concern_id == concern_id)
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_all_by_concern_for_update(
        self,
        db: Session,
        concern_id: UUID
    ) -> List[Escalation]:
        """
        Lock all escalations for a concern.
        Used for batch operations.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.concern_id == concern_id)
            .with_for_update()
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def lock_all_by_escalated_to_for_update(
        self,
        db: Session,
        escalated_to_id: UUID
    ) -> List[Escalation]:
        """
        Lock all escalations to a user.
        Used for batch operations.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.escalated_to_id == escalated_to_id)
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
        escalation_id: UUID
    ) -> bool:
        """
        Efficient existence check for escalation by ID.
        NO soft-delete filter.
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(self.model.id == escalation_id)
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_by_id_concern_scoped(
        self,
        db: Session,
        escalation_id: UUID,
        concern_id: UUID
    ) -> bool:
        """
        Efficient existence check for escalation by ID scoped to concern.
        NO soft-delete filter.
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == escalation_id,
                self.model.concern_id == concern_id
            )
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_by_concern(
        self,
        db: Session,
        concern_id: UUID
    ) -> bool:
        """
        Existence check for escalation by concern.
        NO soft-delete filter.
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(self.model.concern_id == concern_id)
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    # -----------------------------------------
    # Aggregations (Null-Safe)
    # -----------------------------------------

    def count_by_concern(
        self,
        db: Session,
        concern_id: UUID
    ) -> int:
        """
        Count escalations for a concern.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.concern_id == concern_id)
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_escalated_to(
        self,
        db: Session,
        escalated_to_id: UUID
    ) -> int:
        """
        Count escalations to a user across all concerns.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.escalated_to_id == escalated_to_id)
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_status(
        self,
        db: Session,
        concern_id: UUID,
        status: str
    ) -> int:
        """
        Count escalations by status for a concern.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.concern_id == concern_id,
                self.model.status == status
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_pending_by_escalated_to(
        self,
        db: Session,
        escalated_to_id: UUID
    ) -> int:
        """
        Count pending escalations to a user.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.escalated_to_id == escalated_to_id,
                self.model.status == 'pending'
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # Bulk Operations (Atomic, Empty Guards)
    # -----------------------------------------

    def bulk_update_status(
        self,
        db: Session,
        escalation_ids: List[UUID],
        new_status: str
    ) -> int:
        """
        Bulk update status for multiple escalations.
        Atomic update statement.
        Empty-list guard included.
        Returns count of updated rows.
        NO soft-delete filter.
        """
        if not escalation_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.id.in_(escalation_ids)
            )
            .values(status=new_status)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_by_concern(
        self,
        db: Session,
        concern_id: UUID,
        updates: Dict[str, Any]
    ) -> int:
        """
        Bulk update escalations for a concern.
        Atomic update statement scoped by concern_id.
        Empty-list guard included.
        Returns count of updated rows.
        NO soft-delete filter.
        """
        if not updates:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.concern_id == concern_id
            )
            .values(**updates)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_by_escalated_to(
        self,
        db: Session,
        escalated_to_id: UUID,
        updates: Dict[str, Any]
    ) -> int:
        """
        Bulk update escalations to a user.
        Atomic update statement scoped by escalated_to_id.
        Empty-list guard included.
        Returns count of updated rows.
        NO soft-delete filter.
        """
        if not updates:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.escalated_to_id == escalated_to_id
            )
            .values(**updates)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_resolve_escalations(
        self,
        db: Session,
        escalation_ids: List[UUID],
        resolved_at: datetime,
        resolution_notes: Optional[str] = None
    ) -> int:
        """
        Bulk resolve multiple escalations.
        Atomic update statement.
        Empty-list guard included.
        Returns count of updated rows.
        NO soft-delete filter.
        """
        if not escalation_ids:
            return 0

        values = {
            'status': 'resolved',
            'resolved_at': resolved_at
        }
        if resolution_notes is not None:
            values['resolution_notes'] = resolution_notes

        stmt = (
            update(self.model)
            .where(
                self.model.id.in_(escalation_ids)
            )
            .values(**values)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_delete_by_concern(
        self,
        db: Session,
        concern_id: UUID
    ) -> int:
        """
        Bulk delete all escalations for a concern.
        Atomic delete statement scoped by concern_id.
        Returns count of deleted rows.
        NO soft-delete filter (hard delete).
        """
        from sqlalchemy import delete
        stmt = (
            delete(self.model)
            .where(self.model.concern_id == concern_id)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0