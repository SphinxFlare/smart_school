# transport/schemas/event.py


from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, TYPE_CHECKING
from uuid import UUID
from datetime import datetime, timedelta
from .base import DomainBase
from types.types import TransportEventType

if TYPE_CHECKING:
    from app.domains.identity.schemas.student import StudentReference
    from .trip import TransportTripSummary
else:
    StudentReference = "StudentReference"
    TransportTripSummary = "TransportTripSummary"

class TransportEventBase(BaseModel):
    event_type: TransportEventType
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    timestamp: datetime
    metadata: Optional[Dict] = Field(default_factory=dict)

    @validator('metadata')
    def validate_metadata(cls, v, values):
        event_type = values.get('event_type')
        if event_type == TransportEventType.DELAY_REPORTED and not v.get('reason'):
            raise ValueError('Delay reason required in metadata for delay events')
        if event_type in [TransportEventType.SPEEDING, TransportEventType.HARSH_BRAKING, TransportEventType.AGGRESSIVE_DRIVING]:
            if v.get('speed', 0) <= 0:
                raise ValueError('Speed must be provided for driving behavior events')
        if event_type in [TransportEventType.PICKUP_CONFIRMED, TransportEventType.DROP_CONFIRMED] and not v.get('stop_name'):
            raise ValueError('Stop name required for pickup/drop confirmation events')
        return v

class TransportEventCreate(TransportEventBase):
    trip_id: UUID
    student_id: Optional[UUID] = None
    route_stop_id: Optional[UUID] = None

class TransportEventResponse(TransportEventBase):
    id: UUID
    trip_id: UUID
    student_id: Optional[UUID] = None
    route_stop_id: Optional[UUID] = None
    student: Optional[StudentReference] = None
    trip_summary: Optional[TransportTripSummary] = None

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "event_type": "pickup_confirmed",
                    "trip_id": "trip-uuid",
                    "student_id": "student-uuid",
                    "route_stop_id": "stop-uuid",
                    "timestamp": "2026-02-19T07:25:15Z",
                    "latitude": 28.6852,
                    "longitude": 77.1083,
                    "metadata": {
                        "stop_name": "Sector 10 Metro Station",
                        "stop_sequence": 3,
                        "driver_id": "driver-uuid",
                        "confirmation_method": "rfid_scan"
                    },
                    "student": {
                        "id": "student-uuid",
                        "admission_number": "STU2026045",
                        "full_name": "Jamie Smith",
                        "class_name": "Grade 10",
                        "section_name": "A"
                    }
                },
                {
                    "event_type": "speeding",
                    "trip_id": "trip-uuid",
                    "timestamp": "2026-02-19T07:42:18Z",
                    "latitude": 28.6912,
                    "longitude": 77.1198,
                    "metadata": {
                        "speed": 78.5,
                        "speed_limit": 60,
                        "duration_seconds": 35,
                        "location_description": "Near Sector 15 Market"
                    }
                },
                {
                    "event_type": "delay_reported",
                    "trip_id": "trip-uuid",
                    "timestamp": "2026-02-19T07:38:45Z",
                    "latitude": 28.6875,
                    "longitude": 77.1125,
                    "metadata": {
                        "reason": "traffic_congestion",
                        "estimated_delay_minutes": 15,
                        "location": "Sector 14 Crossing",
                        "reported_by": "driver"
                    }
                }
            ]
        }

class LiveLocationUpdate(BaseModel):
    """Real-time location streaming payload"""
    trip_id: UUID
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timestamp: datetime
    speed: float = Field(..., ge=0, le=200)
    heading: float = Field(..., ge=0, le=360)
    accuracy: float = Field(..., ge=0, le=100)
    battery_level: Optional[float] = Field(None, ge=0, le=100)
    is_moving: bool = True

    @validator('timestamp')
    def validate_timestamp_not_future(cls, v):
        if v > datetime.utcnow() + timedelta(minutes=5):
            raise ValueError('Timestamp cannot be more than 5 minutes in the future')
        return v

class ETACalculationRequest(BaseModel):
    """Request for ETA calculation"""
    trip_id: UUID
    current_location: Dict[str, float]  # {"lat": 28.6852, "lng": 77.1083}
    current_time: datetime
    traffic_conditions: str = Field(default="normal", pattern=r"^(normal|heavy|light)$")
    weather_conditions: str = Field(default="clear", pattern=r"^(clear|rain|fog|storm)$")

class ETAResponse(BaseModel):
    """ETA calculation response"""
    trip_id: UUID
    current_stop_sequence: int
    next_stop_id: UUID
    next_stop_name: str
    estimated_arrival_time: datetime
    estimated_delay_minutes: int = 0
    confidence_score: float = Field(..., ge=0, le=100)
    route_progress_percentage: float = Field(..., ge=0, le=100)
    traffic_impact: str = Field(..., pattern=r"^(none|low|medium|high)$")

# Resolve forward references
TransportEventResponse.model_rebuild()
ETAResponse.model_rebuild()