# transport/repositories/transit/bus_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from repositories.base import SchoolScopedRepository
from transport.models.transit import Bus


class BusRepository(SchoolScopedRepository[Bus]):
    """
    Repository for Bus model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    NOTE: Bus model does NOT have is_deleted, so no soft-delete filtering.
    Zero business logic, zero validation, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(Bus)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        school_id: UUID,
        bus_id: UUID
    ) -> Optional[Bus]:
        """
        Retrieve bus by ID scoped to school.
        Prevents horizontal privilege escalation.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == bus_id,
                self.model.school_id == school_id
            )
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_bus_number(
        self,
        db: Session,
        school_id: UUID,
        bus_number: str
    ) -> Optional[Bus]:
        """
        Retrieve bus by bus_number scoped to school.
        Respects unique constraint (school_id, bus_number).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.bus_number == bus_number
            )
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_registration_number(
        self,
        db: Session,
        school_id: UUID,
        registration_number: str
    ) -> Optional[Bus]:
        """
        Retrieve bus by registration_number scoped to school.
        Respects unique constraint (school_id, registration_number).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.registration_number == registration_number
            )
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_gps_device_id(
        self,
        db: Session,
        school_id: UUID,
        gps_device_id: str
    ) -> Optional[Bus]:
        """
        Retrieve bus by gps_device_id scoped to school.
        Respects unique constraint (school_id, gps_device_id).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.gps_device_id == gps_device_id
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
    ) -> List[Bus]:
        """
        List all buses within school tenant.
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
        status: Any,  # BusStatus enum
        skip: int = 0,
        limit: int = 100
    ) -> List[Bus]:
        """
        List buses by status within school tenant.
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

    def list_active_buses(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Bus]:
        """
        List active buses within school tenant.
        Deterministic ordering: created_at DESC, id DESC.
        """
        from types.transport import BusStatus
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.status == BusStatus.ACTIVE
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

    def list_inactive_buses(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Bus]:
        """
        List inactive buses within school tenant.
        Deterministic ordering: created_at DESC, id DESC.
        """
        from types.transport import BusStatus
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.status == BusStatus.INACTIVE
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
        bus_id: UUID
    ) -> Optional[Bus]:
        """
        Lock bus for update (bus state modifications).
        Scoped to school_id for tenant safety.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == bus_id,
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
        bus_id: UUID
    ) -> Optional[Bus]:
        """
        Lock bus for status update operations.
        Maximum concurrency safety for sensitive mutation.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == bus_id,
                self.model.school_id == school_id
            )
            .with_for_update(skip_locked=False)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_by_bus_number_for_update(
        self,
        db: Session,
        school_id: UUID,
        bus_number: str
    ) -> Optional[Bus]:
        """
        Lock bus by bus_number for update.
        Tenant-safe locking.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.bus_number == bus_number
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
        bus_id: UUID
    ) -> bool:
        """
        Efficient existence check for bus by ID.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == bus_id,
                self.model.school_id == school_id
            )
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_bus_number(
        self,
        db: Session,
        school_id: UUID,
        bus_number: str,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for bus_number within school.
        Respects unique constraint (school_id, bus_number).
        Optional exclude_id for update operations.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.school_id == school_id,
            self.model.bus_number == bus_number
        )
        
        if exclude_id is not None:
            stmt = stmt.where(self.model.id != exclude_id)
        
        result = db.execute(stmt)
        count = result.scalar() or 0
        return count > 0

    def exists_registration_number(
        self,
        db: Session,
        school_id: UUID,
        registration_number: str,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for registration_number within school.
        Respects unique constraint (school_id, registration_number).
        Optional exclude_id for update operations.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.school_id == school_id,
            self.model.registration_number == registration_number
        )
        
        if exclude_id is not None:
            stmt = stmt.where(self.model.id != exclude_id)
        
        result = db.execute(stmt)
        count = result.scalar() or 0
        return count > 0

    def exists_gps_device_id(
        self,
        db: Session,
        school_id: UUID,
        gps_device_id: str,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for gps_device_id within school.
        Respects unique constraint (school_id, gps_device_id).
        Optional exclude_id for update operations.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.school_id == school_id,
            self.model.gps_device_id == gps_device_id
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
        Count buses within school.
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
        status: Any  # BusStatus enum
    ) -> int:
        """
        Count buses by status within school.
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

    def count_active(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count active buses within school.
        Null-safe aggregation.
        """
        from types.transport import BusStatus
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.status == BusStatus.ACTIVE
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_inactive(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count inactive buses within school.
        Null-safe aggregation.
        """
        from types.transport import BusStatus
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.status == BusStatus.INACTIVE
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
        bus_ids: List[UUID],
        new_status: Any  # BusStatus enum
    ) -> int:
        """
        Bulk update status for multiple buses.
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Returns count of updated rows.
        """
        if not bus_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(bus_ids)
            )
            .values(status=new_status)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_gps_device(
        self,
        db: Session,
        school_id: UUID,
        bus_ids: List[UUID],
        gps_device_id: Optional[str]
    ) -> int:
        """
        Bulk update GPS device ID for multiple buses.
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Returns count of updated rows.
        """
        if not bus_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(bus_ids)
            )
            .values(gps_device_id=gps_device_id)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0