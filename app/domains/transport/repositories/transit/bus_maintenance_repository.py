# transport/repositories/transit/bus_maintenance_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, func, update

from repositories.base import SchoolScopedRepository
from transport.models.transit import BusMaintenance, Bus


class BusMaintenanceRepository(SchoolScopedRepository[BusMaintenance]):
    """
    Repository for BusMaintenance model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    NOTE: BusMaintenance model does NOT have is_deleted, so no soft-delete filtering.
    Zero business logic, zero validation, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(BusMaintenance)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        school_id: UUID,
        maintenance_id: UUID
    ) -> Optional[BusMaintenance]:
        """
        Retrieve maintenance record by ID scoped to school.
        Prevents horizontal privilege escalation.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == maintenance_id,
                self.model.school_id == school_id
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
    ) -> List[BusMaintenance]:
        """
        List all maintenance records within school tenant.
        Deterministic ordering: performed_at DESC, id DESC.
        """
        stmt = (
            select(self.model)
            .where(self.model.school_id == school_id)
            .order_by(
                self.model.performed_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_bus(
        self,
        db: Session,
        school_id: UUID,
        bus_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[BusMaintenance]:
        """
        List maintenance records for a bus within school tenant.
        Deterministic ordering: performed_at DESC, id DESC.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.bus_id == bus_id
            )
            .order_by(
                self.model.performed_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_maintenance_type(
        self,
        db: Session,
        school_id: UUID,
        maintenance_type: Any,  # MaintenanceType enum
        skip: int = 0,
        limit: int = 100
    ) -> List[BusMaintenance]:
        """
        List maintenance records by type within school tenant.
        Deterministic ordering: performed_at DESC, id DESC.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.maintenance_type == maintenance_type
            )
            .order_by(
                self.model.performed_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
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
    ) -> List[BusMaintenance]:
        """
        List maintenance records by date range within school tenant.
        Index-friendly filtering on performed_at.
        Deterministic ordering: performed_at DESC, id DESC.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.performed_at >= start_date,
                self.model.performed_at <= end_date
            )
            .order_by(
                self.model.performed_at.desc(),
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
        maintenance_id: UUID
    ) -> Optional[BusMaintenance]:
        """
        Lock maintenance record for update.
        Scoped to school_id for tenant safety.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == maintenance_id,
                self.model.school_id == school_id
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
        maintenance_id: UUID
    ) -> bool:
        """
        Efficient existence check for maintenance record by ID.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == maintenance_id,
                self.model.school_id == school_id
            )
            .limit(1)
        )
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
        Count maintenance records within school.
        Null-safe aggregation.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.school_id == school_id)
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_bus(
        self,
        db: Session,
        school_id: UUID,
        bus_id: UUID
    ) -> int:
        """
        Count maintenance records for a bus within school.
        Null-safe aggregation.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.bus_id == bus_id
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_maintenance_type(
        self,
        db: Session,
        school_id: UUID,
        maintenance_type: Any  # MaintenanceType enum
    ) -> int:
        """
        Count maintenance records by type within school.
        Null-safe aggregation.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.maintenance_type == maintenance_type
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def sum_cost_by_school(
        self,
        db: Session,
        school_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> float:
        """
        Sum maintenance costs within school.
        Null-safe aggregation (returns 0.0 if None).
        """
        stmt = select(func.sum(self.model.cost)).where(
            self.model.school_id == school_id
        )
        
        if start_date:
            stmt = stmt.where(self.model.performed_at >= start_date)
        if end_date:
            stmt = stmt.where(self.model.performed_at <= end_date)
        
        result = db.execute(stmt)
        value = result.scalar()
        return value if value is not None else 0.0

    def sum_cost_by_bus(
        self,
        db: Session,
        school_id: UUID,
        bus_id: UUID
    ) -> float:
        """
        Sum maintenance costs for a bus within school.
        Null-safe aggregation (returns 0.0 if None).
        """
        stmt = (
            select(func.sum(self.model.cost))
            .where(
                self.model.school_id == school_id,
                self.model.bus_id == bus_id
            )
        )
        result = db.execute(stmt)
        value = result.scalar()
        return value if value is not None else 0.0

    # -----------------------------------------
    # Bulk Operations (Atomic, Empty Guards)
    # -----------------------------------------

    def bulk_update_cost(
        self,
        db: Session,
        school_id: UUID,
        maintenance_ids: List[UUID],
        cost: float
    ) -> int:
        """
        Bulk update cost for multiple maintenance records.
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Returns count of updated rows.
        """
        if not maintenance_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(maintenance_ids)
            )
            .values(cost=cost)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0