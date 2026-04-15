# transport/schemas/notification.py


from pydantic import BaseModel, Field, validator
from typing import Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from .base import DomainBase

if TYPE_CHECKING:
    from app.domains.identity.schemas.student import StudentReference
    from app.domains.identity.schemas.parent import ParentReference
else:
    StudentReference = "StudentReference"
    ParentReference = "ParentReference"

class TransportNotificationBase(BaseModel):
    notification_type: str = Field(
        ...,
        pattern=r"^(pickup_confirmed|drop_confirmed|delay_alert|eta_update|safety_alert|trip_cancelled)$"
    )
    title: str = Field(..., min_length=3, max_length=100)
    message: str = Field(..., min_length=5, max_length=500)
    priority: str = Field(default="normal", pattern=r"^(low|normal|high|urgent)$")
    action_url: Optional[str] = Field(None, max_length=200)

class TransportNotificationCreate(TransportNotificationBase):
    trip_id: UUID
    student_id: UUID
    parent_id: UUID
    sent_at: datetime

class TransportNotificationUpdate(BaseModel):
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    is_delivered: Optional[bool] = None
    is_read: Optional[bool] = None

class TransportNotificationResponse(TransportNotificationBase):
    id: UUID
    trip_id: UUID
    student_id: UUID
    parent_id: UUID
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    is_delivered: bool = False
    is_read: bool = False
    student: StudentReference
    parent: ParentReference

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "id": "e5f6a7b8-c9d0-1234-ef56-789012345678",
                    "trip_id": "trip-uuid",
                    "student_id": "student-uuid",
                    "parent_id": "parent-uuid",
                    "notification_type": "pickup_confirmed",
                    "title": "Jamie has boarded the bus",
                    "message": "Your child Jamie Smith (Grade 10-A) has been picked up from Sector 10 Metro Station at 7:25 AM. Bus BUS-001 is proceeding to school.",
                    "priority": "normal",
                    "action_url": "/app/transport/trip/trip-uuid",
                    "sent_at": "2026-02-19T07:25:20Z",
                    "delivered_at": "2026-02-19T07:25:22Z",
                    "read_at": "2026-02-19T07:26:15Z",
                    "is_delivered": True,
                    "is_read": True,
                    "student": {
                        "id": "student-uuid",
                        "admission_number": "STU2026045",
                        "full_name": "Jamie Smith",
                        "class_name": "Grade 10",
                        "section_name": "A"
                    },
                    "parent": {
                        "id": "parent-uuid",
                        "full_name": "Maria Rodriguez",
                        "email": "maria.rodriguez@email.com",
                        "phone": "+91 9876543210"
                    }
                },
                {
                    "notification_type": "delay_alert",
                    "title": "Bus Delay Alert",
                    "message": "Bus BUS-001 is delayed by approximately 15 minutes due to traffic congestion near Sector 14 Crossing. New ETA: 8:15 AM.",
                    "priority": "high",
                    "sent_at": "2026-02-19T07:40:00Z"
                }
            ]
        }

class NotificationPreferences(BaseModel):
    """Parent notification preferences for transport"""
    parent_id: UUID
    enable_pickup_notifications: bool = True
    enable_drop_notifications: bool = True
    enable_delay_notifications: bool = True
    enable_safety_alerts: bool = True
    notification_channels: list[str] = Field(
        default=["push", "sms"],
        min_items=1,
        unique_items=True,
        pattern=r"^(push|sms|email|whatsapp)$"
    )
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    quiet_hours_end: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")

class NotificationStatistics(BaseModel):
    """Notification delivery statistics"""
    date: datetime
    total_sent: int = 0
    delivered: int = 0
    read: int = 0
    failed: int = 0
    delivery_rate: float = Field(default=0.0, ge=0, le=100)
    read_rate: float = Field(default=0.0, ge=0, le=100)
    avg_delivery_time_seconds: float = 0.0
    by_type: dict[str, int] = Field(default_factory=dict)

# Resolve forward references
TransportNotificationResponse.model_rebuild()