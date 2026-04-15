# finance/repositories/transactions/payment_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update
from decimal import Decimal

from repositories.base import SchoolScopedRepository
from finance.models.transactions import Payment


class PaymentRepository(SchoolScopedRepository[Payment]):
    """
    Repository for Payment model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    Zero business logic, zero financial calculations, zero status transitions.
    """

    def __init__(self):
        super().__init__(Payment)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        school_id: UUID,
        payment_id: UUID
    ) -> Optional[Payment]:
        """
        Retrieve payment by ID scoped to school.
        Prevents horizontal privilege escalation.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == payment_id,
                self.model.school_id == school_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Listing Methods
    # -----------------------------------------

    def list_by_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Payment]:
        """
        List payments by student within school tenant.
        Deterministic ordering: payment_date DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id
            )
            .order_by(
                self.model.payment_date.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_student_fee(
        self,
        db: Session,
        school_id: UUID,
        student_fee_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Payment]:
        """
        List payments by student fee record within school tenant.
        Deterministic ordering: payment_date DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_fee_id == student_fee_id
            )
            .order_by(
                self.model.payment_date.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_admission_application(
        self,
        db: Session,
        school_id: UUID,
        admission_application_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Payment]:
        """
        List payments by admission application within school tenant.
        Deterministic ordering: payment_date DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.admission_application_id == admission_application_id
            )
            .order_by(
                self.model.payment_date.desc(),
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
        status: Any,  # PaymentStatus enum
        skip: int = 0,
        limit: int = 100
    ) -> List[Payment]:
        """
        List payments by status within school tenant.
        Uses index on status.
        Deterministic ordering: payment_date DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.status == status
            )
            .order_by(
                self.model.payment_date.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_school_wide(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Payment]:
        """
        List all payments within school tenant.
        Deterministic ordering: payment_date DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(self.model.school_id == school_id)
            .order_by(
                self.model.payment_date.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Row Locking
    # -----------------------------------------

    def lock_for_update(
        self,
        db: Session,
        school_id: UUID,
        payment_id: UUID
    ) -> Optional[Payment]:
        """
        Lock payment for update.
        Scoped to school_id for tenant safety.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == payment_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_for_update_student_scoped(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        payment_id: UUID
    ) -> Optional[Payment]:
        """
        Lock payment for update scoped to school and student.
        Maximum concurrency safety.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == payment_id,
                self.model.school_id == school_id,
                self.model.student_id == student_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Existence Checks
    # -----------------------------------------

    def exists_by_id(
        self,
        db: Session,
        school_id: UUID,
        payment_id: UUID
    ) -> bool:
        """
        Efficient existence check for payment by ID.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == payment_id,
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

    def sum_amount_by_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        status_filter: Optional[Any] = None
    ) -> Decimal:
        """
        Sum payment amount for a student within school.
        NO business logic interpretation (pure DB sum).
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = select(func.sum(self.model.amount)).where(
            self.model.school_id == school_id,
            self.model.student_id == student_id
        )
        
        if status_filter is not None:
            stmt = stmt.where(self.model.status == status_filter)
        
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        value = result.scalar()
        return value if value is not None else Decimal('0.0')

    def sum_amount_by_status(
        self,
        db: Session,
        school_id: UUID,
        status: Any
    ) -> Decimal:
        """
        Sum payment amount by status within school.
        NO business logic interpretation.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.sum(self.model.amount))
            .where(
                self.model.school_id == school_id,
                self.model.status == status
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        value = result.scalar()
        return value if value is not None else Decimal('0.0')

    def count_by_status(
        self,
        db: Session,
        school_id: UUID,
        status: Any
    ) -> int:
        """
        Count payments by status within school.
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

    # -----------------------------------------
    # Bulk Operations (Atomic, Whitelisted)
    # -----------------------------------------

    def bulk_update_status(
        self,
        db: Session,
        school_id: UUID,
        payment_ids: List[UUID],
        new_status: Any
    ) -> int:
        """
        Bulk update status for multiple payments.
        Atomic update statement scoped by school_id.
        Excludes soft-deleted records explicitly.
        Whitelists only 'status' field.
        Returns count of updated rows.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(payment_ids),
                self.model.is_deleted.is_(False)
            )
            .values(status=new_status)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_details(
        self,
        db: Session,
        school_id: UUID,
        payment_ids: List[UUID],
        transaction_reference: Optional[str] = None,
        remarks: Optional[str] = None
    ) -> int:
        """
        Bulk update mutable details (reference, remarks) for multiple payments.
        Atomic update statement scoped by school_id.
        Excludes soft-deleted records explicitly.
        Whitelists only 'transaction_reference' and 'remarks'.
        Returns count of updated rows.
        """
        values = {}
        if transaction_reference is not None:
            values['transaction_reference'] = transaction_reference
        if remarks is not None:
            values['remarks'] = remarks
        
        if not values:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(payment_ids),
                self.model.is_deleted.is_(False)
            )
            .values(**values)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0