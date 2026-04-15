# transport/models/transit.py

from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, Boolean, Integer, Enum as SQLEnum, Index, Float, Text, UniqueConstraint
from datetime import datetime
import uuid
from types.types import UserRoleType
from types.transport import BusStatus, RouteStatus, DriverStatus, MaintenanceType
from db.base import Base 


# =========================
# BUS
# =========================

class Bus(Base):
    __tablename__ = "buses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    
    bus_number = Column(String, nullable=False)
    registration_number = Column(String, nullable=False)

    capacity = Column(Integer, nullable=False)
    gps_device_id = Column(String)

    status = Column(SQLEnum(BusStatus), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_buses_school_id", "school_id"),
        Index("ix_buses_status", "status"),
        UniqueConstraint("school_id", "bus_number", name="uq_bus_school_number"),
        UniqueConstraint("school_id", "registration_number", name="uq_bus_school_registration"),
        UniqueConstraint("school_id", "gps_device_id", name="uq_bus_school_gps")
    )


# =========================
# MAINTENANCE
# =========================

class BusMaintenance(Base):
    __tablename__ = "bus_maintenance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bus_id = Column(UUID(as_uuid=True), ForeignKey("buses.id"), nullable=False)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    maintenance_type = Column(SQLEnum(MaintenanceType), nullable=False)
    description = Column(Text, nullable=False)

    cost = Column(Float)
    performed_at = Column(DateTime, nullable=False)

    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_bus_maintenance_bus_id", "bus_id"),
        Index("ix_bus_maintenance_school_id", "school_id")
    )


class Route(Base):
    """
    Transport route definition
    """
    __tablename__ = "routes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    name = Column(String, nullable=False)  # "Route A - East Zone"
    description = Column(Text)
    distance_km = Column(Float)  # Approximate route distance
    estimated_duration_minutes = Column(Integer)  # Estimated travel time
    status = Column(SQLEnum(RouteStatus), nullable=False)  # "active", "inactive"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    
    __table_args__ = (
        Index('ix_routes_school_id', 'school_id'),
        Index('ix_routes_status', 'status'),
        UniqueConstraint("school_id", "name", name="uq_route_school_name")
    )


class RouteStop(Base):
    """
    Individual stops along a route with sequence
    """
    __tablename__ = "route_stops"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=False)
    stop_name = Column(String, nullable=False)
    address = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    sequence_order = Column(Integer, nullable=False)  # Stop sequence (1, 2, 3...)
    estimated_arrival_time = Column(DateTime)  # For morning pickup
    estimated_departure_time = Column(DateTime)  # For evening drop
    landmark = Column(String)  # Nearby landmark for identification
    contact_person = Column(String)
    contact_phone = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    
    __table_args__ = (
        Index('ix_route_stops_route_id', 'route_id'),
        Index('ix_route_stops_sequence', 'route_id', 'sequence_order'),
        Index('ix_route_stops_school_id', 'school_id'),
        UniqueConstraint("route_id", "sequence_order", name="uq_route_stop_sequence")
    ) 