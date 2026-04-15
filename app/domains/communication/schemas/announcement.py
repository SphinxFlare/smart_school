# communication/schemas/announcement.py


from pydantic import BaseModel, Field, validator, HttpUrl
from typing import List, Optional, Dict, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from .base import DomainBase, TimestampSchema

if TYPE_CHECKING:
    from app.domains.identity.schemas.user import UserReference
    from app.domains.identity.schemas.class_section import ClassSectionReference
else:
    UserReference = "UserReference"
    ClassSectionReference = "ClassSectionReference"

class AnnouncementAttachment(BaseModel):
    """
    Announcement attachment metadata
    """
    name: str = Field(..., min_length=1, max_length=200)
    file_path: str = Field(..., max_length=500)
    file_type: str = Field(..., pattern=r"^(pdf|docx|jpg|png|zip|mp4|mp3)$")
    file_size_kb: int = Field(..., ge=1, le=102400)  # Max 100MB
    uploaded_at: datetime
    description: Optional[str] = Field(None, max_length=200)

class AnnouncementBase(DomainBase):
    """
    Base schema for school announcements
    """
    title: str = Field(..., min_length=3, max_length=200)
    content: str = Field(..., min_length=10, max_length=5000)
    announcement_type: str = Field(
        ...,
        pattern=r"^(notice|holiday|event|activity|urgent|general)$",
        description="Type of announcement"
    )
    category: Optional[str] = Field(
        None,
        pattern=r"^(academic|administrative|sports|cultural|general|urgent)$",
        description="Category for filtering"
    )
    target_roles: Optional[List[str]] = Field(
        None,
        description="Target roles: student, parent, teacher, staff, admin, driver",
        min_items=1
    )
    target_class_ids: Optional[List[UUID]] = Field(None, min_items=1)
    target_section_ids: Optional[List[UUID]] = Field(None, min_items=1)
    target_student_ids: Optional[List[UUID]] = Field(None, min_items=1)
    published_at: datetime
    expires_at: Optional[datetime] = Field(
        None,
        description="When announcement should no longer be visible"
    )
    is_pinned: bool = Field(default=False, description="Show at top of announcements list")
    priority: str = Field(
        default="normal",
        pattern=r"^(low|normal|high|urgent)$",
        description="Display priority"
    )
    attachments: List[AnnouncementAttachment] = Field(default_factory=list)
    tags: Optional[List[str]] = Field(None, max_items=10)
    allow_comments: bool = Field(default=False)
    requires_acknowledgment: bool = Field(default=False)

    @validator('expires_at')
    def validate_expiry_after_publish(cls, v, values):
        if v and values.get('published_at') and v <= values['published_at']:
            raise ValueError('Expiry date must be after publish date')
        return v
    
    @validator('target_student_ids')
    def validate_target_students(cls, v, values):
        if v and (values.get('target_class_ids') or values.get('target_section_ids')):
            raise ValueError('Cannot specify both target students and target classes/sections')
        return v

class AnnouncementCreate(AnnouncementBase):
    """
    Schema for creating an announcement
    """
    school_id: UUID
    published_by_id: UUID

class AnnouncementUpdate(BaseModel):
    """
    Schema for updating an announcement
    """
    title: Optional[str] = None
    content: Optional[str] = None
    announcement_type: Optional[str] = None
    category: Optional[str] = None
    target_roles: Optional[List[str]] = None
    target_class_ids: Optional[List[UUID]] = None
    target_section_ids: Optional[List[UUID]] = None
    published_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_pinned: Optional[bool] = None
    priority: Optional[str] = None
    attachments: Optional[List[AnnouncementAttachment]] = None
    is_published: Optional[bool] = None
    tags: Optional[List[str]] = None

