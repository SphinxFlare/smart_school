# transport/schemas/route.py


from pydantic import BaseModel, Field, validator
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime, time
from .base import DomainBase, TimestampSchema

if TYPE_CHECKING:
    from .bus import BusReference
else:
    BusReference = "BusReference"

class RouteBase(DomainBase):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    distance_km: Optional[float] = Field(None, ge=0.1, le=200.0)
    estimated_duration_minutes: Optional[int] = Field(None, ge=5, le=300)
    status: str = Field(default="active", pattern=r"^(active|inactive|suspended)$")
    direction: str = Field(default="bidirectional", pattern=r"^(bidirectional|pickup_only|drop_only)$")

class RouteCreate(RouteBase):
    school_id: UUID

class RouteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    distance_km: Optional[float] = None
    estimated_duration_minutes: Optional[int] = None
    status: Optional[str] = None
    direction: Optional[str] = None

class RouteStopBase(BaseModel):
    stop_name: str = Field(..., min_length=2, max_length=100)
    address: str = Field(..., min_length=5, max_length=300)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    sequence_order: int = Field(..., ge=1)
    estimated_arrival_time: Optional[time] = None
    estimated_departure_time: Optional[time] = None
    landmark: Optional[str] = Field(None, max_length=100)
    contact_person: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, min_length=10, max_length=20)

    @validator('estimated_departure_time')
    def validate_time_sequence(cls, v, values):
        if v and values.get('estimated_arrival_time') and v <= values['estimated_arrival_time']:
            raise ValueError('Departure time must be after arrival time')
        return v

class RouteStopCreate(RouteStopBase):
    route_id: UUID

class RouteStopUpdate(BaseModel):
    stop_name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    sequence_order: Optional[int] = None
    estimated_arrival_time: Optional[time] = None
    estimated_departure_time: Optional[time] = None
    landmark: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None

class RouteStopResponse(RouteStopBase, TimestampSchema):
    id: UUID
    route_id: UUID
    is_deleted: bool

class RouteResponse(RouteBase, TimestampSchema):
    id: UUID
    school_id: UUID
    is_deleted: bool
    total_stops: int = 0
    active_buses: int = 0
    stops: List[RouteStopResponse] = []
    assigned_buses: List[BusReference] = []

    class Config:
        json_schema_extra = {
            "example": {
                "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "school_id": "school-uuid",
                "name": "Route A - East Zone",
                "description": "Covers Rohini sectors 10-18 with 8 stops",
                "distance_km": 12.5,
                "estimated_duration_minutes": 45,
                "status": "active",
                "direction": "bidirectional",
                "created_at": "2026-01-05T10:00:00Z",
                "is_deleted": False,
                "total_stops": 8,
                "active_buses": 2,
                "stops": [
                    {
                        "id": "stop-uuid-1",
                        "route_id": "route-uuid",
                        "stop_name": "Sector 10 Metro Station",
                        "address": "Near Metro Pillar 45, Sector 10, Rohini",
                        "latitude": 28.6852,
                        "longitude": 77.1083,
                        "sequence_order": 1,
                        "estimated_arrival_time": "07:15:00",
                        "estimated_departure_time": "07:20:00",
                        "landmark": "Metro Station Entrance",
                        "contact_person": "Security Guard",
                        "contact_phone": "+91 9876543210",
                        "created_at": "2026-01-05T10:30:00Z",
                        "is_deleted": False
                    }
                ],
                "assigned_buses": [
                    {
                        "id": "bus-uuid-1",
                        "bus_number": "BUS-001",
                        "registration_number": "DL01AB1234",
                        "capacity": 45,
                        "status": "active"
                    }
                ]
            }
        }

class RouteReference(BaseModel):
    id: UUID
    name: str
    total_stops: int
    status: str

class RouteOptimizationRequest(BaseModel):
    """Request for route optimization analysis"""
    route_id: UUID
    optimization_criteria: str = Field(
        default="shortest_time",
        pattern=r"^(shortest_time|shortest_distance|minimum_stops|balanced)$"
    )
    traffic_conditions: str = Field(default="normal", pattern=r"^(normal|heavy|light)$")
    time_window: Optional[tuple[time, time]] = None
    max_detour_minutes: int = Field(default=10, ge=0, le=60)

# Resolve forward references
RouteResponse.model_rebuild()