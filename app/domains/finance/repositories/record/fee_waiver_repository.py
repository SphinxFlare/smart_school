# finance/repositories/record/fee_waiver_repository.py


from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update, Any
from decimal import Decimal

from repositories.base import SchoolScopedRepository
from finance.models.record import FeeWaiver


class FeeWaiverRepository(SchoolScopedRepository[FeeWaiver]):
    """
    Repository for FeeWaiver model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    Zero approval logic, zero status transitions, zero amount validations.
    """

    def __init__(self):
        super().__init__(FeeWaiver)

    # -----------------------------------------
    # Student-Scoped Listing
    # -----------------------------------------

    def list_by_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeeWaiver]:
        """
        List waivers by student within school tenant.
        Deterministic ordering: created_at DESC, id DESC.
        Soft-delete filtered.
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
    ) -> List[FeeWaiver]:
        """
        List waivers by specific student fee record within school tenant.
        Deterministic ordering: created_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_fee_id == student_fee_id
            )
            .order_by(
                self.model.created_at.desc(),
                self.model.id.desc()
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
    ) -> List[FeeWaiver]:
        """
        Filter waivers by status within school tenant.
        Uses index on status.
        Deterministic ordering: created_at DESC, id DESC.
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
                self.model.created_at.desc(),
                self.model.id.desc()
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
    ) -> List[FeeWaiver]:
        """
        Filter waivers by status across all students in school.
        Deterministic ordering: created_at DESC, id DESC.
        Soft-delete filtered.
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
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def filter_by_date_range(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeeWaiver]:
        """
        Filter waivers by date range (created_at) within school tenant.
        Index-friendly filtering (no functions on column).
        Deterministic ordering: created_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id,
                self.model.created_at >= start_date,
                self.model.created_at <= end_date
            )
            .order_by(
                self.model.created_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Existence Checks
    # -----------------------------------------

    def exists_pending_by_student_fee(
        self,
        db: Session,
        school_id: UUID,
        student_fee_id: UUID
    ) -> bool:
        """
        Efficient existence check for pending waivers per student_fee_id.
        Uses select(id).limit(1) style for performance.
        Tenant-safe with school_id filter.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.school_id == school_id,
                self.model.student_fee_id == student_fee_id,
                self.model.status == 'pending'
            )
            .limit(1)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_by_id_school_scoped(
        self,
        db: Session,
        school_id: UUID,
        waiver_id: UUID
    ) -> bool:
        """
        Existence check for waiver by ID within school tenant.
        Efficient count-based check.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.id == waiver_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        count = result.scalar() or 0
        return count > 0

    # -----------------------------------------
    # Row Locking
    # -----------------------------------------

    def lock_for_update(
        self,
        db: Session,
        school_id: UUID,
        waiver_id: UUID
    ) -> Optional[FeeWaiver]:
        """
        Lock waiver for update (approval/rejection workflows).
        Scoped to school_id for tenant safety.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == waiver_id,
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
        waiver_id: UUID
    ) -> Optional[FeeWaiver]:
        """
        Lock waiver for update scoped to school and student.
        Maximum concurrency safety.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == waiver_id,
                self.model.school_id == school_id,
                self.model.student_id == student_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_by_student_fee_for_update(
        self,
        db: Session,
        school_id: UUID,
        student_fee_id: UUID
    ) -> Optional[FeeWaiver]:
        """
        Lock waiver by student_fee_id for update.
        Tenant-safe locking.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_fee_id == student_fee_id
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
        Count waivers by status for a student within school.
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
        Count waivers by status across all students in school.
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

    def sum_amount_waived(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        status_filter: Optional[str] = None
    ) -> Decimal:
        """
        Sum amount_waived for a student within school.
        NO business logic interpretation (pure DB sum).
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = select(func.sum(self.model.amount_waived)).where(
            self.model.school_id == school_id,
            self.model.student_id == student_id
        )
        
        if status_filter:
            stmt = stmt.where(self.model.status == status_filter)
        
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        value = result.scalar()
        return value if value is not None else Decimal('0.0')

    def sum_amount_waived_school_wide(
        self,
        db: Session,
        school_id: UUID,
        status_filter: Optional[str] = None
    ) -> Decimal:
        """
        Sum amount_waived across all students in school.
        NO business logic interpretation (pure DB sum).
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = select(func.sum(self.model.amount_waived)).where(
            self.model.school_id == school_id
        )
        
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
        waiver_id: UUID
    ) -> bool:
        """
        Soft delete waiver record.
        Scoped to school_id for tenant safety.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.id == waiver_id,
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
        waiver_id: UUID
    ) -> bool:
        """
        Soft delete waiver record scoped to school and student.
        Maximum safety for sensitive operations.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.id == waiver_id,
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
        waiver_id: UUID
    ) -> bool:
        """
        Restore soft-deleted waiver record.
        Scoped to school_id.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == waiver_id,
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
        waiver_ids: List[UUID],
        new_status: str
    ) -> int:
        """
        Bulk update status for multiple waiver records.
        Atomic update statement scoped by school_id.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(waiver_ids),
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
        Bulk update selected mutable fields for a student's waiver records.
        Strict whitelist enforcement.
        Prevents mutation of tenant keys, identifiers, and financial base values.
        Returns count of updated rows.
        """

        # Whitelisted mutable fields ONLY
        ALLOWED_FIELDS = {
            "status",
            "rejection_reason"
        }

        safe_updates = {
            key: value
            for key, value in updates.items()
            if key in ALLOWED_FIELDS
        }

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