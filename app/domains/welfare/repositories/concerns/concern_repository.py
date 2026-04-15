# welfare/repositories/complaints/concern_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from repositories.base import SchoolScopedRepository
from welfare.models.complaints import Concern


class ConcernRepository(SchoolScopedRepository[Concern]):
    """
    Repository for Concern model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    Soft-delete aware (Concern model has is_deleted).
    Zero business logic, zero validation, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(Concern)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        school_id: UUID,
        concern_id: UUID
    ) -> Optional[Concern]:
        """
        Retrieve concern by ID scoped to school.
        Prevents horizontal privilege escalation.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == concern_id,
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
        concern_id: UUID
    ) -> Optional[Concern]:
        """
        Retrieve concern by ID scoped to school and student.
        Maximum safety for sensitive operations.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == concern_id,
                self.model.school_id == school_id,
                self.model.student_id == student_id
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
    ) -> List[Concern]:
        """
        List all concerns within school tenant.
        Deterministic ordering: reported_at DESC, id DESC.
        Soft-delete filtered (excludes deleted).
        """
        stmt = (
            select(self.model)
            .where(self.model.school_id == school_id)
            .order_by(
                self.model.reported_at.desc(),
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
    ) -> List[Concern]:
        """
        List concerns for a student within school tenant.
        Uses index on student_id.
        Deterministic ordering: reported_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id
            )
            .order_by(
                self.model.reported_at.desc(),
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
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Concern]:
        """
        List concerns by status within school tenant.
        Uses index on status.
        Deterministic ordering: reported_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.status == status
            )
            .order_by(
                self.model.reported_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_type(
        self,
        db: Session,
        school_id: UUID,
        concern_type: Any,  # ConcernType enum
        skip: int = 0,
        limit: int = 100
    ) -> List[Concern]:
        """
        List concerns by type within school tenant.
        Uses index on type.
        Deterministic ordering: reported_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.type == concern_type
            )
            .order_by(
                self.model.reported_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_reporter(
        self,
        db: Session,
        school_id: UUID,
        reported_by_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Concern]:
        """
        List concerns by reporter within school tenant.
        Deterministic ordering: reported_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.reported_by_id == reported_by_id
            )
            .order_by(
                self.model.reported_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_date_range(
        self,
        db: Session,
        school_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[Concern]:
        """
        List concerns within date range.
        Index-friendly filtering on reported_at.
        Deterministic ordering: reported_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.reported_at >= start_date,
                self.model.reported_at <= end_date
            )
            .order_by(
                self.model.reported_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_severity(
        self,
        db: Session,
        school_id: UUID,
        severity: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Concern]:
        """
        List concerns by severity within school tenant.
        Deterministic ordering: reported_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.severity == severity
            )
            .order_by(
                self.model.reported_at.desc(),
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
    ) -> List[Concern]:
        """
        List soft-deleted concerns within school tenant.
        Does NOT apply soft-delete filter (explicitly includes deleted).
        Deterministic ordering: reported_at DESC, id DESC.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
            .order_by(
                self.model.reported_at.desc(),
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
        concern_id: UUID
    ) -> Optional[Concern]:
        """
        Lock concern for update.
        Scoped to school_id for tenant safety.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == concern_id,
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
        concern_id: UUID
    ) -> Optional[Concern]:
        """
        Lock concern for update scoped to school and student.
        Maximum concurrency safety for sensitive mutation.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == concern_id,
                self.model.school_id == school_id,
                self.model.student_id == student_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_by_student_for_update(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID
    ) -> List[Concern]:
        """
        Lock all concerns for a student.
        Used for batch operations.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id
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
        concern_id: UUID
    ) -> bool:
        """
        Efficient existence check for concern by ID.
        Soft-delete filtered.
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == concern_id,
                self.model.school_id == school_id
            )
            .limit(1)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_by_id_student_scoped(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        concern_id: UUID
    ) -> bool:
        """
        Efficient existence check for concern by ID scoped to student.
        Soft-delete filtered.
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == concern_id,
                self.model.school_id == school_id,
                self.model.student_id == student_id
            )
            .limit(1)
        )
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
        Count concerns within school.
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
        Count concerns for a student within school.
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

    def count_by_status(
        self,
        db: Session,
        school_id: UUID,
        status: str
    ) -> int:
        """
        Count concerns by status within school.
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

    def count_by_type(
        self,
        db: Session,
        school_id: UUID,
        concern_type: Any  # ConcernType enum
    ) -> int:
        """
        Count concerns by type within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.type == concern_type
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_severity(
        self,
        db: Session,
        school_id: UUID,
        severity: str
    ) -> int:
        """
        Count concerns by severity within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.severity == severity
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
        Count soft-deleted concerns within school.
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
        concern_id: UUID
    ) -> bool:
        """
        Soft delete concern record.
        Scoped to school_id for tenant safety.
        Returns True if successful.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.id == concern_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        concern = result.scalar_one_or_none()

        if concern:
            concern.is_deleted = True
            concern.deleted_at = now
            db.flush()
            return True
        return False

    def restore(
        self,
        db: Session,
        school_id: UUID,
        concern_id: UUID
    ) -> bool:
        """
        Restore soft-deleted concern record.
        Scoped to school_id.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == concern_id,
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        concern = result.scalar_one_or_none()

        if concern:
            concern.is_deleted = False
            concern.deleted_at = None
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
        concern_ids: List[UUID],
        new_status: str
    ) -> int:
        """
        Bulk update status for multiple concerns.
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not concern_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(concern_ids),
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
        Bulk update concerns for a student.
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

    def bulk_soft_delete_by_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID
    ) -> int:
        """
        Bulk soft delete all concerns for a student.
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
            .values(is_deleted=True, deleted_at=now)
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
        Bulk restore all soft-deleted concerns for a student.
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