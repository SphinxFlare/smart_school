# transport/repositories/allocations/student_transport_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from repositories.base import SchoolScopedRepository
from transport.models.allocations import StudentTransport


class StudentTransportRepository(SchoolScopedRepository[StudentTransport]):
    """
    Repository for StudentTransport model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    Soft-delete aware (StudentTransport model has is_deleted).
    Zero business logic, zero overlap validation, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(StudentTransport)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        school_id: UUID,
        transport_id: UUID
    ) -> Optional[StudentTransport]:
        """
        Retrieve student transport by ID scoped to school.
        Prevents horizontal privilege escalation.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == transport_id,
                self.model.school_id == school_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Listing Methods
    # -----------------------------------------

    def list_by_school(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentTransport]:
        """
        List all student transport records within school tenant.
        Deterministic ordering: created_at DESC, id DESC.
        Soft-delete filtered (excludes deleted).
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
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentTransport]:
        """
        List student transport records for a student within school tenant.
        Deterministic ordering: effective_from ASC, id ASC (sequence matters).
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id
            )
            .order_by(
                self.model.effective_from.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
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
    ) -> List[StudentTransport]:
        """
        List student transport records for a student within academic year.
        Deterministic ordering: effective_from ASC, id ASC (sequence matters).
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
                self.model.effective_from.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_bus_assignment(
        self,
        db: Session,
        school_id: UUID,
        bus_assignment_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentTransport]:
        """
        List student transport records for a bus assignment.
        Deterministic ordering: created_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.bus_assignment_id == bus_assignment_id
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

    def list_by_academic_year(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentTransport]:
        """
        List student transport records for an academic year within school.
        Deterministic ordering: created_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.academic_year_id == academic_year_id
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

    def list_active_transports(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentTransport]:
        """
        List active student transport records within school tenant.
        Deterministic ordering: created_at DESC, id DESC.
        Soft-delete filtered.
        """
        from types.transport import StudentTransportStatus
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.status == StudentTransportStatus.ACTIVE
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

    def list_deleted(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentTransport]:
        """
        List soft-deleted student transport records within school tenant.
        Does NOT apply soft-delete filter (explicitly includes deleted).
        Deterministic ordering: created_at DESC, id DESC.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
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

    # -----------------------------------------
    # Row Locking
    # -----------------------------------------

    def lock_for_update(
        self,
        db: Session,
        school_id: UUID,
        transport_id: UUID
    ) -> Optional[StudentTransport]:
        """
        Lock student transport for update.
        Scoped to school_id for tenant safety.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == transport_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_by_student_and_academic_year_for_update(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        academic_year_id: UUID
    ) -> Optional[StudentTransport]:
        """
        Lock student transport by student and academic year.
        Respects composite uniqueness constraint.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id,
                self.model.academic_year_id == academic_year_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_all_transports_by_student_for_update(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        academic_year_id: Optional[UUID] = None
    ) -> List[StudentTransport]:
        """
        Lock all transport records for a student within academic year.
        Used for reassignment operations.
        Soft-delete filtered.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.student_id == student_id
        )
        
        if academic_year_id:
            stmt = stmt.where(self.model.academic_year_id == academic_year_id)
        
        stmt = stmt.with_for_update()
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def lock_all_transports_by_assignment_for_update(
        self,
        db: Session,
        school_id: UUID,
        bus_assignment_id: UUID
    ) -> List[StudentTransport]:
        """
        Lock all transport records for a bus assignment.
        Used for reassignment operations.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.bus_assignment_id == bus_assignment_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Existence Checks
    # -----------------------------------------

    def exists_by_id(
        self,
        db: Session,
        school_id: UUID,
        transport_id: UUID
    ) -> bool:
        """
        Efficient existence check for student transport by ID.
        Soft-delete filtered.
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == transport_id,
                self.model.school_id == school_id
            )
            .limit(1)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_by_composite_unique(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        academic_year_id: UUID,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for composite uniqueness constraint.
        Respects (school_id, student_id, academic_year_id).
        Optional exclude_id for update operations.
        Soft-delete filtered.
        Uses select(id).limit(1) pattern.
        """
        stmt = select(self.model.id).where(
            self.model.school_id == school_id,
            self.model.student_id == student_id,
            self.model.academic_year_id == academic_year_id
        )
        
        if exclude_id is not None:
            stmt = stmt.where(self.model.id != exclude_id)
        
        stmt = stmt.limit(1)
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    # -----------------------------------------
    # Aggregations (Null-Safe)
    # -----------------------------------------

    def count_by_school(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count student transport records within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.school_id == school_id)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID
    ) -> int:
        """
        Count student transport records for a student within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_bus_assignment(
        self,
        db: Session,
        school_id: UUID,
        bus_assignment_id: UUID
    ) -> int:
        """
        Count student transport records for a bus assignment.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.bus_assignment_id == bus_assignment_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_academic_year(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID
    ) -> int:
        """
        Count student transport records for an academic year within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.academic_year_id == academic_year_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_deleted(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count soft-deleted student transport records within school.
        Null-safe aggregation.
        Does NOT apply soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # Soft Delete Operations
    # -----------------------------------------

    def soft_delete(
        self,
        db: Session,
        school_id: UUID,
        transport_id: UUID
    ) -> bool:
        """
        Soft delete student transport record.
        Scoped to school_id for tenant safety.
        Returns True if successful.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.id == transport_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        transport = result.scalar_one_or_none()

        if transport:
            transport.is_deleted = True
            db.flush()
            return True
        return False

    def restore(
        self,
        db: Session,
        school_id: UUID,
        transport_id: UUID
    ) -> bool:
        """
        Restore soft-deleted student transport record.
        Scoped to school_id.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == transport_id,
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        transport = result.scalar_one_or_none()

        if transport:
            transport.is_deleted = False
            db.flush()
            return True
        return False

    # -----------------------------------------
    # Bulk Operations (Atomic, Empty Guards)
    # -----------------------------------------

    def bulk_update_status(
        self,
        db: Session,
        school_id: UUID,
        transport_ids: List[UUID],
        new_status: Any
    ) -> int:
        """
        Bulk update status for multiple student transport records.
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not transport_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(transport_ids),
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
        Bulk update student transport records for a specific student.
        Atomic update statement scoped by school_id and student_id.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not updates:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id,
                self.model.is_deleted.is_(False)
            )
            .values(**updates)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_by_bus_assignment(
        self,
        db: Session,
        school_id: UUID,
        bus_assignment_id: UUID,
        updates: Dict[str, Any]
    ) -> int:
        """
        Bulk update student transport records for a bus assignment.
        Atomic update statement scoped by school_id and bus_assignment_id.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not updates:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.bus_assignment_id == bus_assignment_id,
                self.model.is_deleted.is_(False)
            )
            .values(**updates)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_soft_delete_by_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID
    ) -> int:
        """
        Bulk soft delete all student transport records for a student.
        Atomic update statement scoped by school_id.
        Returns count of updated rows.
        """
        now = datetime.utcnow()
        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id,
                self.model.is_deleted.is_(False)
            )
            .values(is_deleted=True)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_restore_by_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID
    ) -> int:
        """
        Bulk restore all soft-deleted student transport records for a student.
        Atomic update statement scoped by school_id.
        Returns count of updated rows.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id,
                self.model.is_deleted.is_(True)
            )
            .values(is_deleted=False, deleted_at=None)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0
    

    def lock_by_assignment_and_year_for_update(
        self,
        db: Session,
        school_id: UUID,
        bus_assignment_id: UUID,
        academic_year_id: UUID
    ) -> List[StudentTransport]:

        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.bus_assignment_id == bus_assignment_id,
                self.model.academic_year_id == academic_year_id
            )
            .with_for_update()
        )

        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())