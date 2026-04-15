# identity/repositories/profiles/student_parent_repository.py


from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, func, update

from repositories.base import SchoolScopedRepository
from identity.models.profiles import StudentParent, Student, Parent


class StudentParentRepository(SchoolScopedRepository[StudentParent]):
    """
    Repository for StudentParent model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation by joining both Student and Parent.
    Verifies both Student and Parent belong to the same school_id.
    NOTE: StudentParent model does NOT have is_deleted, so no soft-delete filtering.
    Zero business logic, zero guardian count rules, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(StudentParent)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        school_id: UUID,
        student_parent_id: UUID
    ) -> Optional[StudentParent]:
        """
        Retrieve student-parent link by ID scoped to school.
        Joins with Student and Parent to verify tenant isolation.
        """
        student_alias = aliased(Student)
        parent_alias = aliased(Parent)
        stmt = (
            select(self.model)
            .join(student_alias, self.model.student_id == student_alias.id)
            .join(parent_alias, self.model.parent_id == parent_alias.id)
            .where(
                self.model.id == student_parent_id,
                student_alias.school_id == school_id,
                parent_alias.school_id == school_id
            )
        )
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
    ) -> List[StudentParent]:
        """
        List parent links for a student within school tenant.
        Joins with Student and Parent to verify tenant isolation.
        Deterministic ordering: created_at DESC, id DESC.
        """
        student_alias = aliased(Student)
        parent_alias = aliased(Parent)
        stmt = (
            select(self.model)
            .join(student_alias, self.model.student_id == student_alias.id)
            .join(parent_alias, self.model.parent_id == parent_alias.id)
            .where(
                self.model.student_id == student_id,
                student_alias.school_id == school_id,
                parent_alias.school_id == school_id
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

    def list_by_parent(
        self,
        db: Session,
        school_id: UUID,
        parent_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentParent]:
        """
        List student links for a parent within school tenant.
        Joins with Student and Parent to verify tenant isolation.
        Deterministic ordering: created_at DESC, id DESC.
        """
        student_alias = aliased(Student)
        parent_alias = aliased(Parent)
        stmt = (
            select(self.model)
            .join(student_alias, self.model.student_id == student_alias.id)
            .join(parent_alias, self.model.parent_id == parent_alias.id)
            .where(
                self.model.parent_id == parent_id,
                student_alias.school_id == school_id,
                parent_alias.school_id == school_id
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

    def list_primary_guardians(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentParent]:
        """
        List primary guardian links for a student within school tenant.
        Filters by is_primary=True.
        Joins with Student and Parent to verify tenant isolation.
        Deterministic ordering: created_at DESC, id DESC.
        """
        student_alias = aliased(Student)
        parent_alias = aliased(Parent)
        stmt = (
            select(self.model)
            .join(student_alias, self.model.student_id == student_alias.id)
            .join(parent_alias, self.model.parent_id == parent_alias.id)
            .where(
                self.model.student_id == student_id,
                self.model.is_primary.is_(True),
                student_alias.school_id == school_id,
                parent_alias.school_id == school_id
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

    def list_by_school(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentParent]:
        """
        List all student-parent links within school tenant.
        Joins with Student and Parent to verify tenant isolation.
        Deterministic ordering: created_at DESC, id DESC.
        """
        student_alias = aliased(Student)
        parent_alias = aliased(Parent)
        stmt = (
            select(self.model)
            .join(student_alias, self.model.student_id == student_alias.id)
            .join(parent_alias, self.model.parent_id == parent_alias.id)
            .where(
                student_alias.school_id == school_id,
                parent_alias.school_id == school_id
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
        student_parent_id: UUID
    ) -> Optional[StudentParent]:
        """
        Lock student-parent link for update (assignment mutation).
        Joins with Student and Parent to verify tenant isolation.
        """
        student_alias = aliased(Student)
        parent_alias = aliased(Parent)
        stmt = (
            select(self.model)
            .join(student_alias, self.model.student_id == student_alias.id)
            .join(parent_alias, self.model.parent_id == parent_alias.id)
            .where(
                self.model.id == student_parent_id,
                student_alias.school_id == school_id,
                parent_alias.school_id == school_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_by_student_and_parent_for_update(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        parent_id: UUID
    ) -> Optional[StudentParent]:
        """
        Lock student-parent link by student and parent for update.
        Joins with Student and Parent to verify tenant isolation.
        """
        student_alias = aliased(Student)
        parent_alias = aliased(Parent)
        stmt = (
            select(self.model)
            .join(student_alias, self.model.student_id == student_alias.id)
            .join(parent_alias, self.model.parent_id == parent_alias.id)
            .where(
                self.model.student_id == student_id,
                self.model.parent_id == parent_id,
                student_alias.school_id == school_id,
                parent_alias.school_id == school_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Existence Checks
    # -----------------------------------------

    def exists_by_id(
        self,
        db: Session,
        school_id: UUID,
        student_parent_id: UUID
    ) -> bool:
        """
        Efficient existence check for student-parent link by ID.
        Joins with Student and Parent to verify tenant isolation.
        """
        student_alias = aliased(Student)
        parent_alias = aliased(Parent)
        stmt = (
            select(self.model.id)
            .join(student_alias, self.model.student_id == student_alias.id)
            .join(parent_alias, self.model.parent_id == parent_alias.id)
            .where(
                self.model.id == student_parent_id,
                student_alias.school_id == school_id,
                parent_alias.school_id == school_id
            )
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_student_parent_pair(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        parent_id: UUID,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for student-parent pair within school.
        Respects unique constraint (student_id, parent_id).
        Optional exclude_id for update operations.
        Joins with Student and Parent to verify tenant isolation.
        """
        student_alias = aliased(Student)
        parent_alias = aliased(Parent)
        stmt = select(func.count(self.model.id)).join(
            student_alias, self.model.student_id == student_alias.id
        ).join(
            parent_alias, self.model.parent_id == parent_alias.id
        ).where(
            self.model.student_id == student_id,
            self.model.parent_id == parent_id,
            student_alias.school_id == school_id,
            parent_alias.school_id == school_id
        )
        
        if exclude_id is not None:
            stmt = stmt.where(self.model.id != exclude_id)
        
        result = db.execute(stmt)
        count = result.scalar() or 0
        return count > 0

    # -----------------------------------------
    # Aggregations (Null-Safe)
    # -----------------------------------------

    def count_by_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID
    ) -> int:
        """
        Count parent links for a student within school.
        Null-safe aggregation.
        Joins with Student and Parent to verify tenant isolation.
        """
        student_alias = aliased(Student)
        parent_alias = aliased(Parent)
        stmt = (
            select(func.count(self.model.id))
            .join(student_alias, self.model.student_id == student_alias.id)
            .join(parent_alias, self.model.parent_id == parent_alias.id)
            .where(
                self.model.student_id == student_id,
                student_alias.school_id == school_id,
                parent_alias.school_id == school_id
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_parent(
        self,
        db: Session,
        school_id: UUID,
        parent_id: UUID
    ) -> int:
        """
        Count student links for a parent within school.
        Null-safe aggregation.
        Joins with Student and Parent to verify tenant isolation.
        """
        student_alias = aliased(Student)
        parent_alias = aliased(Parent)
        stmt = (
            select(func.count(self.model.id))
            .join(student_alias, self.model.student_id == student_alias.id)
            .join(parent_alias, self.model.parent_id == parent_alias.id)
            .where(
                self.model.parent_id == parent_id,
                student_alias.school_id == school_id,
                parent_alias.school_id == school_id
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_primary_guardians(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID
    ) -> int:
        """
        Count primary guardian links for a student within school.
        Null-safe aggregation.
        Joins with Student and Parent to verify tenant isolation.
        """
        student_alias = aliased(Student)
        parent_alias = aliased(Parent)
        stmt = (
            select(func.count(self.model.id))
            .join(student_alias, self.model.student_id == student_alias.id)
            .join(parent_alias, self.model.parent_id == parent_alias.id)
            .where(
                self.model.student_id == student_id,
                self.model.is_primary.is_(True),
                student_alias.school_id == school_id,
                parent_alias.school_id == school_id
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # Assignment Operations
    # -----------------------------------------

    def assign_parent_to_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        parent_id: UUID,
        relationship: str,
        is_primary: bool = False
    ) -> StudentParent:
        """
        Assign parent to student.
        Verifies tenant isolation via Student and Parent joins.
        Creates new assignment or updates existing one.
        """
        existing = self.lock_by_student_and_parent_for_update(
            db, school_id, student_id, parent_id
        )

        if existing:
            existing.relationship = relationship
            existing.is_primary = is_primary
            db.flush()
            return existing
        else:
            student_parent = StudentParent(
                school_id=school_id,
                student_id=student_id,
                parent_id=parent_id,
                relationship=relationship,
                is_primary=is_primary
            )
            db.add(student_parent)
            db.flush()
            return student_parent

    def remove_parent_from_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        parent_id: UUID
    ) -> bool:
        """
        Remove parent from student (hard delete - no soft delete on model).
        Verifies tenant isolation via Student and Parent joins.
        Returns True if successful.
        """
        student_parent = self.lock_by_student_and_parent_for_update(
            db, school_id, student_id, parent_id
        )

        if student_parent:
            db.delete(student_parent)
            db.flush()
            return True
        return False

    # -----------------------------------------
    # Bulk Operations (Atomic, Subquery-Based)
    # -----------------------------------------

    def bulk_set_primary_guardian(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        parent_id: UUID
    ) -> int:
        """
        Bulk set primary guardian for a student.
        First clears all existing primary flags, then sets new one.
        Atomic update statements with tenant verification via subqueries.
        Returns count of updated rows.
        """
        # Subquery to enforce tenant isolation on student
        student_subq = (
            select(Student.id)
            .where(
                Student.id == student_id,
                Student.school_id == school_id
            )
        )

        # Clear existing primary flags
        clear_stmt = (
            update(self.model)
            .where(
                self.model.student_id.in_(student_subq),
                self.model.is_primary.is_(True)
            )
            .values(is_primary=False)
        )
        db.execute(clear_stmt)

        # Subquery to enforce tenant isolation on parent
        parent_subq = (
            select(Parent.id)
            .where(
                Parent.id == parent_id,
                Parent.school_id == school_id
            )
        )

        # Set new primary guardian
        set_stmt = (
            update(self.model)
            .where(
                self.model.student_id.in_(student_subq),
                self.model.parent_id.in_(parent_subq)
            )
            .values(is_primary=True)
        )

        result = db.execute(set_stmt)
        db.flush()
        return result.rowcount or 0


    def bulk_reassign_parent(
        self,
        db: Session,
        school_id: UUID,
        old_parent_id: UUID,
        new_parent_id: UUID,
        student_ids: List[UUID]
    ) -> int:
        """
        Bulk reassign parent for multiple students.
        Atomic update statement with tenant verification via subqueries.
        Empty-list guard included.
        Returns count of updated rows.
        """
        if not student_ids:
            return 0

        student_subq = (
            select(Student.id)
            .where(
                Student.id.in_(student_ids),
                Student.school_id == school_id
            )
        )

        old_parent_subq = (
            select(Parent.id)
            .where(
                Parent.id == old_parent_id,
                Parent.school_id == school_id
            )
        )

        new_parent_subq = (
            select(Parent.id)
            .where(
                Parent.id == new_parent_id,
                Parent.school_id == school_id
            )
        )

        stmt = (
            update(self.model)
            .where(
                self.model.student_id.in_(student_subq),
                self.model.parent_id.in_(old_parent_subq)
            )
            .values(parent_id=new_parent_subq.scalar_subquery())
        )

        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0