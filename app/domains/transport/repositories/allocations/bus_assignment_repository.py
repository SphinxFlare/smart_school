# transport/repositories/allocations/bus_assignment_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from repositories.base import SchoolScopedRepository
from transport.models.allocations import BusAssignment


class BusAssignmentRepository(SchoolScopedRepository[BusAssignment]):
    """
    Repository for BusAssignment model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    Soft-delete aware (BusAssignment model has is_deleted).
    Zero business logic, zero overlap validation, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(BusAssignment)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        school_id: UUID,
        assignment_id: UUID
    ) -> Optional[BusAssignment]:
        """
        Retrieve bus assignment by ID scoped to school.
        Prevents horizontal privilege escalation.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == assignment_id,
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
    ) -> List[BusAssignment]:
        """
        List all bus assignments within school tenant.
        Deterministic ordering: effective_from DESC, id DESC.
        Soft-delete filtered (excludes deleted).
        """
        stmt = (
            select(self.model)
            .where(self.model.school_id == school_id)
            .order_by(
                self.model.effective_from.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_bus(
        self,
        db: Session,
        school_id: UUID,
        bus_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[BusAssignment]:
        """
        List bus assignments for a specific bus within school tenant.
        Deterministic ordering: effective_from DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.bus_id == bus_id
            )
            .order_by(
                self.model.effective_from.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_bus_and_academic_year(
        self,
        db: Session,
        school_id: UUID,
        bus_id: UUID,
        academic_year_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[BusAssignment]:
        """
        List bus assignments for a bus within academic year.
        Deterministic ordering: effective_from ASC, id ASC (sequence matters).
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.bus_id == bus_id,
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

    def list_by_driver(
        self,
        db: Session,
        school_id: UUID,
        driver_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[BusAssignment]:
        """
        List bus assignments for a driver within school tenant.
        Deterministic ordering: effective_from DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.driver_id == driver_id
            )
            .order_by(
                self.model.effective_from.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_route(
        self,
        db: Session,
        school_id: UUID,
        route_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[BusAssignment]:
        """
        List bus assignments for a route within school tenant.
        Deterministic ordering: effective_from DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.route_id == route_id
            )
            .order_by(
                self.model.effective_from.desc(),
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
    ) -> List[BusAssignment]:
        """
        List bus assignments for an academic year within school tenant.
        Deterministic ordering: effective_from DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.academic_year_id == academic_year_id
            )
            .order_by(
                self.model.effective_from.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_active_assignments(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[BusAssignment]:
        """
        List active bus assignments within school tenant.
        Deterministic ordering: effective_from DESC, id DESC.
        Soft-delete filtered.
        """
        from types.transport import AssignmentStatus
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.status == AssignmentStatus.ACTIVE
            )
            .order_by(
                self.model.effective_from.desc(),
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
    ) -> List[BusAssignment]:
        """
        List soft-deleted bus assignments within school tenant.
        Does NOT apply soft-delete filter (explicitly includes deleted).
        Deterministic ordering: effective_from DESC, id DESC.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
            .order_by(
                self.model.effective_from.desc(),
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
        assignment_id: UUID
    ) -> Optional[BusAssignment]:
        """
        Lock bus assignment for update.
        Scoped to school_id for tenant safety.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == assignment_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_by_bus_and_academic_year_for_update(
        self,
        db: Session,
        school_id: UUID,
        bus_id: UUID,
        academic_year_id: UUID,
        effective_from: datetime
    ) -> Optional[BusAssignment]:
        """
        Lock bus assignment by bus, academic year, and effective_from.
        Respects composite uniqueness constraint.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.bus_id == bus_id,
                self.model.academic_year_id == academic_year_id,
                self.model.effective_from == effective_from
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_all_assignments_by_bus_for_update(
        self,
        db: Session,
        school_id: UUID,
        bus_id: UUID,
        academic_year_id: Optional[UUID] = None
    ) -> List[BusAssignment]:
        """
        Lock all assignments for a bus within academic year.
        Used for reassignment operations.
        Soft-delete filtered.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.bus_id == bus_id
        )
        
        if academic_year_id:
            stmt = stmt.where(self.model.academic_year_id == academic_year_id)
        
        stmt = stmt.with_for_update()
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def lock_all_assignments_by_driver_for_update(
        self,
        db: Session,
        school_id: UUID,
        driver_id: UUID,
        academic_year_id: Optional[UUID] = None
    ) -> List[BusAssignment]:
        """
        Lock all assignments for a driver within academic year.
        Used for reassignment operations.
        Soft-delete filtered.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.driver_id == driver_id
        )
        
        if academic_year_id:
            stmt = stmt.where(self.model.academic_year_id == academic_year_id)
        
        stmt = stmt.with_for_update()
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def lock_all_assignments_by_route_for_update(
        self,
        db: Session,
        school_id: UUID,
        route_id: UUID,
        academic_year_id: Optional[UUID] = None
    ) -> List[BusAssignment]:
        """
        Lock all assignments for a route within academic year.
        Used for reassignment operations.
        Soft-delete filtered.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.route_id == route_id
        )
        
        if academic_year_id:
            stmt = stmt.where(self.model.academic_year_id == academic_year_id)
        
        stmt = stmt.with_for_update()
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
        assignment_id: UUID
    ) -> bool:
        """
        Efficient existence check for bus assignment by ID.
        Soft-delete filtered.
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == assignment_id,
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
        bus_id: UUID,
        academic_year_id: UUID,
        effective_from: datetime,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for composite uniqueness constraint.
        Respects (school_id, bus_id, academic_year_id, effective_from).
        Optional exclude_id for update operations.
        Soft-delete filtered.
        Uses select(id).limit(1) pattern.
        """
        stmt = select(self.model.id).where(
            self.model.school_id == school_id,
            self.model.bus_id == bus_id,
            self.model.academic_year_id == academic_year_id,
            self.model.effective_from == effective_from
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
        Count bus assignments within school.
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

    def count_by_bus(
        self,
        db: Session,
        school_id: UUID,
        bus_id: UUID
    ) -> int:
        """
        Count bus assignments for a bus within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.bus_id == bus_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_driver(
        self,
        db: Session,
        school_id: UUID,
        driver_id: UUID
    ) -> int:
        """
        Count bus assignments for a driver within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.driver_id == driver_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_route(
        self,
        db: Session,
        school_id: UUID,
        route_id: UUID
    ) -> int:
        """
        Count bus assignments for a route within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.route_id == route_id
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
        Count bus assignments for an academic year within school.
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
        Count soft-deleted bus assignments within school.
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
        assignment_id: UUID
    ) -> bool:
        """
        Soft delete bus assignment record.
        Scoped to school_id for tenant safety.
        Returns True if successful.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.id == assignment_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        assignment = result.scalar_one_or_none()

        if assignment:
            assignment.is_deleted = True
            db.flush()
            return True
        return False

    def restore(
        self,
        db: Session,
        school_id: UUID,
        assignment_id: UUID
    ) -> bool:
        """
        Restore soft-deleted bus assignment record.
        Scoped to school_id.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == assignment_id,
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        assignment = result.scalar_one_or_none()

        if assignment:
            assignment.is_deleted = False
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
        assignment_ids: List[UUID],
        new_status: Any
    ) -> int:
        """
        Bulk update status for multiple bus assignments.
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not assignment_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(assignment_ids),
                self.model.is_deleted.is_(False)
            )
            .values(status=new_status)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_by_bus(
        self,
        db: Session,
        school_id: UUID,
        bus_id: UUID,
        updates: Dict[str, Any]
    ) -> int:
        """
        Bulk update bus assignments for a specific bus.
        Atomic update statement scoped by school_id and bus_id.
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
                self.model.bus_id == bus_id,
                self.model.is_deleted.is_(False)
            )
            .values(**updates)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_by_academic_year(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID,
        updates: Dict[str, Any]
    ) -> int:
        """
        Bulk update bus assignments for an academic year.
        Atomic update statement scoped by school_id and academic_year_id.
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
                self.model.academic_year_id == academic_year_id,
                self.model.is_deleted.is_(False)
            )
            .values(**updates)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_soft_delete_by_bus(
        self,
        db: Session,
        school_id: UUID,
        bus_id: UUID
    ) -> int:
        """
        Bulk soft delete all bus assignments for a bus.
        Atomic update statement scoped by school_id.
        Returns count of updated rows.
        """
        now = datetime.utcnow()
        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.bus_id == bus_id,
                self.model.is_deleted.is_(False)
            )
            .values(is_deleted=True)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_restore_by_bus(
        self,
        db: Session,
        school_id: UUID,
        bus_id: UUID
    ) -> int:
        """
        Bulk restore all soft-deleted bus assignments for a bus.
        Atomic update statement scoped by school_id.
        Returns count of updated rows.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.bus_id == bus_id,
                self.model.is_deleted.is_(True)
            )
            .values(is_deleted=False, deleted_at=None)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0
    

    def lock_by_bus_and_year_for_update(
        self,
        db: Session,
        school_id: UUID,
        bus_id: UUID,
        academic_year_id: UUID
    ) -> List[BusAssignment]:

        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.bus_id == bus_id,
                self.model.academic_year_id == academic_year_id
            )
            .with_for_update()
        )

        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())
