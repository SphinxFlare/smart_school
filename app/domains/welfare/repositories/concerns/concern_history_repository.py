# welfare/repositories/complaints/concern_history_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from repositories.base import BaseRepository
from welfare.models.complaints import ConcernHistory


class ConcernHistoryRepository(BaseRepository[ConcernHistory]):
    """
    Repository for ConcernHistory model operations.
    Extends BaseRepository - model does NOT contain school_id.
    Tenant isolation enforced through concern_id scoping at service layer.
    NO soft-delete filtering (model lacks is_deleted - audit log).
    Zero business logic, zero validation, zero authorization decisions.
    Append-only audit log - avoid update-heavy APIs.
    """

    def __init__(self):
        super().__init__(ConcernHistory)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        history_id: UUID
    ) -> Optional[ConcernHistory]:
        """
        Retrieve history record by ID.
        NO soft-delete filter (audit log).
        """
        stmt = (
            select(self.model)
            .where(self.model.id == history_id)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_id_concern_scoped(
        self,
        db: Session,
        history_id: UUID,
        concern_id: UUID
    ) -> Optional[ConcernHistory]:
        """
        Retrieve history record by ID scoped to concern.
        Prevents unauthorized access across concerns.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == history_id,
                self.model.concern_id == concern_id
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
    ) -> List[ConcernHistory]:
        """
        List history records for a concern.
        Deterministic ordering: changed_at ASC, id ASC (audit trail order).
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.concern_id == concern_id)
            .order_by(
                self.model.changed_at.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_concern_ordered(
        self,
        db: Session,
        concern_id: UUID
    ) -> List[ConcernHistory]:
        """
        List all history records for a concern ordered by audit trail.
        No pagination - returns all records for concern processing.
        Deterministic ordering: changed_at ASC, id ASC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.concern_id == concern_id)
            .order_by(
                self.model.changed_at.asc(),
                self.model.id.asc()
            )
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_action(
        self,
        db: Session,
        concern_id: UUID,
        action: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ConcernHistory]:
        """
        List history records by action for a concern.
        Deterministic ordering: changed_at ASC, id ASC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.concern_id == concern_id,
                self.model.action == action
            )
            .order_by(
                self.model.changed_at.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_changer(
        self,
        db: Session,
        changed_by_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ConcernHistory]:
        """
        List history records by changer across all concerns.
        Deterministic ordering: changed_at DESC, id DESC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.changed_by_id == changed_by_id)
            .order_by(
                self.model.changed_at.desc(),
                self.model.id.desc()
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
    ) -> List[ConcernHistory]:
        """
        List history records within date range for a concern.
        Index-friendly filtering on changed_at.
        Deterministic ordering: changed_at ASC, id ASC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.concern_id == concern_id,
                self.model.changed_at >= start_date,
                self.model.changed_at <= end_date
            )
            .order_by(
                self.model.changed_at.asc(),
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
        history_id: UUID
    ) -> Optional[ConcernHistory]:
        """
        Lock history record for update.
        NO soft-delete filter.
        Note: History is typically immutable, but lock provided for edge cases.
        """
        stmt = (
            select(self.model)
            .where(self.model.id == history_id)
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_all_by_concern_for_update(
        self,
        db: Session,
        concern_id: UUID
    ) -> List[ConcernHistory]:
        """
        Lock all history records for a concern.
        Used for audit trail operations.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.concern_id == concern_id)
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
        history_id: UUID
    ) -> bool:
        """
        Efficient existence check for history record by ID.
        NO soft-delete filter.
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(self.model.id == history_id)
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_by_id_concern_scoped(
        self,
        db: Session,
        history_id: UUID,
        concern_id: UUID
    ) -> bool:
        """
        Efficient existence check for history record by ID scoped to concern.
        NO soft-delete filter.
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == history_id,
                self.model.concern_id == concern_id
            )
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
        Count history records for a concern.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.concern_id == concern_id)
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_action(
        self,
        db: Session,
        concern_id: UUID,
        action: str
    ) -> int:
        """
        Count history records by action for a concern.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.concern_id == concern_id,
                self.model.action == action
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_changer(
        self,
        db: Session,
        changed_by_id: UUID
    ) -> int:
        """
        Count history records by changer across all concerns.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.changed_by_id == changed_by_id)
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # Insert-Safe Reads
    # -----------------------------------------

    def get_latest_history_by_concern(
        self,
        db: Session,
        concern_id: UUID
    ) -> Optional[ConcernHistory]:
        """
        Get the latest history record for a concern.
        Used for insert-safe reads before appending new history.
        Deterministic ordering: changed_at DESC, id DESC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(self.model.concern_id == concern_id)
            .order_by(
                self.model.changed_at.desc(),
                self.model.id.desc()
            )
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_latest_history_by_concern_and_action(
        self,
        db: Session,
        concern_id: UUID,
        action: str
    ) -> Optional[ConcernHistory]:
        """
        Get the latest history record for a concern filtered by action.
        Used for insert-safe reads before appending new history.
        Deterministic ordering: changed_at DESC, id DESC.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.concern_id == concern_id,
                self.model.action == action
            )
            .order_by(
                self.model.changed_at.desc(),
                self.model.id.desc()
            )
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Bulk Operations (Read-Only for Audit Log)
    # -----------------------------------------

    def bulk_delete_by_concern(
        self,
        db: Session,
        concern_id: UUID
    ) -> int:
        """
        Bulk delete all history records for a concern.
        Atomic delete statement scoped by concern_id.
        Returns count of deleted rows.
        NO soft-delete filter (hard delete).
        WARNING: Use only for data cleanup, not normal operations.
        """
        from sqlalchemy import delete
        stmt = (
            delete(self.model)
            .where(self.model.concern_id == concern_id)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0