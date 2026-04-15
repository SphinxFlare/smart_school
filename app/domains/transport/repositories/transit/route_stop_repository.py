# transport/repositories/transit/route_stop_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, func, update

from repositories.base import SchoolScopedRepository
from transport.models.transit import RouteStop, Route


class RouteStopRepository(SchoolScopedRepository[RouteStop]):
    """
    Repository for RouteStop model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    Soft-delete aware (RouteStop model has is_deleted).
    Zero business logic, zero validation, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(RouteStop)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        school_id: UUID,
        stop_id: UUID
    ) -> Optional[RouteStop]:
        """
        Retrieve route stop by ID scoped to school.
        Prevents horizontal privilege escalation.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == stop_id,
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
    ) -> List[RouteStop]:
        """
        List all route stops within school tenant.
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

    def list_by_route(
        self,
        db: Session,
        school_id: UUID,
        route_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[RouteStop]:
        """
        List route stops for a route within school tenant.
        Deterministic ordering: sequence_order ASC, id ASC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.route_id == route_id
            )
            .order_by(
                self.model.sequence_order.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_route_ordered(
        self,
        db: Session,
        school_id: UUID,
        route_id: UUID
    ) -> List[RouteStop]:
        """
        List all route stops for a route ordered by sequence.
        No pagination - returns all stops for route processing.
        Deterministic ordering: sequence_order ASC, id ASC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.route_id == route_id
            )
            .order_by(
                self.model.sequence_order.asc(),
                self.model.id.asc()
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_deleted(
        self,
        db: Session,
        school_id: UUID,
        route_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[RouteStop]:
        """
        List soft-deleted route stops within school tenant.
        Does NOT apply soft-delete filter (explicitly includes deleted).
        Deterministic ordering: created_at DESC, id DESC.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.is_deleted.is_(True)
        )
        
        if route_id:
            stmt = stmt.where(self.model.route_id == route_id)
        
        stmt = (
            stmt.order_by(
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
        stop_id: UUID
    ) -> Optional[RouteStop]:
        """
        Lock route stop for update (stop modifications).
        Scoped to school_id for tenant safety.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == stop_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()


    def lock_by_route_and_sequence_for_update(
        self,
        db: Session,
        school_id: UUID,
        route_id: UUID,
        sequence_order: int
    ) -> Optional[RouteStop]:
        """
        Lock route stop by route and sequence for update.
        Tenant-safe locking.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.route_id == route_id,
                self.model.sequence_order == sequence_order
            )
            .with_for_update()
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
        stop_id: UUID
    ) -> bool:
        """
        Efficient existence check for route stop by ID.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == stop_id,
                self.model.school_id == school_id
            )
            .limit(1)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_route_sequence(
        self,
        db: Session,
        school_id: UUID,
        route_id: UUID,
        sequence_order: int,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for route/sequence combination within school.
        Respects unique constraint (route_id, sequence_order).
        Optional exclude_id for update operations.
        Soft-delete filtered.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.school_id == school_id,
            self.model.route_id == route_id,
            self.model.sequence_order == sequence_order
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
        Count route stops within school.
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

    def count_by_route(
        self,
        db: Session,
        school_id: UUID,
        route_id: UUID
    ) -> int:
        """
        Count route stops for a route within school.
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

    def count_deleted(
        self,
        db: Session,
        school_id: UUID,
        route_id: Optional[UUID] = None
    ) -> int:
        """
        Count soft-deleted route stops within school.
        Null-safe aggregation.
        Does NOT apply soft-delete filter.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.school_id == school_id,
            self.model.is_deleted.is_(True)
        )
        
        if route_id:
            stmt = stmt.where(self.model.route_id == route_id)
        
        result = db.execute(stmt)
        return result.scalar() or 0

    def get_max_sequence_order(
        self,
        db: Session,
        school_id: UUID,
        route_id: UUID
    ) -> int:
        """
        Get maximum sequence_order for a route.
        Returns 0 if no stops exist.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.max(self.model.sequence_order))
            .where(
                self.model.school_id == school_id,
                self.model.route_id == route_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        value = result.scalar()
        return value if value is not None else 0

    # -----------------------------------------
    # Soft Delete Operations
    # -----------------------------------------

    def soft_delete(
        self,
        db: Session,
        school_id: UUID,
        stop_id: UUID
    ) -> bool:
        """
        Soft delete route stop record.
        Scoped to school_id for tenant safety.
        Returns True if successful.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.id == stop_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        stop = result.scalar_one_or_none()

        if stop:
            stop.is_deleted = True
            db.flush()
            return True
        return False

    def restore(
        self,
        db: Session,
        school_id: UUID,
        stop_id: UUID
    ) -> bool:
        """
        Restore soft-deleted route stop record.
        Scoped to school_id.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == stop_id,
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        stop = result.scalar_one_or_none()

        if stop:
            stop.is_deleted = False
            db.flush()
            return True
        return False
    
    
    def lock_by_route_for_update(
        self,
        db: Session,
        school_id: UUID,
        route_id: UUID
    ) -> List[RouteStop]:
        """
        Lock all route stops for a route.
        Used before sequence reordering to prevent race conditions.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.route_id == route_id
            )
            .with_for_update()
        )

        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Bulk Operations (Atomic, Empty Guards)
    # -----------------------------------------

    def bulk_update_sequence_order(
        self,
        db: Session,
        school_id: UUID,
        route_id: UUID,
        sequence_updates: List[Dict[str, Any]]
    ) -> int:
        """
        Bulk update sequence_order for multiple route stops.
        sequence_updates: List of {'id': UUID, 'sequence_order': int}
        Atomic update statements scoped by school_id.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not sequence_updates:
            return 0

        updated_count = 0
        for update_data in sequence_updates:
            stop_id = update_data.get('id')
            sequence_order = update_data.get('sequence_order')
            
            if stop_id and sequence_order is not None:
                stmt = (
                    update(self.model)
                    .where(
                        self.model.school_id == school_id,
                        self.model.route_id == route_id,
                        self.model.id == stop_id,
                        self.model.is_deleted.is_(False)
                    )
                    .values(sequence_order=sequence_order)
                )
                result = db.execute(stmt)
                updated_count += result.rowcount or 0

        db.flush()
        return updated_count

    def bulk_soft_delete_by_route(
        self,
        db: Session,
        school_id: UUID,
        route_id: UUID
    ) -> int:
        """
        Bulk soft delete all route stops for a route.
        Atomic update statement scoped by school_id.
        Returns count of updated rows.
        """
        now = datetime.utcnow()
        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.route_id == route_id,
                self.model.is_deleted.is_(False)
            )
            .values(is_deleted=True)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_restore_by_route(
        self,
        db: Session,
        school_id: UUID,
        route_id: UUID
    ) -> int:
        """
        Bulk restore all soft-deleted route stops for a route.
        Atomic update statement scoped by school_id.
        Returns count of updated rows.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.route_id == route_id,
                self.model.is_deleted.is_(True)
            )
            .values(is_deleted=False)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0