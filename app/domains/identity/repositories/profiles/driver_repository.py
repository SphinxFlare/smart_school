# identity/repositories/profiles/driver_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, func, update

from repositories.base import SchoolScopedRepository
from identity.models.profiles import Driver


class DriverRepository(SchoolScopedRepository[Driver]):
    """
    Repository for Driver model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    NOTE: Driver model does NOT have is_deleted, so no soft-delete filtering.
    Zero business logic, zero license validation, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(Driver)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        school_id: UUID,
        driver_id: UUID
    ) -> Optional[Driver]:
        """
        Retrieve driver by ID scoped to school.
        Prevents horizontal privilege escalation.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == driver_id,
                self.model.school_id == school_id
            )
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_staff_member_id(
        self,
        db: Session,
        school_id: UUID,
        staff_member_id: UUID
    ) -> Optional[Driver]:
        """
        Retrieve driver by staff_member_id scoped to school.
        Respects unique constraint on staff_member_id.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.staff_member_id == staff_member_id
            )
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_license_number(
        self,
        db: Session,
        school_id: UUID,
        license_number: str
    ) -> Optional[Driver]:
        """
        Retrieve driver by license_number scoped to school.
        Respects unique constraint (school_id, license_number).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.license_number == license_number
            )
        )
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
    ) -> List[Driver]:
        """
        List all drivers within school tenant.
        Deterministic ordering: created_at DESC, id DESC.
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
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_status(
        self,
        db: Session,
        school_id: UUID,
        status: Any,  # DriverStatus enum
        skip: int = 0,
        limit: int = 100
    ) -> List[Driver]:
        """
        List drivers by status within school tenant.
        Uses index on status.
        Deterministic ordering: created_at DESC, id DESC.
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
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_expiring_licenses(
        self,
        db: Session,
        school_id: UUID,
        before_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[Driver]:
        """
        List drivers with licenses expiring before a date.
        Index-friendly filtering on license_expiry.
        Deterministic ordering: license_expiry ASC, id ASC.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.license_expiry <= before_date
            )
            .order_by(
                self.model.license_expiry.asc(),
                self.model.id.asc()
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
        driver_id: UUID
    ) -> Optional[Driver]:
        """
        Lock driver for update (status/expiry updates).
        Scoped to school_id for tenant safety.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == driver_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_for_status_update(
        self,
        db: Session,
        school_id: UUID,
        driver_id: UUID
    ) -> Optional[Driver]:
        """
        Lock driver for status update operations.
        Maximum concurrency safety for sensitive mutation.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == driver_id,
                self.model.school_id == school_id
            )
            .with_for_update(skip_locked=False)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_for_expiry_update(
        self,
        db: Session,
        school_id: UUID,
        driver_id: UUID
    ) -> Optional[Driver]:
        """
        Lock driver for license expiry update operations.
        Maximum concurrency safety for sensitive mutation.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == driver_id,
                self.model.school_id == school_id
            )
            .with_for_update(skip_locked=False)
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
        driver_id: UUID
    ) -> bool:
        """
        Efficient existence check for driver by ID.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == driver_id,
                self.model.school_id == school_id
            )
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_license_number(
        self,
        db: Session,
        school_id: UUID,
        license_number: str,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for license_number within school.
        Respects unique constraint (school_id, license_number).
        Optional exclude_id for update operations.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.school_id == school_id,
            self.model.license_number == license_number
        )
        
        if exclude_id is not None:
            stmt = stmt.where(self.model.id != exclude_id)
        
        result = db.execute(stmt)
        count = result.scalar() or 0
        return count > 0

    def exists_staff_member_id(
        self,
        db: Session,
        school_id: UUID,
        staff_member_id: UUID,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for staff_member_id within school.
        Respects unique constraint on staff_member_id.
        Optional exclude_id for update operations.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.school_id == school_id,
            self.model.staff_member_id == staff_member_id
        )
        
        if exclude_id is not None:
            stmt = stmt.where(self.model.id != exclude_id)
        
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
        Count drivers within school.
        Null-safe aggregation.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.school_id == school_id)
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_status(
        self,
        db: Session,
        school_id: UUID,
        status: Any  # DriverStatus enum
    ) -> int:
        """
        Count drivers by status within school.
        Null-safe aggregation.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.status == status
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_expiring_licenses(
        self,
        db: Session,
        school_id: UUID,
        before_date: datetime
    ) -> int:
        """
        Count drivers with licenses expiring before a date.
        Null-safe aggregation.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.license_expiry <= before_date
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # Bulk Operations (Atomic, Empty Guards)
    # -----------------------------------------

    def bulk_update_status(
        self,
        db: Session,
        school_id: UUID,
        driver_ids: List[UUID],
        new_status: Any  # DriverStatus enum
    ) -> int:
        """
        Bulk update status for multiple drivers.
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Returns count of updated rows.
        """
        if not driver_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(driver_ids),
                self.model.status != new_status
            )
            .values(status=new_status)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_license_expiry(
        self,
        db: Session,
        school_id: UUID,
        driver_ids: List[UUID],
        license_expiry: datetime
    ) -> int:
        """
        Bulk update license expiry for multiple drivers.
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Returns count of updated rows.
        """
        if not driver_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(driver_ids),
                self.model.license_expiry != license_expiry
            )
            .values(license_expiry=license_expiry)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0