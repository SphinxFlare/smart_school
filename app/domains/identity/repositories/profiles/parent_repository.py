# identity/repositories/profiles/parent_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, func, update

from repositories.base import SchoolScopedRepository
from identity.models.profiles import Parent, StudentParent, Student


class ParentRepository(SchoolScopedRepository[Parent]):
    """
    Repository for Parent model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    Soft-delete aware (Parent model has is_deleted).
    Zero business logic, zero guardian validation, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(Parent)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        school_id: UUID,
        parent_id: UUID
    ) -> Optional[Parent]:
        """
        Retrieve parent by ID scoped to school.
        Prevents horizontal privilege escalation.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == parent_id,
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
    ) -> Optional[Parent]:
        """
        Retrieve parent by user_id scoped to school.
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

    # -----------------------------------------
    # Listing Methods
    # -----------------------------------------

    def list_by_school(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Parent]:
        """
        List all parents within school tenant.
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
    ) -> List[Parent]:
        """
        List parents linked to a student within school tenant.
        Joins with StudentParent with strict school verification.
        Deterministic ordering: created_at DESC, id DESC.
        Soft-delete filtered.
        """

        student_parent_alias = aliased(StudentParent)
        student_alias = aliased(Student)

        stmt = (
            select(self.model)
            .join(student_parent_alias, self.model.id == student_parent_alias.parent_id)
            .join(student_alias, student_parent_alias.student_id == student_alias.id)
            .where(
                self.model.school_id == school_id,
                student_alias.school_id == school_id,
                student_parent_alias.student_id == student_id,
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
    ) -> List[Parent]:
        """
        List soft-deleted parents within school tenant.
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
        parent_id: UUID
    ) -> Optional[Parent]:
        """
        Lock parent for update (profile modification operations).
        Scoped to school_id for tenant safety.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == parent_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_for_profile_modification(
        self,
        db: Session,
        school_id: UUID,
        parent_id: UUID
    ) -> Optional[Parent]:
        """
        Lock parent for profile modification operations.
        Maximum concurrency safety for sensitive mutation.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == parent_id,
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
        parent_id: UUID
    ) -> bool:
        """
        Efficient existence check for parent by ID.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == parent_id,
                self.model.school_id == school_id
            )
            .limit(1)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

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
        Count parents within school.
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
        Count parents linked to a student within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        student_parent_alias = aliased(StudentParent)
        student_alias = aliased(Student)

        stmt = (
            select(func.count(self.model.id))
            .join(student_parent_alias, self.model.id == student_parent_alias.parent_id)
            .join(student_alias, student_parent_alias.student_id == student_alias.id)
            .where(
                self.model.school_id == school_id,
                student_alias.school_id == school_id,
                student_parent_alias.student_id == student_id,
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
        Count soft-deleted parents within school.
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
        parent_id: UUID
    ) -> bool:
        """
        Soft delete parent record.
        Scoped to school_id for tenant safety.
        Returns True if successful.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.id == parent_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        parent = result.scalar_one_or_none()

        if parent:
            parent.is_deleted = True
            db.flush()
            return True
        return False

    def restore(
        self,
        db: Session,
        school_id: UUID,
        parent_id: UUID
    ) -> bool:
        """
        Restore soft-deleted parent record.
        Scoped to school_id.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == parent_id,
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        parent = result.scalar_one_or_none()

        if parent:
            parent.is_deleted = False
            db.flush()
            return True
        return False

    # -----------------------------------------
    # Bulk Operations (Atomic, Subquery-Based)
    # -----------------------------------------

    def bulk_update_occupation(
        self,
        db: Session,
        school_id: UUID,
        parent_ids: List[UUID],
        occupation: str
    ) -> int:
        """
        Bulk update occupation for multiple parents.
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not parent_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(parent_ids),
                self.model.is_deleted.is_(False)
            )
            .values(occupation=occupation)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0