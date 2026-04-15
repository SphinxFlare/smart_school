# finance/schemas/fee_reminder.py


from pydantic import BaseModel, Field, validator, EmailStr
from typing import List, Optional, TYPE_CHECKING, Literal
from uuid import UUID
from datetime import datetime
from .base import DomainBase

if TYPE_CHECKING:
    from app.domains.identity.schemas.student import StudentReference
    from app.domains.identity.schemas.parent import ParentReference
else:
    StudentReference = "StudentReference"
    ParentReference = "ParentReference"

class ReminderChannel(BaseModel):
    """Channel configuration for reminders"""
    type: Literal["email", "sms", "notification", "whatsapp"] = "email"
    enabled: bool = True
    template_id: Optional[str] = Field(None, max_length=100)
    custom_message: Optional[str] = Field(None, max_length=1000)

class FeeReminderBase(DomainBase):
    reminder_date: datetime
    reminder_type: str = Field(
        ...,
        pattern=r"^(initial|first_followup|second_followup|final_notice)$"
    )
    days_before_due: int = Field(..., ge=0, le=90)
    message_template: Optional[str] = Field(None, max_length=2000)
    channels: List[ReminderChannel] = Field(default_factory=list)
    is_sent: bool = False

class FeeReminderCreate(FeeReminderBase):
    student_fee_id: UUID
    student_id: UUID

class FeeReminderUpdate(BaseModel):
    is_sent: Optional[bool] = None
    sent_at: Optional[datetime] = None
    sent_to_parent_ids: Optional[List[UUID]] = None

class FeeReminderResponse(FeeReminderBase):
    id: UUID
    student_fee_id: UUID
    student_id: UUID
    sent_at: Optional[datetime] = None
    sent_to_parent_ids: Optional[List[UUID]] = None
    student: StudentReference
    sent_to_parents: Optional[List[ParentReference]] = None
    delivery_status: dict = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "f6a7b8c9-d0e1-2345-f678-901234567890",
                "student_fee_id": "student-fee-uuid",
                "student_id": "student-uuid",
                "reminder_date": "2026-04-15T09:00:00Z",
                "reminder_type": "first_followup",
                "days_before_due": 15,
                "message_template": "Dear Parent, This is a reminder that fee payment of ₹{amount} is due on {due_date}. Please pay at your earliest convenience.",
                "channels": [
                    {
                        "type": "email",
                        "enabled": True,
                        "template_id": "fee_reminder_email_v1"
                    },
                    {
                        "type": "sms",
                        "enabled": True,
                        "template_id": "fee_reminder_sms_v1"
                    }
                ],
                "is_sent": True,
                "sent_at": "2026-04-15T09:05:23Z",
                "sent_to_parent_ids": ["parent-uuid-1", "parent-uuid-2"],
                "student": {
                    "id": "student-uuid",
                    "admission_number": "STU2026045",
                    "full_name": "Jamie Smith",
                    "class_name": "Grade 10",
                    "section_name": "A"
                },
                "sent_to_parents": [
                    {
                        "id": "parent-uuid-1",
                        "full_name": "Maria Rodriguez",
                        "email": "maria.rodriguez@email.com",
                        "phone": "+91 9876543210"
                    }
                ],
                "delivery_status": {
                    "email": {"sent": 1, "delivered": 1, "opened": 1, "failed": 0},
                    "sms": {"sent": 1, "delivered": 1, "failed": 0}
                }
            }
        }

class BulkFeeReminderCreate(BaseModel):
    """Create reminders for multiple students"""
    student_fee_ids: List[UUID] = Field(..., min_items=1, max_items=1000)
    reminder_type: str = Field(..., pattern=r"^(initial|first_followup|second_followup|final_notice)$")
    days_before_due: int = Field(..., ge=0, le=90)
    channels: List[ReminderChannel] = Field(default_factory=list)
    schedule_date: Optional[datetime] = None  # None = send immediately

    @validator('student_fee_ids')
    def validate_ids_unique(cls, v):
        if len(set(v)) != len(v):
            raise ValueError('Duplicate student fee IDs not allowed')
        return v

class ReminderStatistics(BaseModel):
    """Statistics for fee reminders"""
    total_reminders: int = 0
    sent_reminders: int = 0
    pending_reminders: int = 0
    failed_reminders: int = 0
    reminders_by_type: dict[str, int] = Field(default_factory=dict)
    delivery_rates: dict[str, float] = Field(default_factory=dict)
    response_rate: float = Field(default=0.0, ge=0, le=100)  # Percentage who paid after reminder

class ReminderLog(BaseModel):
    """Detailed log of reminder delivery"""
    reminder_id: UUID
    channel: str
    recipient_id: UUID
    recipient_type: str  # "parent", "student"
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    status: str  # "sent", "delivered", "opened", "failed"
    error_message: Optional[str] = None
    metadata: Optional[dict] = Field(default_factory=dict)

# Resolve forward references
FeeReminderResponse.model_rebuild()