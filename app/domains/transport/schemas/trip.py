# domains/transport/schemas/trip.py


from pydantic import BaseModel, Field, validator
from typing import List, Optional, TYPE_CHECKING, Dict
from uuid import UUID
from datetime import datetime, timedelta
from .base import DomainBase, TimestampSchema

if TYPE_CHECKING:
    from .bus import BusReference
    from .driver import DriverReference
    from .route import RouteReference
    from app.domains.identity.schemas.student import StudentReference
else:
    BusReference = "BusReference"
    DriverReference = "DriverReference"
    RouteReference = "RouteReference"
    StudentReference = "StudentReference"

class BusAssignmentBase(BaseModel):
    effective_from: datetime
    effective_until: Optional[datetime] = None
    status: str = Field(..., pattern=r"^(active|completed|cancelled|upcoming)$")
    notes: Optional[str] = Field(None, max_length=500)

class BusAssignmentCreate(BusAssignmentBase):
    bus_id: UUID
    driver_id: UUID
    route_id: UUID
    academic_year_id: UUID
    created_by_id: UUID

class BusAssignmentUpdate(BaseModel):
    effective_until: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class BusAssignmentResponse(BusAssignmentBase, TimestampSchema):
    id: UUID
    bus_id: UUID
    driver_id: UUID
    route_id: UUID
    academic_year_id: UUID
    created_by_id: UUID
    is_deleted: bool
    bus: BusReference
    driver: DriverReference
    route: RouteReference
    current_trip: Optional["TransportTripSummary"] = None
    total_trips: int = 0

class TransportTripBase(BaseModel):
    trip_date: datetime
    trip_type: str = Field(..., pattern=r"^(pickup|drop)$", description="Morning pickup or evening drop")
    status: str = Field(..., pattern=r"^(scheduled|in_progress|completed|cancelled|delayed)$")
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    driver_notes: Optional[str] = Field(None, max_length=1000)
    delay_reason: Optional[str] = Field(None, max_length=500)
    estimated_completion_time: Optional[datetime] = None
    actual_completion_time: Optional[datetime] = None

    @validator('ended_at')
    def validate_trip_duration(cls, v, values):
        if v and values.get('started_at') and (v - values['started_at']) > timedelta(hours=8):
            raise ValueError('Trip duration cannot exceed 8 hours')
        return v

class TransportTripCreate(TransportTripBase):
    bus_assignment_id: UUID

class TransportTripUpdate(BaseModel):
    status: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    driver_notes: Optional[str] = None
    delay_reason: Optional[str] = None

class StudentTripStatus(BaseModel):
    """Student-specific trip status"""
    student_id: UUID
    student: StudentReference
    pickup_stop_id: Optional[UUID] = None
    drop_stop_id: Optional[UUID] = None
    pickup_confirmed: bool = False
    pickup_timestamp: Optional[datetime] = None
    drop_confirmed: bool = False
    drop_timestamp: Optional[datetime] = None
    is_on_board: bool = False

class TransportTripResponse(TransportTripBase, TimestampSchema):
    id: UUID
    bus_assignment_id: UUID
    is_deleted: bool
    bus_assignment: BusAssignmentResponse
    students: List[StudentTripStatus] = []
    total_students: int = 0
    students_picked_up: int = 0
    students_dropped: int = 0
    current_location: Optional[Dict] = Field(None, description="{'lat': float, 'lng': float, 'timestamp': datetime, 'speed': float}")
    eta_updates: List[Dict] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "d4e5f6a7-b8c9-0123-def4-567890123456",
                "bus_assignment_id": "assignment-uuid",
                "trip_date": "2026-02-19T00:00:00Z",
                "trip_type": "pickup",
                "status": "in_progress",
                "started_at": "2026-02-19T07:00:00Z",
                "ended_at": None,
                "driver_notes": "Heavy traffic near Sector 15 crossing",
                "delay_reason": "Traffic congestion at morning peak hour",
                "estimated_completion_time": "2026-02-19T08:15:00Z",
                "actual_completion_time": None,
                "created_at": "2026-02-18T18:00:00Z",
                "is_deleted": False,
                "bus_assignment": {
                    "id": "assignment-uuid",
                    "bus_id": "bus-uuid",
                    "driver_id": "driver-uuid",
                    "route_id": "route-uuid",
                    "effective_from": "2026-01-01T00:00:00Z",
                    "status": "active",
                    "bus": {
                        "id": "bus-uuid",
                        "bus_number": "BUS-001",
                        "registration_number": "DL01AB1234",
                        "capacity": 45,
                        "status": "active"
                    },
                    "driver": {
                        "id": "driver-uuid",
                        "staff_id": "staff-uuid",
                        "license_number": "DL9876543210",
                        "full_name": "Rajesh Kumar"
                    },
                    "route": {
                        "id": "route-uuid",
                        "name": "Route A - East Zone",
                        "total_stops": 8,
                        "status": "active"
                    },
                    "current_trip": None,
                    "total_trips": 120
                },
                "students": [
                    {
                        "student_id": "student-uuid-1",
                        "student": {
                            "id": "student-uuid-1",
                            "admission_number": "STU2026045",
                            "full_name": "Jamie Smith",
                            "class_name": "Grade 10",
                            "section_name": "A"
                        },
                        "pickup_stop_id": "stop-uuid-3",
                        "drop_stop_id": "stop-uuid-3",
                        "pickup_confirmed": True,
                        "pickup_timestamp": "2026-02-19T07:25:15Z",
                        "drop_confirmed": False,
                        "drop_timestamp": None,
                        "is_on_board": True
                    }
                ],
                "total_students": 24,
                "students_picked_up": 18,
                "students_dropped": 0,
                "current_location": {
                    "lat": 28.6892,
                    "lng": 77.1156,
                    "timestamp": "2026-02-19T07:45:23Z",
                    "speed": 28.5
                },
                "eta_updates": [
                    {
                        "timestamp": "2026-02-19T07:30:00Z",
                        "eta": "2026-02-19T08:00:00Z",
                        "reason": "normal_traffic"
                    },
                    {
                        "timestamp": "2026-02-19T07:40:00Z",
                        "eta": "2026-02-19T08:15:00Z",
                        "reason": "traffic_congestion"
                    }
                ]
            }
        }

class TransportTripSummary(BaseModel):
    """Compact trip summary for driver dashboard"""
    id: UUID
    trip_type: str
    status: str
    started_at: Optional[datetime] = None
    current_stop_sequence: int = 0
    students_picked_up: int = 0
    total_students: int = 0
    eta: Optional[datetime] = None

class TripAnalytics(BaseModel):
    """Trip performance analytics"""
    date: datetime
    total_trips: int = 0
    completed_trips: int = 0
    delayed_trips: int = 0
    average_delay_minutes: float = 0.0
    on_time_percentage: float = Field(default=0.0, ge=0, le=100)
    total_students_transported: int = 0
    safety_incidents: int = 0
    fuel_consumption_liters: Optional[float] = None

class TripCancellationRequest(BaseModel):
    """Request to cancel a scheduled trip"""
    trip_id: UUID
    reason: str = Field(..., min_length=10, max_length=500)
    notified_parents: bool = False
    alternative_arrangements: Optional[str] = Field(None, max_length=500)
    cancelled_by_id: UUID

# Resolve forward references
BusAssignmentResponse.model_rebuild()
TransportTripResponse.model_rebuild()