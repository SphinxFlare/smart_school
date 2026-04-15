# finance/repositories/record/student_fee_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update
from decimal import Decimal

from repositories.base import SchoolScopedRepository
from finance.models.record import StudentFee


class StudentFeeRepository(SchoolScopedRepository[StudentFee]):
    """
    Repository for StudentFee model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    Zero business logic, zero financial calculations, zero status transitions.
    """

    def __init__(self):
        super().__init__(StudentFee)

    # -----------------------------------------
    # Student-Scoped Listing
    # -----------------------------------------

    def list_by_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        order_by_due_date: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentFee]:
        """
        List fee records by student within school tenant.
        Deterministic ordering:
        - order_by_due_date=True: due_date ASC, id ASC (upcoming dues)
        - order_by_due_date=False: created_at DESC, id DESC (history)
        Soft-delete filtered.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.student_id == student_id
        )

        if order_by_due_date:
            stmt = stmt.order_by(
                self.model.due_date.asc(),
                self.model.id.asc()
            )
        else:
            stmt = stmt.order_by(
                self.model.created_at.desc(),
                self.model.id.desc()
            )

        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_student_and_academic_year(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        academic_year_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentFee]:
        """
        List fee records by student and academic year within school tenant.
        Deterministic ordering: due_date ASC, id ASC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id,
                self.model.academic_year_id == academic_year_id
            )
            .order_by(
                self.model.due_date.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Filtering
    # -----------------------------------------

    def filter_by_status(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentFee]:
        """
        Filter fee records by status within school tenant.
        Uses index on status.
        Deterministic ordering: due_date ASC, id ASC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id,
                self.model.status == status
            )
            .order_by(
                self.model.due_date.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def filter_by_academic_year(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentFee]:
        """
        Filter fee records by academic year within school tenant.
        Cross-student query but MUST remain within tenant boundaries.
        Deterministic ordering: due_date ASC, id ASC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.academic_year_id == academic_year_id
            )
            .order_by(
                self.model.due_date.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def filter_by_status_school_wide(
        self,
        db: Session,
        school_id: UUID,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentFee]:
        """
        Filter fee records by status across all students in school.
        Deterministic ordering: due_date ASC, id ASC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.status == status
            )
            .order_by(
                self.model.due_date.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Unique Retrieval
    # -----------------------------------------

    def get_by_composite_unique(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        fee_structure_id: UUID
    ) -> Optional[StudentFee]:
        """
        Retrieve by composite uniqueness (school + student + fee_structure).
        Respects database unique constraint.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id,
                self.model.fee_structure_id == fee_structure_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_id_school_scoped(
        self,
        db: Session,
        school_id: UUID,
        fee_id: UUID
    ) -> Optional[StudentFee]:
        """
        Retrieve by ID scoped to school.
        Prevents horizontal privilege escalation across tenants.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == fee_id,
                self.model.school_id == school_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_id_student_scoped(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        fee_id: UUID
    ) -> Optional[StudentFee]:
        """
        Retrieve by ID scoped to both school and student.
        Maximum safety for sensitive operations.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == fee_id,
                self.model.school_id == school_id,
                self.model.student_id == student_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Row Locking
    # -----------------------------------------

    def lock_for_update(
        self,
        db: Session,
        school_id: UUID,
        fee_id: UUID
    ) -> Optional[StudentFee]:
        """
        Lock fee record for update to prevent concurrent modifications.
        Scoped to school_id for tenant safety.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == fee_id,
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
        fee_id: UUID
    ) -> Optional[StudentFee]:
        """
        Lock fee record for update scoped to school and student.
        Maximum concurrency safety.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == fee_id,
                self.model.school_id == school_id,
                self.model.student_id == student_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_by_composite_for_update(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        fee_structure_id: UUID
    ) -> Optional[StudentFee]:
        """
        Lock fee record by composite unique keys for update.
        Tenant-safe locking.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id,
                self.model.fee_structure_id == fee_structure_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Aggregations (Null-Safe)
    # -----------------------------------------

    def count_by_status(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        status: str
    ) -> int:
        """
        Count fee records by status for a student within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id,
                self.model.status == status
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_status_school_wide(
        self,
        db: Session,
        school_id: UUID,
        status: str
    ) -> int:
        """
        Count fee records by status across all students in school.
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

    def sum_amount_due(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        status_filter: Optional[str] = None
    ) -> Decimal:
        """
        Sum amount_due for a student within school.
        NO business logic interpretation (pure DB sum).
        Null-safe aggregation (returns Decimal('0.0') if None).
        Soft-delete filtered.
        """
        stmt = select(func.sum(self.model.amount_due)).where(
            self.model.school_id == school_id,
            self.model.student_id == student_id
        )
        
        if status_filter:
            stmt = stmt.where(self.model.status == status_filter)
        
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        value = result.scalar()
        return value if value is not None else Decimal('0.0')

    def sum_amount_paid(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        status_filter: Optional[str] = None
    ) -> Decimal:
        """
        Sum amount_paid for a student within school.
        NO business logic interpretation (pure DB sum).
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = select(func.sum(self.model.amount_paid)).where(
            self.model.school_id == school_id,
            self.model.student_id == student_id
        )
        
        if status_filter:
            stmt = stmt.where(self.model.status == status_filter)
        
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        value = result.scalar()
        return value if value is not None else Decimal('0.0')

    def sum_amount_due_school_wide(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: Optional[UUID] = None,
        status_filter: Optional[str] = None
    ) -> Decimal:
        """
        Sum amount_due across all students in school.
        NO business logic interpretation (pure DB sum).
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = select(func.sum(self.model.amount_due)).where(
            self.model.school_id == school_id
        )
        
        if academic_year_id:
            stmt = stmt.where(self.model.academic_year_id == academic_year_id)
        
        if status_filter:
            stmt = stmt.where(self.model.status == status_filter)
        
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        value = result.scalar()
        return value if value is not None else Decimal('0.0')

    # -----------------------------------------
    # Soft Delete Operations
    # -----------------------------------------

    def soft_delete(
        self,
        db: Session,
        school_id: UUID,
        fee_id: UUID
    ) -> bool:
        """
        Soft delete fee record.
        Scoped to school_id for tenant safety.
        Returns True if successful.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.id == fee_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        record = result.scalar_one_or_none()

        if record:
            record.is_deleted = True
            db.flush()
            return True
        return False

    def soft_delete_student_scoped(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        fee_id: UUID
    ) -> bool:
        """
        Soft delete fee record scoped to school and student.
        Maximum safety for sensitive operations.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.id == fee_id,
                self.model.school_id == school_id,
                self.model.student_id == student_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        record = result.scalar_one_or_none()

        if record:
            record.is_deleted = True
            db.flush()
            return True
        return False

    def restore(
        self,
        db: Session,
        school_id: UUID,
        fee_id: UUID
    ) -> bool:
        """
        Restore soft-deleted fee record.
        Scoped to school_id.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == fee_id,
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        record = result.scalar_one_or_none()

        if record:
            record.is_deleted = False
            db.flush()
            return True
        return False

    # -----------------------------------------
    # Bulk Operations (Atomic, Index-Aware)
    # -----------------------------------------

    def bulk_update_status(
        self,
        db: Session,
        school_id: UUID,
        fee_ids: List[UUID],
        new_status: str
    ) -> int:
        """
        Bulk update status for multiple fee records.
        Atomic update statement scoped by school_id.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(fee_ids),
                self.model.is_deleted.is_(False)
            )
            .values(status=new_status)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_by_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        updates: Dict[str, Any]
    ) -> int:
        """
        Bulk update selected mutable fields for a student's fee records.
        Strictly whitelisted fields only.
        Prevents mutation of identifiers, tenant keys, or financial base values.
        Returns count of updated rows.
        """

        # Whitelisted mutable fields ONLY
        ALLOWED_FIELDS = {
            "status",
            "amount_paid",
            "waived_reason",
            "due_date"
        }

        # Filter updates to allowed fields only
        safe_updates = {
            key: value
            for key, value in updates.items()
            if key in ALLOWED_FIELDS
        }

        # If nothing valid to update, exit early
        if not safe_updates:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id,
                self.model.is_deleted.is_(False)
            )
            .values(**safe_updates)
        )

        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0