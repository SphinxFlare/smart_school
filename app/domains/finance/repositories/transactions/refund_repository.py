# finance/repositories/transactions/refund_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update
from decimal import Decimal

from repositories.base import SchoolScopedRepository
from finance.models.transactions import Refund


class RefundRepository(SchoolScopedRepository[Refund]):
    """
    Repository for Refund model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    Zero business logic, zero approval/validation logic.
    NOTE: Refund model does NOT have is_deleted, so no soft-delete filtering.
    """

    def __init__(self):
        super().__init__(Refund)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        school_id: UUID,
        refund_id: UUID
    ) -> Optional[Refund]:
        """
        Retrieve refund by ID scoped to school.
        Prevents horizontal privilege escalation.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == refund_id,
                self.model.school_id == school_id
            )
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Listing Methods
    # -----------------------------------------

    def list_by_payment(
        self,
        db: Session,
        school_id: UUID,
        payment_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Refund]:
        """
        List refunds by payment ID within school tenant.
        Deterministic ordering: created_at DESC, id DESC.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.payment_id == payment_id
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

    def list_by_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Refund]:
        """
        List refunds by student within school tenant.
        Deterministic ordering: created_at DESC, id DESC.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id
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

    def list_by_status(
        self,
        db: Session,
        school_id: UUID,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Refund]:
        """
        List refunds by status within school tenant.
        Uses index on status.
        Deterministic ordering: created_at DESC, id DESC.
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

    def list_school_wide(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Refund]:
        """
        List all refunds within school tenant.
        Deterministic ordering: created_at DESC, id DESC.
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
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Row Locking
    # -----------------------------------------

    def lock_for_update(
        self,
        db: Session,
        school_id: UUID,
        refund_id: UUID
    ) -> Optional[Refund]:
        """
        Lock refund for update (processing workflows).
        Scoped to school_id for tenant safety.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == refund_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_for_update_student_scoped(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        refund_id: UUID
    ) -> Optional[Refund]:
        """
        Lock refund for update scoped to school and student.
        Maximum concurrency safety.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == refund_id,
                self.model.school_id == school_id,
                self.model.student_id == student_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_by_payment_for_update(
        self,
        db: Session,
        school_id: UUID,
        payment_id: UUID
    ) -> Optional[Refund]:
        """
        Lock refund by payment_id for update.
        Tenant-safe locking.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.payment_id == payment_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Existence Checks
    # -----------------------------------------

    def exists_pending_by_payment(
        self,
        db: Session,
        school_id: UUID,
        payment_id: UUID
    ) -> bool:
        """
        Efficient existence check for pending refunds per payment.
        Uses select(id).limit(1) style for performance.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.school_id == school_id,
                self.model.payment_id == payment_id,
                self.model.status == 'pending'
            )
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_by_id(
        self,
        db: Session,
        school_id: UUID,
        refund_id: UUID
    ) -> bool:
        """
        Efficient existence check for refund by ID.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == refund_id,
                self.model.school_id == school_id
            )
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    # -----------------------------------------
    # Aggregations (Null-Safe)
    # -----------------------------------------

    def sum_amount_by_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        status_filter: Optional[str] = None
    ) -> Decimal:
        """
        Sum refund amount for a student within school.
        NO business logic interpretation.
        Null-safe aggregation.
        """
        stmt = select(func.sum(self.model.amount)).where(
            self.model.school_id == school_id,
            self.model.student_id == student_id
        )
        
        if status_filter:
            stmt = stmt.where(self.model.status == status_filter)
        
        result = db.execute(stmt)
        value = result.scalar()
        return value if value is not None else Decimal('0.0')

    def sum_amount_by_status(
        self,
        db: Session,
        school_id: UUID,
        status: str
    ) -> Decimal:
        """
        Sum refund amount by status within school.
        NO business logic interpretation.
        Null-safe aggregation.
        """
        stmt = (
            select(func.sum(self.model.amount))
            .where(
                self.model.school_id == school_id,
                self.model.status == status
            )
        )
        result = db.execute(stmt)
        value = result.scalar()
        return value if value is not None else Decimal('0.0')

    def count_by_status(
        self,
        db: Session,
        school_id: UUID,
        status: str
    ) -> int:
        """
        Count refunds by status within school.
        Null-safe aggregation.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.status == status
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # Bulk Operations (Atomic, Whitelisted)
    # -----------------------------------------

    def bulk_update_status(
        self,
        db: Session,
        school_id: UUID,
        refund_ids: List[UUID],
        new_status: str,
        processed_at: Optional[datetime] = None,
        processed_by_id: Optional[UUID] = None
    ) -> int:
        """
        Bulk update status for multiple refunds.
        Atomic update statement scoped by school_id.
        Whitelists only status, processed_at, processed_by_id.
        Prevents mutation of identifiers, payment linkage, or amount.
        Returns count of updated rows.
        """
        if not refund_ids:
            return 0
        
        values = {'status': new_status}
        if processed_at is not None:
            values['processed_at'] = processed_at
        if processed_by_id is not None:
            values['processed_by_id'] = processed_by_id

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(refund_ids)
            )
            .values(**values)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_transaction_details(
        self,
        db: Session,
        school_id: UUID,
        refund_ids: List[UUID],
        transaction_reference: Optional[str] = None,
        notes: Optional[str] = None
    ) -> int:
        """
        Bulk update transaction details (reference, notes) for multiple refunds.
        Atomic update statement scoped by school_id.
        Whitelists only transaction_reference and notes.
        Returns count of updated rows.
        """
        if not refund_ids:
            return 0
        
        values = {}
        if transaction_reference is not None:
            values['transaction_reference'] = transaction_reference
        if notes is not None:
            values['notes'] = notes
        
        if not values:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(refund_ids)
            )
            .values(**values)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0