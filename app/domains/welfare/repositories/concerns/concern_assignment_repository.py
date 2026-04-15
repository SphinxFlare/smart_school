# welfare/repositories/complaints/concern_assignment_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from repositories.base import BaseRepository
from welfare.models.complaints import ConcernAssignment


class ConcernAssignmentRepository(BaseRepository[ConcernAssignment]):
    """
    Repository for ConcernAssignment model operations.
    Extends BaseRepository - model does NOT contain school_id.
    Tenant isolation enforced through concern_id scoping at service layer.
    NO soft-delete filtering (model lacks is_deleted).
    Zero business logic, zero validation, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(ConcernAssignment)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        assignment_id: UUID
    ) -> Optional[ConcernAssignment]:
        """
        Retrieve assignment by ID.
        NO soft-delete filter (model lacks is_deleted).
        """
        stmt = (
            select(self.model)
            .where(self.model.id == assignment_id)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_id_concern_scoped(
        self,
        db: Session,
        assignment_id: UUID,
        concern_id: UUID
    ) -> Optional[ConcernAssignment]:
        """
        Retrieve assignment by ID scoped to concern.
        Prevents unauthorized access across concerns.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == assignment_id,
                self.model.concern_id == concern_id
            )
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_concern_and_assignee(
        self,
        db: Session,
        concern_id: UUID,
        assigned_to_id: UUID
    ) -> Optional[ConcernAssignment]:
        """
        Retrieve assignment by concern and assignee.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.concern_id == concern_id,
                self.model.assigned_to_id == assigned_to_id
            )
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
    ) -> List[ConcernAssignment]:
        """
        List assignments for a concern.
        Deterministic ordering: assigned_at DESC, id DESC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.concern_id == concern_id)
            .order_by(
                self.model.assigned_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_assignee(
        self,
        db: Session,
        assigned_to_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ConcernAssignment]:
        """
        List assignments for an assignee across all concerns.
        Uses index on assigned_to_id.
        Deterministic ordering: assigned_at DESC, id DESC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.assigned_to_id == assigned_to_id)
            .order_by(
                self.model.assigned_at.desc(),
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
    ) -> List[ConcernAssignment]:
        """
        List assignments by status for a concern.
        Uses index on status.
        Deterministic ordering: assigned_at DESC, id DESC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.concern_id == concern_id,
                self.model.status == status
            )
            .order_by(
                self.model.assigned_at.desc(),
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
    ) -> List[ConcernAssignment]:
        """
        List assignments by priority for a concern.
        Deterministic ordering: assigned_at DESC, id DESC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.concern_id == concern_id,
                self.model.priority == priority
            )
            .order_by(
                self.model.assigned_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_pending_assignments(
        self,
        db: Session,
        assigned_to_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ConcernAssignment]:
        """
        List pending assignments for an assignee.
        Deterministic ordering: due_date ASC, id ASC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.assigned_to_id == assigned_to_id,
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

    # -----------------------------------------
    # Row Locking
    # -----------------------------------------

    def lock_for_update(
        self,
        db: Session,
        assignment_id: UUID
    ) -> Optional[ConcernAssignment]:
        """
        Lock assignment for update.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.id == assignment_id)
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_for_update_concern_scoped(
        self,
        db: Session,
        assignment_id: UUID,
        concern_id: UUID
    ) -> Optional[ConcernAssignment]:
        """
        Lock assignment for update scoped to concern.
        Maximum concurrency safety for sensitive mutation.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == assignment_id,
                self.model.concern_id == concern_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_by_concern_and_assignee_for_update(
        self,
        db: Session,
        concern_id: UUID,
        assigned_to_id: UUID
    ) -> Optional[ConcernAssignment]:
        """
        Lock assignment by concern and assignee for update.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.concern_id == concern_id,
                self.model.assigned_to_id == assigned_to_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_all_by_concern_for_update(
        self,
        db: Session,
        concern_id: UUID
    ) -> List[ConcernAssignment]:
        """
        Lock all assignments for a concern.
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

    def lock_all_by_assignee_for_update(
        self,
        db: Session,
        assigned_to_id: UUID
    ) -> List[ConcernAssignment]:
        """
        Lock all assignments for an assignee.
        Used for batch operations.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.assigned_to_id == assigned_to_id)
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
        assignment_id: UUID
    ) -> bool:
        """
        Efficient existence check for assignment by ID.
        NO soft-delete filter.
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(self.model.id == assignment_id)
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_by_concern_and_assignee(
        self,
        db: Session,
        concern_id: UUID,
        assigned_to_id: UUID,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for assignment by concern and assignee.
        Optional exclude_id for update operations.
        NO soft-delete filter.
        Uses select(id).limit(1) pattern.
        """
        stmt = select(self.model.id).where(
            self.model.concern_id == concern_id,
            self.model.assigned_to_id == assigned_to_id
        )
        
        if exclude_id is not None:
            stmt = stmt.where(self.model.id != exclude_id)
        
        stmt = stmt.limit(1)
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
        Count assignments for a concern.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.concern_id == concern_id)
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_assignee(
        self,
        db: Session,
        assigned_to_id: UUID
    ) -> int:
        """
        Count assignments for an assignee across all concerns.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.assigned_to_id == assigned_to_id)
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
        Count assignments by status for a concern.
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

    def count_pending_by_assignee(
        self,
        db: Session,
        assigned_to_id: UUID
    ) -> int:
        """
        Count pending assignments for an assignee.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.assigned_to_id == assigned_to_id,
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
        assignment_ids: List[UUID],
        new_status: str
    ) -> int:
        """
        Bulk update status for multiple assignments.
        Atomic update statement.
        Empty-list guard included.
        Returns count of updated rows.
        NO soft-delete filter.
        """
        if not assignment_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.id.in_(assignment_ids)
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
        Bulk update assignments for a concern.
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

    def bulk_update_by_assignee(
        self,
        db: Session,
        assigned_to_id: UUID,
        updates: Dict[str, Any]
    ) -> int:
        """
        Bulk update assignments for an assignee.
        Atomic update statement scoped by assigned_to_id.
        Empty-list guard included.
        Returns count of updated rows.
        NO soft-delete filter.
        """
        if not updates:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.assigned_to_id == assigned_to_id
            )
            .values(**updates)
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
        Bulk delete all assignments for a concern.
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