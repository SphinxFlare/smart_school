# identity/repositories/profiles/student_repository.py


from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from repositories.base import SchoolScopedRepository
from identity.models.profiles import Student


class StudentRepository(SchoolScopedRepository[Student]):
    """
    Repository for Student model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    Soft-delete aware (Student model has is_deleted).
    Zero business logic, zero enrollment validation, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(Student)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID
    ) -> Optional[Student]:
        """
        Retrieve student by ID scoped to school.
        Prevents horizontal privilege escalation.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == student_id,
                self.model.school_id == school_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_user_id(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID
    ) -> Optional[Student]:
        """
        Retrieve student by user_id scoped to school.
        Respects unique constraint on user_id.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.user_id == user_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_admission_number(
        self,
        db: Session,
        school_id: UUID,
        admission_number: str
    ) -> Optional[Student]:
        """
        Retrieve student by admission_number scoped to school.
        Respects unique constraint (school_id, admission_number).
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.admission_number == admission_number
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
    ) -> List[Student]:
        """
        List all students within school tenant.
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

    def list_deleted(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Student]:
        """
        List soft-deleted students within school tenant.
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
        student_id: UUID
    ) -> Optional[Student]:
        """
        Lock student for update (profile edit operations).
        Scoped to school_id for tenant safety.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == student_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_for_enrollment_linkage(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID
    ) -> Optional[Student]:
        """
        Lock student for enrollment linkage operations.
        Maximum concurrency safety for sensitive mutation.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == student_id,
                self.model.school_id == school_id
            )
            .with_for_update(skip_locked=False)
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
        student_id: UUID
    ) -> bool:
        """
        Efficient existence check for student by ID.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == student_id,
                self.model.school_id == school_id
            )
            .limit(1)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_admission_number(
        self,
        db: Session,
        school_id: UUID,
        admission_number: str,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for admission_number within school.
        Respects unique constraint (school_id, admission_number).
        Optional exclude_id for update operations.
        Soft-delete filtered.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.school_id == school_id,
            self.model.admission_number == admission_number
        )
        
        if exclude_id is not None:
            stmt = stmt.where(self.model.id != exclude_id)
        
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        count = result.scalar() or 0
        return count > 0

    def exists_user_id(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for user_id within school.
        Respects unique constraint on user_id.
        Optional exclude_id for update operations.
        Soft-delete filtered.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.school_id == school_id,
            self.model.user_id == user_id
        )
        
        if exclude_id is not None:
            stmt = stmt.where(self.model.id != exclude_id)
        
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        count = result.scalar() or 0
        return count > 0

    # -----------------------------------------
    # Aggregations (Null-Safe)
    # -----------------------------------------

    def count_by_school(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count students within school.
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

    def count_deleted(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count soft-deleted students within school.
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
        student_id: UUID
    ) -> bool:
        """
        Soft delete student record.
        Scoped to school_id for tenant safety.
        Returns True if successful.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.id == student_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        student = result.scalar_one_or_none()

        if student:
            student.is_deleted = True
            student.deleted_at = now
            db.flush()
            return True
        return False

    def restore(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID
    ) -> bool:
        """
        Restore soft-deleted student record.
        Scoped to school_id.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == student_id,
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        student = result.scalar_one_or_none()

        if student:
            student.is_deleted = False
            db.flush()
            return True
        return False

    # -----------------------------------------
    # Bulk Operations (Atomic, Subquery-Based)
    # -----------------------------------------

    def bulk_update_emergency_contact(
        self,
        db: Session,
        school_id: UUID,
        student_ids: List[UUID],
        emergency_contact_name: Optional[str] = None,
        emergency_contact_phone: Optional[str] = None
    ) -> int:
        """
        Bulk update emergency contact info for multiple students.
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not student_ids:
            return 0

        values = {}
        if emergency_contact_name is not None:
            values['emergency_contact_name'] = emergency_contact_name
        if emergency_contact_phone is not None:
            values['emergency_contact_phone'] = emergency_contact_phone
        
        if not values:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(student_ids),
                self.model.is_deleted.is_(False)
            )
            .values(**values)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0