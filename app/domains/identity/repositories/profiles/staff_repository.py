# identity/repositories/profiles/staff_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from repositories.base import SchoolScopedRepository
from identity.models.profiles import StaffMember


class StaffRepository(SchoolScopedRepository[StaffMember]):
    """
    Repository for StaffMember model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    Soft-delete aware (StaffMember model has is_deleted).
    Zero business logic, zero employment validation, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(StaffMember)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        school_id: UUID,
        staff_id: UUID
    ) -> Optional[StaffMember]:
        """
        Retrieve staff member by ID scoped to school.
        Prevents horizontal privilege escalation.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == staff_id,
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
    ) -> Optional[StaffMember]:
        """
        Retrieve staff member by user_id scoped to school.
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

    def get_by_employee_id(
        self,
        db: Session,
        school_id: UUID,
        employee_id: str
    ) -> Optional[StaffMember]:
        """
        Retrieve staff member by employee_id scoped to school.
        Respects unique constraint (school_id, employee_id).
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.employee_id == employee_id
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
    ) -> List[StaffMember]:
        """
        List all staff members within school tenant.
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

    def list_by_department(
        self,
        db: Session,
        school_id: UUID,
        department: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[StaffMember]:
        """
        List staff members by department within school tenant.
        Deterministic ordering: created_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.department == department
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

    def list_by_position(
        self,
        db: Session,
        school_id: UUID,
        position: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[StaffMember]:
        """
        List staff members by position within school tenant.
        Deterministic ordering: created_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.position == position
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
    ) -> List[StaffMember]:
        """
        List soft-deleted staff members within school tenant.
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
        staff_id: UUID
    ) -> Optional[StaffMember]:
        """
        Lock staff member for update (employment status updates).
        Scoped to school_id for tenant safety.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == staff_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_for_employment_status(
        self,
        db: Session,
        school_id: UUID,
        staff_id: UUID
    ) -> Optional[StaffMember]:
        """
        Lock staff member for employment status update operations.
        Maximum concurrency safety for sensitive mutation.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == staff_id,
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
        staff_id: UUID
    ) -> bool:
        """
        Efficient existence check for staff member by ID.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == staff_id,
                self.model.school_id == school_id
            )
            .limit(1)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_employee_id(
        self,
        db: Session,
        school_id: UUID,
        employee_id: str,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for employee_id within school.
        Respects unique constraint (school_id, employee_id).
        Optional exclude_id for update operations.
        Soft-delete filtered.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.school_id == school_id,
            self.model.employee_id == employee_id
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
        Count staff members within school.
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

    def count_by_department(
        self,
        db: Session,
        school_id: UUID,
        department: str
    ) -> int:
        """
        Count staff members by department within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.department == department
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_position(
        self,
        db: Session,
        school_id: UUID,
        position: str
    ) -> int:
        """
        Count staff members by position within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.position == position
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
        Count soft-deleted staff members within school.
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
        staff_id: UUID
    ) -> bool:
        """
        Soft delete staff member record.
        Scoped to school_id for tenant safety.
        Returns True if successful.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == staff_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        staff = result.scalar_one_or_none()

        if staff:
            staff.is_deleted = True
            db.flush()
            return True
        return False

    def restore(
        self,
        db: Session,
        school_id: UUID,
        staff_id: UUID
    ) -> bool:
        """
        Restore soft-deleted staff member record.
        Scoped to school_id.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == staff_id,
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        staff = result.scalar_one_or_none()

        if staff:
            staff.is_deleted = False
            db.flush()
            return True
        return False

    # -----------------------------------------
    # Bulk Operations (Atomic, Subquery-Based)
    # -----------------------------------------

    def bulk_activate(
        self,
        db: Session,
        school_id: UUID,
        staff_ids: List[UUID]
    ) -> int:
        """
        Bulk activate staff members (restore from soft delete).
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Returns count of updated rows.
        """
        if not staff_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(staff_ids),
                self.model.is_deleted.is_(True)
            )
            .values(is_deleted=False)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_position(
        self,
        db: Session,
        school_id: UUID,
        staff_ids: List[UUID],
        position: str
    ) -> int:
        """
        Bulk update position for multiple staff members.
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not staff_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(staff_ids),
                self.model.is_deleted.is_(False)
            )
            .values(position=position)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_department(
        self,
        db: Session,
        school_id: UUID,
        staff_ids: List[UUID],
        department: str
    ) -> int:
        """
        Bulk update department for multiple staff members.
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not staff_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(staff_ids),
                self.model.is_deleted.is_(False)
            )
            .values(department=department)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0