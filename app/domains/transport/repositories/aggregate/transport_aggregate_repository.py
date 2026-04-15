# transport/repositories/aggregate/transport_aggregate_repository.py


from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, date

from sqlalchemy.orm import Session

from transport.models.allocations import BusAssignment, StudentTransport
from transport.models.tracking import TransportTrip, TransportEvent, TransportNotification
from transport.models.transit import Route, RouteStop
from types.transport import TripStatus, StudentTransportStatus
from allocations.bus_assignment_repository import BusAssignmentRepository
from allocations.student_transport_repository import StudentTransportRepository
from tracking.transport_trip_repository import TransportTripRepository
from tracking.transport_event_repository import TransportEventRepository
from tracking.transport_notification_repository import TransportNotificationRepository
from transit.route_repository import RouteRepository
from transit.route_stop_repository import RouteStopRepository


class TransportAggregateRepository:
    """
    Transactional orchestration layer for multi-entity transport operations.
    Does NOT extend SchoolScopedRepository - composes existing repositories.
    Coordinates operations within a single database session passed from service layer.
    Never commits transactions - only flush operations.
    Purely a consistency and atomicity boundary.
    Zero business validation rules, permission logic, or domain policies.
    """

    def __init__(
        self,
        bus_assignment_repo: BusAssignmentRepository,
        student_transport_repo: StudentTransportRepository,
        transport_trip_repo: TransportTripRepository,
        transport_event_repo: TransportEventRepository,
        transport_notification_repo: TransportNotificationRepository,
        route_repo: RouteRepository,
        route_stop_repo: RouteStopRepository
    ):
        self.bus_assignment_repo = bus_assignment_repo
        self.student_transport_repo = student_transport_repo
        self.transport_trip_repo = transport_trip_repo
        self.transport_event_repo = transport_event_repo
        self.transport_notification_repo = transport_notification_repo
        self.route_repo = route_repo
        self.route_stop_repo = route_stop_repo

    # =========================================
    # Idempotent Trip Creation
    # =========================================

    def create_trip_idempotent(
        self,
        db: Session,
        school_id: UUID,
        bus_assignment_id: UUID,
        trip_date: date,
        trip_type: Any,  # TripType enum
        status: Any = None  # TripStatus enum, defaults to SCHEDULED
    ) -> Tuple[Optional[TransportTrip], bool]:
        """
        Idempotently create a transport trip.
        Uses composite unique constraint (school_id, bus_assignment_id, trip_date, trip_type).
        First reads with get_by_composite_unique, then locks with lock_by_composite_unique_for_update.
        Only creates if still absent after lock.
        Returns (trip, is_new) tuple.
        Only flushes - does not commit.
        """
        
        if status is None:
            status = TripStatus.SCHEDULED

        # -------------------------------------
        # Step 1: lock by composite unique
        # -------------------------------------
        locked_trip = self.transport_trip_repo.lock_by_composite_unique_for_update(
            db,
            school_id,
            bus_assignment_id,
            trip_date,
            trip_type
        )

        if locked_trip:
            return (locked_trip, False)

        # -------------------------------------
        # Step 2: verify bus assignment exists
        # -------------------------------------
        bus_assignment = self.bus_assignment_repo.get_by_id(
            db,
            school_id,
            bus_assignment_id
        )

        if not bus_assignment:
            return (None, False)

        # -------------------------------------
        # Step 3: create trip
        # -------------------------------------
        trip = TransportTrip(
            school_id=school_id,
            bus_assignment_id=bus_assignment_id,
            trip_date=trip_date,
            trip_type=trip_type,
            status=status,
            is_deleted=False,
        )

        db.add(trip)
        db.flush()

        return (trip, True)

    # =========================================
    # Trip Execution Workflow
    # =========================================

    def start_trip(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID,
        started_at: datetime
    ) -> bool:
        """
        Start a trip with proper locking.
        Locks trip before updating status to IN_PROGRESS.
        Returns True if successful.
        Only flushes - does not commit.
        """
        # -------------------------------------
        # Step 1: Lock trip for update
        # -------------------------------------
        trip = self.transport_trip_repo.lock_for_update(
            db,
            school_id,
            trip_id
        )

        if not trip:
            return False

        trip.started_at = started_at
        trip.status = TripStatus.IN_PROGRESS

        db.flush()
        return True

    def complete_trip(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID,
        ended_at: datetime,
        driver_notes: Optional[str] = None
    ) -> bool:
        """
        Complete a trip with proper locking.
        Locks trip before updating status to COMPLETED.
        Returns True if successful.
        Only flushes - does not commit.
        """
        # -------------------------------------
        # Step 1: Lock trip for update
        # -------------------------------------
        trip = self.transport_trip_repo.lock_for_update(
            db,
            school_id,
            trip_id
        )

        if not trip:
            return False

        trip.ended_at = ended_at
        trip.status = TripStatus.COMPLETED

        if driver_notes is not None:
            trip.driver_notes = driver_notes

        db.flush()
        return True

    def cancel_trip(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID,
        delay_reason: Optional[str] = None
    ) -> bool:
        """
        Cancel a trip with proper locking.
        Locks trip before updating status to CANCELLED.
        Returns True if successful.
        Only flushes - does not commit.
        """
        # -------------------------------------
        # Step 1: Lock trip for update
        # -------------------------------------
        trip = self.transport_trip_repo.lock_for_update(
            db,
            school_id,
            trip_id
        )

        if not trip:
            return False

        trip.status = TripStatus.CANCELLED

        if delay_reason is not None:
            trip.delay_reason = delay_reason

        db.flush()
        return True

    # =========================================
    # Event Append (Append-Only)
    # =========================================

    def append_event(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID,
        event_type: Any,  # TransportEventType enum
        timestamp: datetime,
        student_id: Optional[UUID] = None,
        route_stop_id: Optional[UUID] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        event_payload: Optional[Dict[str, Any]] = None
    ) -> Optional[TransportEvent]:
        """
        Append a transport event (append-only log).
        Locks latest event before inserting to prevent race conditions.
        Returns created event.
        Only flushes - does not commit.
        """
        # -------------------------------------
        # Step 1: Verify trip exists
        # -------------------------------------
        trip = self.transport_trip_repo.get_by_id(db, school_id, trip_id)
        
        if not trip:
            return None

        # -------------------------------------
        # Step 2: Lock latest event for this trip (prevent race conditions)
        # -------------------------------------
        self.transport_event_repo.lock_events_by_trip_for_update(
            db,
            school_id,
            trip_id
        )

        # -------------------------------------
        # Step 3: Create new event
        # -------------------------------------
        event = TransportEvent(
            school_id=school_id,
            trip_id=trip_id,
            event_type=event_type,
            student_id=student_id,
            route_stop_id=route_stop_id,
            latitude=latitude,
            longitude=longitude,
            timestamp=timestamp,
            event_payload=event_payload
        )
        db.add(event)
        db.flush()  # Get event.id

        return event

    def append_events_batch(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID,
        events_data: List[Dict[str, Any]]
    ) -> List[TransportEvent]:
        """
        Append multiple transport events in batch.
        Locks all events for trip before inserting.
        Returns list of created events.
        Only flushes - does not commit.
        """
        if not events_data:
            return []

        # -------------------------------------
        # Step 1: Verify trip exists
        # -------------------------------------
        trip = self.transport_trip_repo.get_by_id(db, school_id, trip_id)
        
        if not trip:
            return []

        # -------------------------------------
        # Step 2: Lock all events for this trip
        # -------------------------------------
        self.transport_event_repo.lock_events_by_trip_for_update(db, school_id, trip_id)

        # -------------------------------------
        # Step 3: Create all events
        # -------------------------------------
        created_events = []
        
        for event_data in events_data:
            event = TransportEvent(
                school_id=school_id,
                trip_id=trip_id,
                event_type=event_data.get('event_type'),
                student_id=event_data.get('student_id'),
                route_stop_id=event_data.get('route_stop_id'),
                latitude=event_data.get('latitude'),
                longitude=event_data.get('longitude'),
                timestamp=event_data.get('timestamp'),
                event_payload=event_data.get('event_payload')
            )
            db.add(event)
            created_events.append(event)

        db.flush()
        return created_events

    # =========================================
    # Notification Batch Creation
    # =========================================

    def create_notifications_for_trip(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID,
        student_parent_pairs: List[Tuple[UUID, UUID]],
        notification_type: Any,  # TransportNotificationType enum
        title: str,
        message: str
    ) -> List[TransportNotification]:
        """
        Create notifications for all students on a trip.
        Locks notifications by trip before batch creation.
        Returns list of created notifications.
        Only flushes - does not commit.
        """
        if not student_parent_pairs:
            return []

        # -------------------------------------
        # Step 1: verify trip exists
        # -------------------------------------
        trip = self.transport_trip_repo.get_by_id(
            db,
            school_id,
            trip_id
        )

        if not trip:
            return []

        # -------------------------------------
        # Step 2: lock notifications for trip
        # -------------------------------------
        self.transport_notification_repo.lock_undelivered_by_trip_for_update(
            db,
            school_id,
            trip_id
        )

        # -------------------------------------
        # Step 3: create notifications
        # -------------------------------------
        created_notifications = []

        for student_id, parent_id in student_parent_pairs:

            notification = TransportNotification(
                school_id=school_id,
                trip_id=trip_id,
                student_id=student_id,
                parent_id=parent_id,
                notification_type=notification_type,
                title=title,
                message=message,
                is_delivered=False,
                is_read=False
            )

            db.add(notification)
            created_notifications.append(notification)

        db.flush()
        return created_notifications

    def create_notification_for_student(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID,
        student_id: UUID,
        parent_id: UUID,
        notification_type: Any,  # TransportNotificationType enum
        title: str,
        message: str
    ) -> Optional[TransportNotification]:
        """
        Create a single notification for a student/parent.
        Locks notifications by student before creation.
        Returns created notification.
        Only flushes - does not commit.
        """
        # -------------------------------------
        # Step 1: Verify trip exists
        # -------------------------------------
        trip = self.transport_trip_repo.get_by_id(db, school_id, trip_id)
        
        if not trip:
            return None

        # -------------------------------------
        # Step 2: Lock notifications by student
        # -------------------------------------
        self.transport_notification_repo.lock_by_student_for_update(db, school_id, student_id)

        # -------------------------------------
        # Step 3: Create notification
        # -------------------------------------
        notification = TransportNotification(
            school_id=school_id,
            trip_id=trip_id,
            student_id=student_id,
            parent_id=parent_id,
            notification_type=notification_type,
            title=title,
            message=message,
            is_delivered=False,
            is_read=False
        )
        db.add(notification)
        db.flush()

        return notification

    # =========================================
    # Notification Delivery/Read Marking
    # =========================================

    def mark_notification_delivered(
        self,
        db: Session,
        school_id: UUID,
        notification_id: UUID
    ) -> bool:
        """
        Mark a single notification as delivered.
        Locks notification before update.
        Returns True if successful.
        Only flushes - does not commit.
        """
        delivered_at = datetime.utcnow()
        return self.transport_notification_repo.mark_as_delivered(
            db, school_id, notification_id, delivered_at
        )

    def mark_notification_read(
        self,
        db: Session,
        school_id: UUID,
        notification_id: UUID
    ) -> bool:
        """
        Mark a single notification as read.
        Locks notification before update.
        Returns True if successful.
        Only flushes - does not commit.
        """
        read_at = datetime.utcnow()
        return self.transport_notification_repo.mark_as_read(
            db, school_id, notification_id, read_at
        )

    def mark_notifications_delivered_batch(
        self,
        db: Session,
        school_id: UUID,
        notification_ids: List[UUID]
    ) -> int:
        """
        Bulk mark notifications as delivered.
        Returns count of updated rows.
        Only flushes - does not commit.
        """
        delivered_at = datetime.utcnow()
        return self.transport_notification_repo.bulk_mark_as_delivered(
            db, school_id, notification_ids, delivered_at
        )

    def mark_notifications_read_batch(
        self,
        db: Session,
        school_id: UUID,
        notification_ids: List[UUID]
    ) -> int:
        """
        Bulk mark notifications as read.
        Returns count of updated rows.
        Only flushes - does not commit.
        """
        read_at = datetime.utcnow()
        return self.transport_notification_repo.bulk_mark_as_read(
            db, school_id, notification_ids, read_at
        )

    def mark_all_notifications_read_for_parent(
        self,
        db: Session,
        school_id: UUID,
        parent_id: UUID
    ) -> int:
        """
        Mark all unread notifications for a parent as read.
        Locks notifications by parent before update.
        Returns count of updated rows.
        Only flushes - does not commit.
        """
        # -------------------------------------
        # Step 1: Lock notifications by parent
        # -------------------------------------
        self.transport_notification_repo.lock_by_parent_for_update(db, school_id, parent_id)

        # -------------------------------------
        # Step 2: Bulk mark as read
        # -------------------------------------
        read_at = datetime.utcnow()
        return self.transport_notification_repo.bulk_mark_as_read_by_parent(
            db, school_id, parent_id, read_at
        )

    # =========================================
    # Student Transport Assignment
    # =========================================

    def assign_student_to_transport(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        bus_assignment_id: UUID,
        academic_year_id: UUID,
        pickup_stop_id: UUID,
        drop_stop_id: UUID,
        effective_from: datetime,
        effective_until: Optional[datetime] = None,
        status: Any = None
    ) -> Tuple[Optional[StudentTransport], bool]:
        """
        Assign student to transport with idempotency.
        Uses composite unique constraint (school_id, student_id, academic_year_id).
        Lock-first pattern to prevent race conditions.
        Returns (student_transport, is_new).
        Only flushes - does not commit.
        """

        if status is None:
            status = StudentTransportStatus.ACTIVE

        # -------------------------------------
        # Step 1: lock by composite unique
        # -------------------------------------
        locked_transport = (
            self.student_transport_repo
            .lock_by_student_and_academic_year_for_update(
                db,
                school_id,
                student_id,
                academic_year_id,
            )
        )

        if locked_transport:
            locked_transport.bus_assignment_id = bus_assignment_id
            locked_transport.pickup_stop_id = pickup_stop_id
            locked_transport.drop_stop_id = drop_stop_id
            locked_transport.effective_from = effective_from
            locked_transport.effective_until = effective_until
            locked_transport.status = status

            db.flush()
            return (locked_transport, False)

        # -------------------------------------
        # Step 2: verify bus assignment exists
        # -------------------------------------
        bus_assignment = self.bus_assignment_repo.get_by_id(
            db,
            school_id,
            bus_assignment_id,
        )

        if not bus_assignment:
            return (None, False)

        # -------------------------------------
        # Step 3: verify stops exist
        # -------------------------------------
        pickup_stop = self.route_stop_repo.get_by_id(
            db,
            school_id,
            pickup_stop_id,
        )

        drop_stop = self.route_stop_repo.get_by_id(
            db,
            school_id,
            drop_stop_id,
        )

        if not pickup_stop or not drop_stop:
            return (None, False)

        # -------------------------------------
        # Step 4: create new record
        # -------------------------------------
        student_transport = StudentTransport(
            school_id=school_id,
            student_id=student_id,
            bus_assignment_id=bus_assignment_id,
            pickup_stop_id=pickup_stop_id,
            drop_stop_id=drop_stop_id,
            academic_year_id=academic_year_id,
            status=status,
            effective_from=effective_from,
            effective_until=effective_until,
            is_deleted=False,
        )

        db.add(student_transport)
        db.flush()

        return (student_transport, True)

    def revoke_student_transport(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        academic_year_id: UUID,
        discontinuation_reason: Optional[str] = None
    ) -> bool:
        """
        Revoke student transport assignment.
        Locks student transport before update.
        Sets status to DISCONTINUED.
        Returns True if successful.
        Only flushes - does not commit.
        """
        
        # -------------------------------------
        # Step 1: Lock student transport
        # -------------------------------------
        student_transport = self.student_transport_repo.lock_by_student_and_academic_year_for_update(
            db, school_id, student_id, academic_year_id
        )

        if not student_transport:
            return False

        # -------------------------------------
        # Step 2: Update status to discontinued
        # -------------------------------------
        student_transport.status = StudentTransportStatus.DISCONTINUED
        if discontinuation_reason:
            student_transport.discontinuation_reason = discontinuation_reason
        
        db.flush()
        return True

    # =========================================
    # Bus Assignment Operations
    # =========================================

    def get_bus_assignments_for_date(
        self,
        db: Session,
        school_id: UUID,
        bus_id: UUID,
        trip_date: date
    ) -> List[BusAssignment]:
        """
        Get all bus assignments for a bus on a specific date.
        Locks all assignments for bus before returning.
        Used for trip planning.
        """
        # -------------------------------------
        # Step 1: Lock all assignments by bus
        # -------------------------------------
        assignments = self.bus_assignment_repo.lock_all_assignments_by_bus_for_update(
            db, school_id, bus_id
        )

        # -------------------------------------
        # Step 2: Filter by date range (effective_from/effective_until)
        # -------------------------------------
        filtered = []
        for assignment in assignments:
            if assignment.effective_from.date() <= trip_date:
                if assignment.effective_until is None or assignment.effective_until.date() >= trip_date:
                    filtered.append(assignment)

        return filtered

    # =========================================
    # Trip-Event Coordination
    # =========================================

    def get_trip_with_events(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve trip with all associated events.
        Uses explicit repository calls - no lazy loading.
        Returns dict with 'trip' and 'events' keys.
        """
        # -------------------------------------
        # Step 1: Get trip
        # -------------------------------------
        trip = self.transport_trip_repo.get_by_id(db, school_id, trip_id)
        
        if not trip:
            return None

        # -------------------------------------
        # Step 2: Get all events for trip (ordered by sequence)
        # -------------------------------------
        events = self.transport_event_repo.list_by_trip_ordered(db, school_id, trip_id)

        return {
            'trip': trip,
            'events': events
        }

    def get_trip_with_notifications(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve trip with all associated notifications.
        Uses explicit repository calls - no lazy loading.
        Returns dict with 'trip' and 'notifications' keys.
        """
        # -------------------------------------
        # Step 1: Get trip
        # -------------------------------------
        trip = self.transport_trip_repo.get_by_id(db, school_id, trip_id)
        
        if not trip:
            return None

        # -------------------------------------
        # Step 2: Get all notifications for trip
        # -------------------------------------
        notifications = self.transport_notification_repo.list_by_trip(db, school_id, trip_id)

        return {
            'trip': trip,
            'notifications': notifications
        }

    # =========================================
    # Bulk Trip Operations
    # =========================================

    def bulk_cancel_trips_by_assignment(
        self,
        db: Session,
        school_id: UUID,
        bus_assignment_id: UUID,
        trip_date: date,
    ) -> int:
        """
        Bulk cancel all trips for a bus assignment on a date.
        Locks all trips before cancellation.
        Returns count of cancelled trips.
        Only flushes - does not commit.
        """
        # -------------------------------------
        # Step 1: Lock all trips for assignment and date
        # -------------------------------------
        trips = self.transport_trip_repo.lock_all_trips_by_assignment_and_date_for_update(
            db, school_id, bus_assignment_id, trip_date
        )

        if not trips:
            return 0

        # -------------------------------------
        # Step 2: Cancel each trip
        # -------------------------------------
        cancelled_count = 0
        trip_ids = [trip.id for trip in trips]
        
        cancelled_count = self.transport_trip_repo.bulk_update_status(
            db, school_id, trip_ids, TripStatus.CANCELLED
        )

        db.flush()
        return cancelled_count

    # =========================================
    # Cross-Entity Reads (Tenant-Safe)
    # =========================================

    def get_student_transport_with_trip_details(
        self,
        db: Session,
        school_id: UUID,
        student_transport_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve student transport with associated trip details.
        Uses explicit repository calls - no lazy loading.
        Returns dict with 'student_transport', 'bus_assignment', and 'current_trip' keys.
        """
        # -------------------------------------
        # Step 1: Get student transport
        # -------------------------------------
        student_transport = self.student_transport_repo.get_by_id(db, school_id, student_transport_id)
        
        if not student_transport:
            return None

        # -------------------------------------
        # Step 2: Get bus assignment
        # -------------------------------------
        bus_assignment = self.bus_assignment_repo.get_by_id(
            db, school_id, student_transport.bus_assignment_id
        )

        # -------------------------------------
        # Step 3: Get current trip for today (if any)
        # -------------------------------------
        today = date.today()
        
        current_trip = None
        if bus_assignment:
            trips = self.transport_trip_repo.list_by_bus_assignment_and_date(
                db, school_id, student_transport.bus_assignment_id, today
            )
            if trips:
                current_trip = trips[0]  # Get first trip for today

        return {
            'student_transport': student_transport,
            'bus_assignment': bus_assignment,
            'current_trip': current_trip
        }

    # =========================================
    # Soft-Delete Orchestration
    # =========================================

    def soft_delete_trip_cascade(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID
    ) -> Dict[str, Any]:
        """
        Soft delete trip with cascade considerations.
        Note: Events and notifications are immutable logs - not deleted.
        Returns dict with deletion results.
        Only flushes - does not commit.
        """
        results = {
            'trip_deleted': False,
            'events_count': 0,
            'notifications_count': 0
        }

        # -------------------------------------
        # Step 1: Soft delete trip
        # -------------------------------------
        trip_deleted = self.transport_trip_repo.soft_delete(db, school_id, trip_id)
        results['trip_deleted'] = trip_deleted

        if trip_deleted:
            # -------------------------------------
            # Step 2: Count associated events (not deleted - immutable)
            # -------------------------------------
            results['events_count'] = self.transport_event_repo.count_by_trip(
                db, school_id, trip_id
            )

            # -------------------------------------
            # Step 3: Count associated notifications (not deleted - immutable)
            # -------------------------------------
            results['notifications_count'] = self.transport_notification_repo.count_by_trip(
                db, school_id, trip_id
            )

        db.flush()
        return results

    def restore_trip_cascade(
        self,
        db: Session,
        school_id: UUID,
        trip_id: UUID
    ) -> bool:
        """
        Restore soft-deleted trip.
        Events and notifications remain intact (immutable).
        Returns True if successful.
        Only flushes - does not commit.
        """
        return self.transport_trip_repo.restore(db, school_id, trip_id)