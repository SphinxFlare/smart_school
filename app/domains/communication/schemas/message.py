# communication/schemas/message.py


from pydantic import BaseModel, Field, validator
from typing import List, Optional, TYPE_CHECKING, Dict
from uuid import UUID
from datetime import datetime
from .base import DomainBase, TimestampSchema

if TYPE_CHECKING:
    from app.domains.identity.schemas.user import UserReference
else:
    UserReference = "UserReference"

class MessageAttachment(BaseModel):
    """
    Message attachment metadata
    """
    name: str = Field(..., min_length=1, max_length=200)
    file_path: str = Field(..., max_length=500)
    file_type: str = Field(..., pattern=r"^(pdf|docx|jpg|png|zip|mp4|mp3)$")
    file_size_kb: int = Field(..., ge=1, le=51200)  # Max 50MB
    uploaded_at: datetime

class MessageBase(DomainBase):
    """
    Base schema for messages
    """
    subject: Optional[str] = Field(None, max_length=200)
    body: str = Field(..., min_length=1, max_length=5000)
    context_type: Optional[str] = Field(
        None,
        pattern=r"^(attendance|academics|concern|transport|fee|general)$",
        description="Context category"
    )
    context_id: Optional[UUID] = None
    is_two_way: bool = Field(default=True, description="False = announcement-style, True = conversation")
    allow_replies: bool = Field(default=True)
    priority: str = Field(default="normal", pattern=r"^(low|normal|high|urgent)$")
    attachments: List[MessageAttachment] = Field(default_factory=list)
    is_draft: bool = False
    scheduled_send_time: Optional[datetime] = None

class MessageCreate(MessageBase):
    """
    Schema for creating a message
    """
    sender_id: UUID
    recipient_ids: List[UUID] = Field(..., min_items=1, max_items=100)

    @validator('recipient_ids')
    def validate_recipients_unique(cls, v):
        if len(set(v)) != len(v):
            raise ValueError('Duplicate recipients not allowed')
        return v

class MessageReplyCreate(BaseModel):
    """
    Schema for replying to a message
    """
    message_id: UUID
    parent_reply_id: Optional[UUID] = None
    sender_id: UUID
    body: str = Field(..., min_length=1, max_length=2000)
    attachments: List[MessageAttachment] = Field(default_factory=list)

class MessageRecipientStatus(BaseModel):
    """
    Status of message for each recipient
    """
    recipient_id: UUID
    recipient_role: str
    delivery_status: str = Field(default="sent", pattern=r"^(sent|delivered|read|failed)$")
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    is_read: bool = False
    is_starred: bool = False
    deleted_by_recipient: bool = False
    recipient: Optional[UserReference] = None

class MessageResponse(MessageBase, TimestampSchema):
    """
    Response schema for message
    """
    id: UUID
    sender_id: UUID
    is_deleted: bool
    sent_at: datetime
    sender: UserReference
    recipients: List[MessageRecipientStatus] = []
    reply_count: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "id": "d4e5f6a7-b8c9-0123-def4-567890123456",
                "sender_id": "teacher-uuid",
                "subject": "Regarding Jamie's Recent Behavior",
                "body": "Dear Parent,\n\nI wanted to inform you about Jamie's recent behavior in class. While Jamie is generally a good student, there have been a few instances of disruption during mathematics lessons this week.\n\nI believe this is temporary and with your support at home, we can help Jamie get back on track. Please let me know if we can schedule a brief meeting to discuss this further.\n\nThank you for your understanding and cooperation.\n\nBest regards,\nMs. Sarah Chen\nMathematics Teacher\nGrade 10-A",
                "context_type": "concern",
                "context_id": "concern-uuid",
                "is_two_way": True,
                "allow_replies": True,
                "priority": "normal",
                "attachments": [],
                "is_draft": False,
                "sent_at": "2026-02-17T15:30:00Z",
                "created_at": "2026-02-17T15:30:00Z",
                "is_deleted": False,
                "sender": {
                    "id": "teacher-uuid",
                    "full_name": "Ms. Sarah Chen",
                    "email": "s.chen@school.edu",
                    "role": "teacher"
                },
                "recipients": [
                    {
                        "recipient_id": "parent-uuid",
                        "recipient_role": "parent",
                        "delivery_status": "delivered",
                        "delivered_at": "2026-02-17T15:30:05Z",
                        "read_at": "2026-02-17T15:45:23Z",
                        "is_read": True,
                        "is_starred": False,
                        "deleted_by_recipient": False,
                        "recipient": {
                            "id": "parent-uuid",
                            "full_name": "Maria Rodriguez",
                            "email": "maria.rodriguez@email.com",
                            "role": "parent"
                        }
                    }
                ],
                "reply_count": 1
            }
        }

class MessageWithReplies(MessageResponse):
    """
    Message with all replies
    """
    replies: List["MessageReplyResponse"] = []

class MessageReplyResponse(BaseModel):
    """
    Response schema for message reply
    """
    id: UUID
    message_id: UUID
    parent_reply_id: Optional[UUID] = None
    sender_id: UUID
    body: str
    attachments: List[MessageAttachment]
    sent_at: datetime
    is_deleted: bool
    sender: UserReference

class MessageFilter(BaseModel):
    """
    Filter schema for message queries
    """
    user_id: UUID
    folder: str = Field(default="inbox", pattern=r"^(inbox|sent|drafts|starred|archived)$")
    context_type: Optional[str] = None
    priority: Optional[str] = None
    is_read: Optional[bool] = None
    has_replies: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search_query: Optional[str] = Field(None, max_length=200)
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

class MessageStatistics(BaseModel):
    """
    Message statistics for user dashboard
    """
    total_messages: int = 0
    unread_count: int = 0
    sent_count: int = 0
    draft_count: int = 0
    starred_count: int = 0
    avg_response_time_hours: float = 0.0
    messages_by_context: Dict[str, int] = Field(default_factory=dict)
    messages_by_priority: Dict[str, int] = Field(default_factory=dict)
    recent_conversations: List[Dict] = Field(default_factory=list)

# Resolve forward references
MessageWithReplies.model_rebuild()
MessageReplyResponse.model_rebuild()