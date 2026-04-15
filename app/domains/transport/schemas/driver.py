# transport/schemas/driver.py


from pydantic import BaseModel, Field, validator, EmailStr
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime, date
from .base import DomainBase, TimestampSchema

if TYPE_CHECKING:
    from app.domains.identity.schemas.staff import StaffReference
    from .bus import BusReference
    from .trip import TransportTripSummary
else:
    StaffReference = "StaffReference"
    BusReference = "BusReference"
    TransportTripSummary = "TransportTripSummary"

class DriverBase(DomainBase):
    license_number: str = Field(..., min_length=5, max_length=30, unique=True)
    license_type: str = Field(..., min_length=2, max_length=20)
    license_expiry: date
    years_of_experience: int = Field(..., ge=0, le=50)
    emergency_contact_name: str = Field(..., min_length=2, max_length=100)
    emergency_contact_phone: str = Field(..., min_length=10, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)
    medical_fitness_certificate: Optional[str] = Field(None, max_length=500)
    medical_fitness_expiry: Optional[date] = None
    blood_group: Optional[str] = Field(None, max_length=10)
    address: Optional[str] = Field(None, max_length=300)
    status: str = Field(..., pattern=r"^(active|on_leave|suspended|terminated)$")

    @validator('license_expiry', 'medical_fitness_expiry')
    def validate_future_dates(cls, v):
        if v and v < date.today():
            raise ValueError('Expiry date cannot be in the past')
        return v

class DriverCreate(DriverBase):
    staff_member_id: UUID

class DriverUpdate(BaseModel):
    license_number: Optional[str] = None
    license_type: Optional[str] = None
    license_expiry: Optional[date] = None
    years_of_experience: Optional[int] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    medical_fitness_expiry: Optional[date] = None
    status: Optional[str] = None

class DriverResponse(DriverBase, TimestampSchema):
    id: UUID
    staff_member_id: UUID
    is_deleted: bool
    staff: StaffReference
    current_bus: Optional[BusReference] = None
    current_trip: Optional["TransportTripSummary"] = None
    total_trips_completed: int = 0
    safety_score: float = Field(default=100.0, ge=0, le=100)
    violations_count: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                "staff_member_id": "staff-uuid",
                "license_number": "DL9876543210",
                "license_type": "HMV",
                "license_expiry": "2028-05-31",
                "years_of_experience": 12,
                "emergency_contact_name": "Sunita Kumar",
                "emergency_contact_phone": "+91 9876543210",
                "emergency_contact_relationship": "Wife",
                "medical_fitness_certificate": "/documents/drivers/medical_fitness_rajesh.pdf",
                "medical_fitness_expiry": "2027-03-31",
                "blood_group": "B+",
                "address": "H.No 45, Sector 12, Rohini, New Delhi - 110085",
                "status": "active",
                "created_at": "2026-01-15T09:00:00Z",
                "is_deleted": False,
                "staff": {
                    "id": "staff-uuid",
                    "employee_id": "DRV2026001",
                    "full_name": "Rajesh Kumar",
                    "position": "Bus Driver",
                    "department": "Transport"
                },
                "current_bus": {
                    "id": "bus-uuid",
                    "bus_number": "BUS-001",
                    "registration_number": "DL01AB1234",
                    "capacity": 45,
                    "status": "active"
                },
                "current_trip": {
                    "id": "trip-uuid",
                    "trip_type": "pickup",
                    "status": "in_progress",
                    "started_at": "2026-02-19T07:00:00Z",
                    "current_stop_sequence": 3,
                    "students_picked_up": 18,
                    "total_students": 24
                },
                "total_trips_completed": 342,
                "safety_score": 98.5,
                "violations_count": 1
            }
        }

class DriverReference(BaseModel):
    id: UUID
    staff_id: UUID
    license_number: str
    full_name: str

class DriverPerformanceMetrics(BaseModel):
    """Driver performance analytics"""
    driver_id: UUID
    driver_name: str
    period_start: date
    period_end: date
    total_trips: int = 0
    on_time_percentage: float = Field(default=0.0, ge=0, le=100)
    average_speed_kmph: float = Field(default=0.0, ge=0)
    harsh_braking_count: int = 0
    speeding_incidents: int = 0
    student_complaints: int = 0
    safety_score: float = Field(default=100.0, ge=0, le=100)
    recommendations: List[str] = []

class DriverAssignmentSummary(BaseModel):
    """Current assignment details"""
    driver_id: UUID
    bus_number: str
    route_name: str
    trip_type: str
    scheduled_start: datetime
    status: str

# Resolve forward references
DriverResponse.model_rebuild()
DriverPerformanceMetrics.model_rebuild()