# transport/models/tracking.py


from sqlalchemy import (
    Column, String, UUID, ForeignKey, DateTime, Float, Text, Boolean, Integer,
    Enum as SQLEnum, Date, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timedelta
import uuid
from types.types import TransportEventType
from types.transport import TripType, TransportNotificationType, TripStatus
from db.base import Base


class TransportTrip(Base):
    """
    Daily transport trip session (morning pickup or evening drop)
    """
    __tablename__ = "transport_trips"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    bus_assignment_id = Column(UUID(as_uuid=True), ForeignKey("bus_assignments.id"), nullable=False)
    trip_date = Column(Date, nullable=False)
    trip_type = Column(SQLEnum(TripType), nullable=False)  # "pickup", "drop"
    status = Column(SQLEnum(TripStatus), nullable=False)  # "scheduled", "in_progress", "completed", "cancelled"
    started_at = Column(DateTime)  # When driver started the trip
    ended_at = Column(DateTime)  # When trip completed
    driver_notes = Column(Text)
    delay_reason = Column(Text)  # If trip was delayed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    
    __table_args__ = (
        UniqueConstraint("school_id", 'bus_assignment_id', 'trip_date', 'trip_type', name='uq_bus_trip_date_type'),
        Index('ix_transport_trips_bus_assignment', 'bus_assignment_id'),
        Index('ix_transport_trips_trip_date', 'trip_date'),
        Index('ix_transport_trips_status', 'status'),
        Index("ix_transport_trips_school_id", "school_id")
    )


class TransportEvent(Base):
    """
    Real-time transport events: confirmations, telemetry, delays
    """
    __tablename__ = "transport_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("transport_trips.id"), nullable=False)
    event_type = Column(SQLEnum(TransportEventType), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    route_stop_id = Column(UUID(as_uuid=True), ForeignKey("route_stops.id"))
    latitude = Column(Float)
    longitude = Column(Float)
    timestamp = Column(DateTime, nullable=False)
    event_payload = Column(JSONB)  # Additional data: {"speed": 60, "reason": "traffic"}
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_transport_events_trip_id', 'trip_id'),
        Index('ix_transport_events_student_id', 'student_id'),
        Index('ix_transport_events_timestamp', 'timestamp'),
        Index('ix_transport_events_event_type', 'event_type'),
        Index("ix_transport_events_school_id", "school_id")
    )


class TransportNotification(Base):
    """
    Parent notifications for transport events
    """
    __tablename__ = "transport_notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("transport_trips.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("parents.id"), nullable=False)
    notification_type = Column(SQLEnum(TransportNotificationType), nullable=False)  # "pickup_confirmed", "drop_confirmed", "delay_alert", "eta_update"
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    is_delivered = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_transport_notifications_student_id', 'student_id'),
        Index('ix_transport_notifications_parent_id', 'parent_id'),
        Index('ix_transport_notifications_sent_at', 'sent_at'),
        Index("ix_transport_notifications_school_id", "school_id")
    )