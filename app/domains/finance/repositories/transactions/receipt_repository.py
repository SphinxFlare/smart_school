# finance/repositories/transactions/receipt_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update
from decimal import Decimal

from repositories.base import SchoolScopedRepository
from finance.models.transactions import Receipt


class ReceiptRepository(SchoolScopedRepository[Receipt]):
    """
    Repository for Receipt model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    Zero business logic, zero receipt number generation.
    NOTE: Receipt model does NOT have is_deleted, so no soft-delete filtering.
    """

    def __init__(self):
        super().__init__(Receipt)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        school_id: UUID,
        receipt_id: UUID
    ) -> Optional[Receipt]:
        """
        Retrieve receipt by ID scoped to school.
        Prevents horizontal privilege escalation.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == receipt_id,
                self.model.school_id == school_id
            )
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_receipt_number(
        self,
        db: Session,
        school_id: UUID,
        receipt_number: str
    ) -> Optional[Receipt]:
        """
        Retrieve receipt by receipt_number scoped to school.
        Respects unique constraint (school_id, receipt_number).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.receipt_number == receipt_number
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
    ) -> List[Receipt]:
        """
        List receipts by payment ID within school tenant.
        Deterministic ordering: date_issued DESC, id DESC.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.payment_id == payment_id
            )
            .order_by(
                self.model.date_issued.desc(),
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
    ) -> List[Receipt]:
        """
        List receipts by student within school tenant.
        Deterministic ordering: date_issued DESC, id DESC.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id
            )
            .order_by(
                self.model.date_issued.desc(),
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
    ) -> List[Receipt]:
        """
        List all receipts within school tenant.
        Deterministic ordering: date_issued DESC, id DESC.
        """
        stmt = (
            select(self.model)
            .where(self.model.school_id == school_id)
            .order_by(
                self.model.date_issued.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_voided(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Receipt]:
        """
        List voided receipts within school tenant.
        Deterministic ordering: date_issued DESC, id DESC.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.is_voided.is_(True)
            )
            .order_by(
                self.model.date_issued.desc(),
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
        receipt_id: UUID
    ) -> Optional[Receipt]:
        """
        Lock receipt for update (e.g., voiding).
        Scoped to school_id for tenant safety.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == receipt_id,
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
        receipt_id: UUID
    ) -> Optional[Receipt]:
        """
        Lock receipt for update scoped to school and student.
        Maximum concurrency safety.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == receipt_id,
                self.model.school_id == school_id,
                self.model.student_id == student_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Existence Checks
    # -----------------------------------------

    def exists_receipt_number(
        self,
        db: Session,
        school_id: UUID,
        receipt_number: str,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for receipt_number within school.
        Respects unique constraint (school_id, receipt_number).
        Optional exclude_id for update operations.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.school_id == school_id,
            self.model.receipt_number == receipt_number
        )
        
        if exclude_id is not None:
            stmt = stmt.where(self.model.id != exclude_id)
        
        result = db.execute(stmt)
        count = result.scalar() or 0
        return count > 0

    def exists_by_id(
        self,
        db: Session,
        school_id: UUID,
        receipt_id: UUID
    ) -> bool:
        """
        Efficient existence check for receipt by ID.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == receipt_id,
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
        include_voided: bool = False
    ) -> Decimal:
        """
        Sum receipt amount for a student within school.
        NO business logic interpretation.
        Null-safe aggregation.
        """
        stmt = select(func.sum(self.model.amount)).where(
            self.model.school_id == school_id,
            self.model.student_id == student_id
        )
        
        if not include_voided:
            stmt = stmt.where(self.model.is_voided.is_(False))
        
        result = db.execute(stmt)
        value = result.scalar()
        return value if value is not None else Decimal('0.0')

    def sum_amount_school_wide(
        self,
        db: Session,
        school_id: UUID,
        include_voided: bool = False
    ) -> Decimal:
        """
        Sum receipt amount across school.
        NO business logic interpretation.
        Null-safe aggregation.
        """
        stmt = select(func.sum(self.model.amount)).where(
            self.model.school_id == school_id
        )
        
        if not include_voided:
            stmt = stmt.where(self.model.is_voided.is_(False))
        
        result = db.execute(stmt)
        value = result.scalar()
        return value if value is not None else Decimal('0.0')

    def count_voided(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count voided receipts within school.
        Null-safe aggregation.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.is_voided.is_(True)
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # Bulk Operations (Atomic, Whitelisted)
    # -----------------------------------------

    def bulk_void_receipts(
        self,
        db: Session,
        school_id: UUID,
        receipt_ids: List[UUID],
        voided_at: datetime,
        voided_by_id: UUID,
        void_reason: str
    ) -> int:
        """
        Bulk void receipts.
        Atomic update statement scoped by school_id.
        Whitelists only void-related fields (is_voided, voided_at, voided_by_id, void_reason).
        Prevents mutation of identifiers, payment linkage, or amount.
        Returns count of updated rows.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(receipt_ids),
                self.model.is_voided.is_(False)  # Only void non-voided receipts
            )
            .values(
                is_voided=True,
                voided_at=voided_at,
                voided_by_id=voided_by_id,
                void_reason=void_reason
            )
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0