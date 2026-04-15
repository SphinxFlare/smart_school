# transport/models/allocations.py


from sqlalchemy import (
    Column, String, UUID, ForeignKey, DateTime, Boolean, Text,
    UniqueConstraint, Index, Enum as SQLEnum
)
from datetime import datetime
import uuid
from db.base import Base
from types.transport import AssignmentStatus, StudentTransportStatus


class BusAssignment(Base):
    """
    Bus-driver-route assignment for specific period
    """
    __tablename__ = "bus_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bus_id = Column(UUID(as_uuid=True), ForeignKey("buses.id"), nullable=False)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=False)
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=False)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False)
    effective_from = Column(DateTime, nullable=False)
    effective_until = Column(DateTime)
    status = Column(SQLEnum(AssignmentStatus), nullable=False)  # "active", "completed", "cancelled"
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    
    __table_args__ = (
        Index('ix_bus_assignments_bus_id', 'bus_id'),
        Index("ix_bus_assignments_school_id", "school_id"),
        Index('ix_bus_assignments_driver_id', 'driver_id'),
        Index('ix_bus_assignments_route_id', 'route_id'),
        Index('ix_bus_assignments_effective_period', 'effective_from', 'effective_until'),
        UniqueConstraint(
            "school_id",
            "bus_id",
            "academic_year_id",
            "effective_from",
            name="uq_bus_assignment_period"
        )
    )  


class StudentTransport(Base):
    """
    Student assignment to specific bus route with pickup/drop stops
    """
    __tablename__ = "student_transport"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    bus_assignment_id = Column(UUID(as_uuid=True), ForeignKey("bus_assignments.id"), nullable=False)
    pickup_stop_id = Column(UUID(as_uuid=True), ForeignKey("route_stops.id"), nullable=False)
    drop_stop_id = Column(UUID(as_uuid=True), ForeignKey("route_stops.id"), nullable=False)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False)
    status = Column(SQLEnum(StudentTransportStatus), nullable=False)  # "active", "on_hold", "discontinued"
    discontinuation_reason = Column(Text)
    effective_from = Column(DateTime, nullable=False)
    effective_until = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    
    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "student_id",
            "academic_year_id",
            name="uq_student_transport_year"
        ),
        Index('ix_student_transport_student_id', 'student_id'),
        Index('ix_student_transport_bus_assignment', 'bus_assignment_id'),
        Index("ix_student_transport_school_id", "school_id")
    )