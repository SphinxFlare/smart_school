# communication/schemas/notification.py


from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, TYPE_CHECKING, Literal
from uuid import UUID
from datetime import datetime
from .base import DomainBase, TimestampSchema

if TYPE_CHECKING:
    from app.domains.identity.schemas.user import UserReference
else:
    UserReference = "UserReference"

class NotificationChannel(BaseModel):
    """Notification delivery channels"""
    type: Literal["push", "email", "sms", "whatsapp", "in_app"] = "in_app"
    enabled: bool = True
    device_token: Optional[str] = Field(None, max_length=500)
    email_address: Optional[str] = None
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20)

class NotificationBase(DomainBase):
    """
    Base schema for user notifications
    """
    title: str = Field(..., min_length=3, max_length=150)
    message: str = Field(..., min_length=5, max_length=1000)
    notification_type: str = Field(
        ...,
        pattern=r"^(transport|attendance|exam|fee|concern|message|system|announcement)$",
        description="Category of notification"
    )
    priority: str = Field(
        default="normal",
        pattern=r"^(low|normal|high|urgent)$",
        description="Notification priority"
    )
    entity_type: Optional[str] = Field(
        None,
        max_length=50,
        description="Type of related entity (e.g., 'transport_trip', 'fee_payment')"
    )
    entity_id: Optional[UUID] = Field(
        None,
        description="ID of related entity for deep linking"
    )
    action_url: Optional[str] = Field(
        None,
        max_length=500,
        description="Deep link to relevant screen in app"
    )
    image_url: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict] = Field(
        default_factory=dict,
        description="Additional context data"
    )

class NotificationCreate(NotificationBase):
    """
    Schema for creating a notification
    """
    user_id: UUID
    sent_at: datetime = Field(default_factory=datetime.utcnow)

class NotificationUpdate(BaseModel):
    """
    Schema for updating notification status
    """
    is_read: Optional[bool] = None
    read_at: Optional[datetime] = None
    is_archived: Optional[bool] = None

class NotificationResponse(NotificationBase, TimestampSchema):
    """
    Response schema for notification with user context
    """
    id: UUID
    user_id: UUID
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    is_delivered: bool = False
    is_read: bool = False
    is_archived: bool = False
    expires_at: Optional[datetime] = None
    user: Optional[UserReference] = None

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "user_id": "user-uuid",
                    "title": "Jamie has boarded the bus",
                    "message": "Your child Jamie Smith (Grade 10-A) has been picked up from Sector 10 Metro Station at 7:25 AM. Bus BUS-001 is proceeding to school.",
                    "notification_type": "transport",
                    "priority": "normal",
                    "entity_type": "transport_trip",
                    "entity_id": "trip-uuid",
                    "action_url": "/app/transport/trip/trip-uuid",
                    "image_url": "https://school.edu/images/bus-icon.png",
                    "metadata": {
                        "bus_number": "BUS-001",
                        "driver_name": "Rajesh Kumar",
                        "pickup_time": "2026-02-19T07:25:15Z",
                        "stop_name": "Sector 10 Metro Station"
                    },
                    "sent_at": "2026-02-19T07:25:20Z",
                    "delivered_at": "2026-02-19T07:25:22Z",
                    "read_at": "2026-02-19T07:26:15Z",
                    "is_delivered": True,
                    "is_read": True,
                    "is_archived": False,
                    "created_at": "2026-02-19T07:25:20Z",
                    "user": {
                        "id": "user-uuid",
                        "full_name": "Maria Rodriguez",
                        "email": "maria.rodriguez@email.com",
                        "role": "parent"
                    }
                },
                {
                    "title": "Fee Payment Due",
                    "message": "Annual tuition fee of ₹45,000 is due by April 30, 2026. Please make payment to avoid late fees.",
                    "notification_type": "fee",
                    "priority": "high",
                    "entity_type": "student_fee",
                    "entity_id": "student-fee-uuid",
                    "action_url": "/app/finance/payments",
                    "sent_at": "2026-02-15T10:00:00Z",
                    "priority": "high"
                },
                {
                    "title": "Quarterly Exam Results Published",
                    "message": "Your child's quarterly exam results are now available. Overall percentage: 87%",
                    "notification_type": "exam",
                    "priority": "normal",
                    "entity_type": "exam_result",
                    "entity_id": "exam-result-uuid",
                    "action_url": "/app/academics/results",
                    "sent_at": "2026-02-18T14:30:00Z"
                }
            ]
        }

class NotificationFilter(BaseModel):
    """
    Filter schema for notification queries
    """
    user_id: Optional[UUID] = None
    notification_type: Optional[str] = None
    priority: Optional[str] = None
    is_read: Optional[bool] = None
    is_delivered: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    entity_type: Optional[str] = None
    include_archived: bool = False
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v and values.get('date_from') and v < values['date_from']:
            raise ValueError('date_to must be after date_from')
        return v

class NotificationStatistics(BaseModel):
    """
    Notification delivery and engagement statistics
    """
    total_sent: int = 0
    delivered: int = 0
    read: int = 0
    failed: int = 0
    delivery_rate: float = Field(default=0.0, ge=0, le=100)
    read_rate: float = Field(default=0.0, ge=0, le=100)
    avg_delivery_time_seconds: float = 0.0
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_priority: Dict[str, int] = Field(default_factory=dict)
    by_channel: Dict[str, int] = Field(default_factory=dict)

class BulkNotificationCreate(BaseModel):
    """
    Schema for creating notifications for multiple users
    """
    user_ids: list[UUID] = Field(..., min_items=1, max_items=1000)
    title: str = Field(..., min_length=3, max_length=150)
    message: str = Field(..., min_length=5, max_length=1000)
    notification_type: str
    priority: str = "normal"
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    action_url: Optional[str] = None
    send_immediately: bool = True

    @validator('user_ids')
    def validate_unique_users(cls, v):
        if len(set(v)) != len(v):
            raise ValueError('Duplicate user IDs not allowed')
        return v

class NotificationPreferenceUpdate(BaseModel):
    """
    Update user notification preferences
    """
    user_id: UUID
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    transport_notifications: Optional[bool] = None
    attendance_notifications: Optional[bool] = None
    exam_notifications: Optional[bool] = None
    fee_notifications: Optional[bool] = None
    concern_notifications: Optional[bool] = None
    message_notifications: Optional[bool] = None
    system_notifications: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    quiet_hours_end: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")

class NotificationDeliveryLog(BaseModel):
    """
    Detailed delivery log for a notification
    """
    notification_id: UUID
    channel: str
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    status: str = Field(..., pattern=r"^(sent|delivered|failed|pending)$")
    provider_response: Optional[Dict] = None
    error_message: Optional[str] = None
    retry_count: int = 0

# Resolve forward references
NotificationResponse.model_rebuild()