class AnnouncementResponse(AnnouncementBase, TimestampSchema):
    """
    Response schema for announcement with relationships
    """
    id: UUID
    school_id: UUID
    published_by_id: UUID
    is_published: bool = True
    is_deleted: bool
    views_count: int = 0
    likes_count: int = 0
    comments_count: int = 0
    acknowledgments_count: int = 0
    published_by: UserReference
    target_classes: Optional[List[ClassSectionReference]] = None
    target_sections: Optional[List[ClassSectionReference]] = None

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                    "school_id": "school-uuid",
                    "title": "Republic Day Celebration - January 26, 2026",
                    "content": "Dear Parents and Students,\n\nWe are pleased to announce that our school will be celebrating Republic Day on January 26, 2026. The celebration will include a flag hoisting ceremony, cultural programs, and patriotic song competitions.\n\nSchedule:\n- 8:00 AM: Assembly and flag hoisting\n- 9:00 AM: Cultural programs\n- 11:00 AM: Patriotic song competition\n- 12:30 PM: Distribution of sweets\n\nAll students are requested to wear traditional Indian attire. Parents are welcome to attend the cultural programs.\n\nThank you,\nSchool Administration",
                    "announcement_type": "event",
                    "category": "cultural",
                    "target_roles": ["parent", "student"],
                    "target_class_ids": ["class-uuid-1", "class-uuid-2"],
                    "published_at": "2026-01-20T10:00:00Z",
                    "expires_at": "2026-01-27T23:59:59Z",
                    "is_pinned": True,
                    "priority": "high",
                    "attachments": [
                        {
                            "name": "republic_day_schedule.pdf",
                            "file_path": "/announcements/2026/01/republic_day_schedule.pdf",
                            "file_type": "pdf",
                            "file_size_kb": 245,
                            "uploaded_at": "2026-01-20T09:45:00Z",
                            "description": "Detailed schedule of events"
                        },
                        {
                            "name": "venue_map.jpg",
                            "file_path": "/announcements/2026/01/venue_map.jpg",
                            "file_type": "jpg",
                            "file_size_kb": 1250,
                            "uploaded_at": "2026-01-20T09:46:00Z",
                            "description": "Venue layout map"
                        }
                    ],
                    "tags": ["republic_day", "celebration", "cultural_event"],
                    "allow_comments": True,
                    "requires_acknowledgment": True,
                    "published_by_id": "user-uuid",
                    "is_published": True,
                    "created_at": "2026-01-20T09:30:00Z",
                    "is_deleted": False,
                    "views_count": 1245,
                    "likes_count": 87,
                    "comments_count": 23,
                    "acknowledgments_count": 956,
                    "published_by": {
                        "id": "user-uuid",
                        "full_name": "Dr. Sunita Menon",
                        "email": "principal@dpsrohini.edu.in",
                        "role": "admin"
                    },
                    "target_classes": [
                        {
                            "class_id": "class-uuid-1",
                            "class_name": "Grade 10",
                            "section_id": None,
                            "section_name": None
                        }
                    ]
                },
                {
                    "title": "School Holiday - Diwali Break",
                    "content": "School will remain closed from November 1-5, 2026 for Diwali celebrations. Classes resume on November 6, 2026.",
                    "announcement_type": "holiday",
                    "category": "general",
                    "target_roles": ["parent", "student", "teacher", "staff"],
                    "published_at": "2026-10-15T09:00:00Z",
                    "announcement_type": "holiday"
                }
            ]
        }

class AnnouncementSummary(BaseModel):
    """
    Compact summary for listing views
    """
    id: UUID
    title: str
    announcement_type: str
    category: Optional[str] = None
    published_at: datetime
    expires_at: Optional[datetime] = None
    is_pinned: bool
    priority: str
    views_count: int
    is_expired: bool = False

class AnnouncementAcknowledgment(BaseModel):
    """
    Track which users have acknowledged an announcement
    """
    announcement_id: UUID
    user_id: UUID
    acknowledged_at: datetime
    user: Optional[UserReference] = None

class BulkAnnouncementCreate(BaseModel):
    """
    Create multiple announcements at once
    """
    announcements: List[AnnouncementCreate] = Field(..., min_items=1, max_items=50)
    send_notifications: bool = Field(default=True)

    @validator('announcements')
    def validate_unique_titles(cls, v):
        titles = [a.title for a in v]
        if len(titles) != len(set(titles)):
            raise ValueError('Duplicate announcement titles not allowed')
        return v

class AnnouncementAnalytics(BaseModel):
    """
    Analytics for announcement engagement
    """
    announcement_id: UUID
    total_views: int = 0
    unique_viewers: int = 0
    view_rate: float = Field(default=0.0, ge=0, le=100)
    acknowledgment_rate: float = Field(default=0.0, ge=0, le=100)
    avg_time_spent_seconds: float = 0.0
    shares_count: int = 0
    comments_breakdown: Dict[str, int] = Field(default_factory=dict)
    views_by_role: Dict[str, int] = Field(default_factory=dict)
    views_by_class: Dict[str, int] = Field(default_factory=dict)
    peak_viewing_time: Optional[datetime] = None

# Resolve forward references
AnnouncementResponse.model_rebuild()
AnnouncementAcknowledgment.model_rebuild()