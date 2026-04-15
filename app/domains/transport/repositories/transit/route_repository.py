# transport/repositories/transit/route_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from repositories.base import SchoolScopedRepository
from transport.models.transit import Route


class RouteRepository(SchoolScopedRepository[Route]):
    """
    Repository for Route model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    Soft-delete aware (Route model has is_deleted).
    Zero business logic, zero validation, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(Route)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        school_id: UUID,
        route_id: UUID
    ) -> Optional[Route]:
        """
        Retrieve route by ID scoped to school.
        Prevents horizontal privilege escalation.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == route_id,
                self.model.school_id == school_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_name(
        self,
        db: Session,
        school_id: UUID,
        name: str
    ) -> Optional[Route]:
        """
        Retrieve route by name scoped to school.
        Respects unique constraint (school_id, name).
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.name == name
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
    ) -> List[Route]:
        """
        List all routes within school tenant.
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

    def list_by_status(
        self,
        db: Session,
        school_id: UUID,
        status: Any,  # RouteStatus enum
        skip: int = 0,
        limit: int = 100
    ) -> List[Route]:
        """
        List routes by status within school tenant.
        Uses index on status.
        Deterministic ordering: created_at DESC, id DESC.
        Soft-delete filtered.
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
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_active_routes(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Route]:
        """
        List active routes within school tenant.
        Deterministic ordering: created_at DESC, id DESC.
        Soft-delete filtered.
        """
        from types.transport import RouteStatus
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.status == RouteStatus.ACTIVE
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

    def list_inactive_routes(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Route]:
        """
        List inactive routes within school tenant.
        Deterministic ordering: created_at DESC, id DESC.
        Soft-delete filtered.
        """
        from types.transport import RouteStatus
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.status == RouteStatus.INACTIVE
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
    ) -> List[Route]:
        """
        List soft-deleted routes within school tenant.
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
        route_id: UUID
    ) -> Optional[Route]:
        """
        Lock route for update (route modifications).
        Scoped to school_id for tenant safety.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == route_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()
    

    def lock_by_name_for_update(
        self,
        db: Session,
        school_id: UUID,
        name: str
    ) -> Optional[Route]:
        """
        Lock route by name for update.
        Tenant-safe locking.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.name == name
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
        route_id: UUID
    ) -> bool:
        """
        Efficient existence check for route by ID.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == route_id,
                self.model.school_id == school_id
            )
            .limit(1)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_name(
        self,
        db: Session,
        school_id: UUID,
        name: str,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for route name within school.
        Respects unique constraint (school_id, name).
        Optional exclude_id for update operations.
        Soft-delete filtered.
        """
        stmt = select(self.model.id).where(
            self.model.school_id == school_id,
            self.model.name == name
        ).limit(1)
        
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
        Count routes within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model.id)
            .where(self.model.school_id == school_id)
        ).limit(1)
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_status(
        self,
        db: Session,
        school_id: UUID,
        status: Any  # RouteStatus enum
    ) -> int:
        """
        Count routes by status within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.school_id == school_id,
                self.model.status == status
            )
        ).limit(1)
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_active(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count active routes within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        from types.transport import RouteStatus
        stmt = (
            select(self.model.id)
            .where(
                self.model.school_id == school_id,
                self.model.status == RouteStatus.ACTIVE
            )
        ).limit(1)
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_deleted(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count soft-deleted routes within school.
        Null-safe aggregation.
        Does NOT apply soft-delete filter.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
        ).limit(1)
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # Soft Delete Operations
    # -----------------------------------------

    def soft_delete(
        self,
        db: Session,
        school_id: UUID,
        route_id: UUID
    ) -> bool:
        """
        Soft delete route record.
        Scoped to school_id for tenant safety.
        Returns True if successful.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.id == route_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        route = result.scalar_one_or_none()

        if route:
            route.is_deleted = True
            route.deleted_at = now
            db.flush()
            return True
        return False

    def restore(
        self,
        db: Session,
        school_id: UUID,
        route_id: UUID
    ) -> bool:
        """
        Restore soft-deleted route record.
        Scoped to school_id.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == route_id,
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        route = result.scalar_one_or_none()

        if route:
            route.is_deleted = False
            route.deleted_at = None
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
        route_ids: List[UUID],
        new_status: Any  # RouteStatus enum
    ) -> int:
        """
        Bulk update status for multiple routes.
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not route_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(route_ids),
                self.model.is_deleted.is_(False)
            )
            .values(status=new_status)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_route_info(
        self,
        db: Session,
        school_id: UUID,
        route_ids: List[UUID],
        distance_km: Optional[float] = None,
        estimated_duration_minutes: Optional[int] = None
    ) -> int:
        """
        Bulk update route info for multiple routes.
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not route_ids:
            return 0

        values = {}
        if distance_km is not None:
            values['distance_km'] = distance_km
        if estimated_duration_minutes is not None:
            values['estimated_duration_minutes'] = estimated_duration_minutes
        
        if not values:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(route_ids),
                self.model.is_deleted.is_(False)
            )
            .values(**values)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0