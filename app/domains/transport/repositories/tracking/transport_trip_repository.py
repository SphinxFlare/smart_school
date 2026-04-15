# transport/repositories/tracking/transport_trip_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from repositories.base import SchoolScopedRepository
from transport.models.tracking import TransportTrip


class TransportTripRepository(SchoolScopedRepository[TransportTrip]):
    """
    Repository for TransportTrip model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    Soft-delete aware (TransportTrip model has is_deleted).
    Zero business logic, zero trip lifecycle validation, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(TransportTrip)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID
    ) -> Optional[TransportTrip]:
        """
        Retrieve transport trip by ID scoped to school.
        Prevents horizontal privilege escalation.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == trip_id,
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
    ) -> List[TransportTrip]:
        """
        List all transport trips within school tenant.
        Deterministic ordering: trip_date DESC, created_at DESC, id DESC.
        Soft-delete filtered (excludes deleted).
        """
        stmt = (
            select(self.model)
            .where(self.model.school_id == school_id)
            .order_by(
                self.model.trip_date.desc(),
                self.model.created_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_bus_assignment(
        self,
        db: Session,
        school_id: UUID,
        bus_assignment_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransportTrip]:
        """
        List transport trips for a bus assignment within school tenant.
        Deterministic ordering: trip_date DESC, created_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.bus_assignment_id == bus_assignment_id
            )
            .order_by(
                self.model.trip_date.desc(),
                self.model.created_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_bus_assignment_and_date(
        self,
        db: Session,
        school_id: UUID,
        bus_assignment_id: UUID,
        trip_date: date,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransportTrip]:
        """
        List transport trips for a bus assignment on a specific date.
        Deterministic ordering: trip_type ASC, created_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.bus_assignment_id == bus_assignment_id,
                self.model.trip_date == trip_date
            )
            .order_by(
                self.model.trip_type.asc(),
                self.model.created_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_trip_date(
        self,
        db: Session,
        school_id: UUID,
        trip_date: date,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransportTrip]:
        """
        List transport trips for a specific date within school tenant.
        Deterministic ordering: trip_date DESC, created_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.trip_date == trip_date
            )
            .order_by(
                self.model.trip_date.desc(),
                self.model.created_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_date_range(
        self,
        db: Session,
        school_id: UUID,
        start_date: date,
        end_date: date,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransportTrip]:
        """
        List transport trips within date range.
        Index-friendly filtering on trip_date.
        Deterministic ordering: trip_date DESC, created_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.trip_date >= start_date,
                self.model.trip_date <= end_date
            )
            .order_by(
                self.model.trip_date.desc(),
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
        status: Any,  # TripStatus enum
        skip: int = 0,
        limit: int = 100
    ) -> List[TransportTrip]:
        """
        List transport trips by status within school tenant.
        Uses index on status.
        Deterministic ordering: trip_date DESC, created_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.status == status
            )
            .order_by(
                self.model.trip_date.desc(),
                self.model.created_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_trip_type(
        self,
        db: Session,
        school_id: UUID,
        trip_type: Any,  # TripType enum
        skip: int = 0,
        limit: int = 100
    ) -> List[TransportTrip]:
        """
        List transport trips by trip type within school tenant.
        Deterministic ordering: trip_date DESC, created_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.trip_type == trip_type
            )
            .order_by(
                self.model.trip_date.desc(),
                self.model.created_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_active_trips(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransportTrip]:
        """
        List active (in_progress) transport trips within school tenant.
        Deterministic ordering: trip_date DESC, created_at DESC, id DESC.
        Soft-delete filtered.
        """
        from types.transport import TripStatus
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.status == TripStatus.IN_PROGRESS
            )
            .order_by(
                self.model.trip_date.desc(),
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
    ) -> List[TransportTrip]:
        """
        List soft-deleted transport trips within school tenant.
        Does NOT apply soft-delete filter (explicitly includes deleted).
        Deterministic ordering: trip_date DESC, created_at DESC, id DESC.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
            .order_by(
                self.model.trip_date.desc(),
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
        trip_id: UUID
    ) -> Optional[TransportTrip]:
        """
        Lock transport trip for update.
        Scoped to school_id for tenant safety.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == trip_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_by_composite_unique_for_update(
        self,
        db: Session,
        school_id: UUID,
        bus_assignment_id: UUID,
        trip_date: date,
        trip_type: Any  # TripType enum
    ) -> Optional[TransportTrip]:
        """
        Lock transport trip by composite uniqueness constraint.
        Respects (school_id, bus_assignment_id, trip_date, trip_type).
        Used for idempotent trip creation.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.bus_assignment_id == bus_assignment_id,
                self.model.trip_date == trip_date,
                self.model.trip_type == trip_type
            )
            .order_by(self.model.id.asc())
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_all_trips_by_assignment_and_date_for_update(
        self,
        db: Session,
        school_id: UUID,
        bus_assignment_id: UUID,
        trip_date: date
    ) -> List[TransportTrip]:
        """
        Lock all trips for a bus assignment on a specific date.
        Used for trip sequence operations.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.bus_assignment_id == bus_assignment_id,
                self.model.trip_date == trip_date
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def lock_all_trips_by_assignment_for_update(
        self,
        db: Session,
        school_id: UUID,
        bus_assignment_id: UUID,
        trip_date: Optional[date] = None
    ) -> List[TransportTrip]:
        """
        Lock all trips for a bus assignment.
        Used for reassignment operations.
        Soft-delete filtered.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.bus_assignment_id == bus_assignment_id
        )
        
        if trip_date:
            stmt = stmt.where(self.model.trip_date == trip_date)
        
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
        trip_id: UUID
    ) -> bool:
        """
        Efficient existence check for transport trip by ID.
        Soft-delete filtered.
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == trip_id,
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
        bus_assignment_id: UUID,
        trip_date: date,
        trip_type: Any,  # TripType enum
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for composite uniqueness constraint.
        Respects (school_id, bus_assignment_id, trip_date, trip_type).
        Optional exclude_id for update operations.
        Soft-delete filtered.
        Uses select(id).limit(1) pattern.
        """
        stmt = select(self.model.id).where(
            self.model.school_id == school_id,
            self.model.bus_assignment_id == bus_assignment_id,
            self.model.trip_date == trip_date,
            self.model.trip_type == trip_type
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
        Count transport trips within school.
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

    def count_by_bus_assignment(
        self,
        db: Session,
        school_id: UUID,
        bus_assignment_id: UUID
    ) -> int:
        """
        Count transport trips for a bus assignment within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.bus_assignment_id == bus_assignment_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_trip_date(
        self,
        db: Session,
        school_id: UUID,
        trip_date: date
    ) -> int:
        """
        Count transport trips for a specific date within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.trip_date == trip_date
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_status(
        self,
        db: Session,
        school_id: UUID,
        status: Any  # TripStatus enum
    ) -> int:
        """
        Count transport trips by status within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.status == status
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
        Count soft-deleted transport trips within school.
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
        trip_id: UUID
    ) -> bool:
        """
        Soft delete transport trip record.
        Scoped to school_id for tenant safety.
        Returns True if successful.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.id == trip_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        trip = result.scalar_one_or_none()

        if trip:
            trip.is_deleted = True
            db.flush()
            return True
        return False

    def restore(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID
    ) -> bool:
        """
        Restore soft-deleted transport trip record.
        Scoped to school_id.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == trip_id,
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        trip = result.scalar_one_or_none()

        if trip:
            trip.is_deleted = False
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
        trip_ids: List[UUID],
        new_status: Any  # TripStatus enum
    ) -> int:
        """
        Bulk update status for multiple transport trips.
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not trip_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(trip_ids),
                self.model.is_deleted.is_(False)
            )
            .values(status=new_status)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_by_bus_assignment(
        self,
        db: Session,
        school_id: UUID,
        bus_assignment_id: UUID,
        updates: Dict[str, Any]
    ) -> int:
        """
        Bulk update transport trips for a bus assignment.
        Atomic update statement scoped by school_id and bus_assignment_id.
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
                self.model.bus_assignment_id == bus_assignment_id,
                self.model.is_deleted.is_(False)
            )
            .values(**updates)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_by_trip_date(
        self,
        db: Session,
        school_id: UUID,
        trip_date: date,
        updates: Dict[str, Any]
    ) -> int:
        """
        Bulk update transport trips for a specific date.
        Atomic update statement scoped by school_id and trip_date.
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
                self.model.trip_date == trip_date,
                self.model.is_deleted.is_(False)
            )
            .values(**updates)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_soft_delete_by_bus_assignment(
        self,
        db: Session,
        school_id: UUID,
        bus_assignment_id: UUID
    ) -> int:
        """
        Bulk soft delete all transport trips for a bus assignment.
        Atomic update statement scoped by school_id.
        Returns count of updated rows.
        """
        now = datetime.utcnow()
        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.bus_assignment_id == bus_assignment_id,
                self.model.is_deleted.is_(False)
            )
            .values(is_deleted=True)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_restore_by_bus_assignment(
        self,
        db: Session,
        school_id: UUID,
        bus_assignment_id: UUID
    ) -> int:
        """
        Bulk restore all soft-deleted transport trips for a bus assignment.
        Atomic update statement scoped by school_id.
        Returns count of updated rows.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.bus_assignment_id == bus_assignment_id,
                self.model.is_deleted.is_(True)
            )
            .values(is_deleted=False)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0
    

    def get_by_composite_unique(
        self,
        db: Session,
        school_id: UUID,
        bus_assignment_id: UUID,
        trip_date: date,
        trip_type: Any
    ) -> Optional[TransportTrip]:

        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.bus_assignment_id == bus_assignment_id,
                self.model.trip_date == trip_date,
                self.model.trip_type == trip_type
            )
        )

        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return result.scalar_one_or_none()
    

    def get_latest_by_assignment(
        self,
        db: Session,
        school_id: UUID,
        bus_assignment_id: UUID
    ) -> Optional[TransportTrip]:

        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.bus_assignment_id == bus_assignment_id
            )
            .order_by(
                self.model.trip_date.desc(),
                self.model.created_at.desc(),
                self.model.id.desc()
            )
            .limit(1)
        )

        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return result.scalar_one_or_none()