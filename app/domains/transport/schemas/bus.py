# transport/schemas/bus.py

from pydantic import BaseModel, Field, validator
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime, date
from .base import DomainBase, TimestampSchema

if TYPE_CHECKING:
    from .driver import DriverReference
    from .route import RouteReference
else:
    DriverReference = "DriverReference"
    RouteReference = "RouteReference"

class BusBase(DomainBase):
    bus_number: str = Field(..., min_length=2, max_length=20, pattern=r"^[A-Z0-9\-]{2,20}$")
    registration_number: str = Field(..., min_length=5, max_length=20, unique=True)
    make: Optional[str] = Field(None, max_length=50)
    model: Optional[str] = Field(None, max_length=50)
    year: Optional[int] = Field(None, ge=1990, le=2100)
    capacity: int = Field(..., ge=10, le=100)
    color: Optional[str] = Field(None, max_length=30)
    gps_device_id: Optional[str] = Field(None, max_length=100, unique=True)
    status: str = Field(..., pattern=r"^(active|maintenance|decommissioned|accident)$")
    insurance_expiry: Optional[date] = None
    permit_expiry: Optional[date] = None
    last_maintenance_date: Optional[date] = None
    next_maintenance_due: Optional[date] = None

    @validator('insurance_expiry', 'permit_expiry', 'next_maintenance_due')
    def validate_future_dates(cls, v):
        if v and v < date.today():
            raise ValueError('Expiry/maintenance date cannot be in the past')
        return v

class BusCreate(BusBase):
    school_id: UUID

class BusUpdate(BaseModel):
    bus_number: Optional[str] = None
    registration_number: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    capacity: Optional[int] = None
    color: Optional[str] = None
    gps_device_id: Optional[str] = None
    status: Optional[str] = None
    insurance_expiry: Optional[date] = None
    permit_expiry: Optional[date] = None
    next_maintenance_due: Optional[date] = None

class BusResponse(BusBase, TimestampSchema):
    id: UUID
    school_id: UUID
    is_deleted: bool
    current_driver: Optional[DriverReference] = None
    current_route: Optional[RouteReference] = None
    active_assignments: int = 0
    total_trips_today: int = 0
    last_location: Optional[dict] = Field(None, description="{'lat': float, 'lng': float, 'timestamp': datetime}")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "school_id": "school-uuid",
                "bus_number": "BUS-001",
                "registration_number": "DL01AB1234",
                "make": "Tata",
                "model": "Starbus",
                "year": 2022,
                "capacity": 45,
                "color": "Yellow",
                "gps_device_id": "GPS-DEVICE-7890",
                "status": "active",
                "insurance_expiry": "2027-03-31",
                "permit_expiry": "2026-12-31",
                "last_maintenance_date": "2026-01-15",
                "next_maintenance_due": "2026-07-15",
                "created_at": "2026-01-10T08:00:00Z",
                "is_deleted": False,
                "current_driver": {
                    "id": "driver-uuid",
                    "staff_id": "staff-uuid",
                    "license_number": "DL9876543210",
                    "full_name": "Rajesh Kumar"
                },
                "current_route": {
                    "id": "route-uuid",
                    "name": "Route A - East Zone",
                    "total_stops": 8
                },
                "active_assignments": 2,
                "total_trips_today": 2,
                "last_location": {
                    "lat": 28.6139,
                    "lng": 77.2090,
                    "timestamp": "2026-02-19T08:45:23Z"
                }
            }
        }

class BusReference(BaseModel):
    id: UUID
    bus_number: str
    registration_number: str
    capacity: int
    status: str

class BusMaintenanceBase(BaseModel):
    maintenance_type: str = Field(..., pattern=r"^(routine|repair|inspection|emergency)$")
    description: str = Field(..., min_length=10, max_length=1000)
    cost: Optional[float] = Field(None, ge=0)
    performed_by: str = Field(..., min_length=2, max_length=100)
    performed_at: datetime
    next_due_date: Optional[date] = None
    document_path: Optional[str] = Field(None, max_length=500)

class BusMaintenanceCreate(BusMaintenanceBase):
    bus_id: UUID
    created_by_id: UUID

class BusMaintenanceResponse(BusMaintenanceBase, TimestampSchema):
    id: UUID
    bus_id: UUID
    created_by_id: UUID
    is_deleted: bool
    bus: BusReference

# Resolve forward references
BusResponse.model_rebuild()
BusMaintenanceResponse.model_rebuild()