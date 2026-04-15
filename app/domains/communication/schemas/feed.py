# communication/schemas/feed.py


from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, TYPE_CHECKING, List
from uuid import UUID
from datetime import datetime
from .base import DomainBase, TimestampSchema

if TYPE_CHECKING:
    from app.domains.identity.schemas.user import UserReference
else:
    UserReference = "UserReference"

class FeedItemBase(BaseModel):
    """
    Base schema for daily feed items
    """
    feed_date: datetime = Field(..., description="Date this feed item appears")
    item_type: str = Field(
        ...,
        pattern=r"^(announcement|exam|holiday|event|concern_update|birthday|achievement|urgent)$",
        description="Type of feed item"
    )
    source_type: str = Field(
        ...,
        pattern=r"^(announcement|exam|concern|student|meeting|achievement|system)$",
        description="Origin of the feed item"
    )
    source_id: UUID = Field(..., description="ID of source entity")
    title: str = Field(..., min_length=3, max_length=200)
    summary: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = Field(None, max_length=2000)
    priority: str = Field(
        default="normal",
        pattern=r"^(low|normal|high|urgent)$",
        description="Display priority"
    )
    is_pinned: bool = Field(default=False)
    image_url: Optional[str] = Field(None, max_length=500)
    action_url: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict] = Field(default_factory=dict)

class FeedItemCreate(FeedItemBase):
    """
    Schema for creating a feed item
    """
    school_id: UUID

class FeedItemUpdate(BaseModel):
    """
    Schema for updating a feed item
    """
    summary: Optional[str] = None
    content: Optional[str] = None
    priority: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_active: Optional[bool] = None

class FeedItemResponse(FeedItemBase, TimestampSchema):
    """
    Response schema for feed item
    """
    id: UUID
    school_id: UUID
    is_active: bool = True
    is_deleted: bool
    views_count: int = 0
    likes_count: int = 0
    comments_count: int = 0
    created_by: Optional[UserReference] = None

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                    "school_id": "school-uuid",
                    "feed_date": "2026-02-19T00:00:00Z",
                    "item_type": "birthday",
                    "source_type": "student",
                    "source_id": "student-uuid",
                    "title": "Happy Birthday, Jamie Smith!",
                    "summary": "Today is Jamie Smith's birthday! Grade 10-A",
                    "content": "Wishing a very happy birthday to Jamie Smith from Grade 10-A! 🎂🎉",
                    "priority": "normal",
                    "is_pinned": False,
                    "image_url": "https://school.edu/images/birthday-cake.png",
                    "action_url": "/app/students/student-uuid",
                    "metadata": {
                        "student_name": "Jamie Smith",
                        "class_name": "Grade 10",
                        "section_name": "A",
                        "age": 16
                    },
                    "is_active": True,
                    "created_at": "2026-02-19T00:00:00Z",
                    "views_count": 45,
                    "likes_count": 12,
                    "comments_count": 3
                },
                {
                    "feed_date": "2026-02-20T00:00:00Z",
                    "item_type": "exam",
                    "source_type": "exam",
                    "source_id": "exam-uuid",
                    "title": "Quarterly Exams Start Tomorrow",
                    "summary": "Quarterly examinations begin on February 20, 2026",
                    "priority": "high",
                    "is_pinned": True,
                    "metadata": {
                        "exam_name": "Quarterly Examination - Term 2",
                        "start_date": "2026-02-20",
                        "end_date": "2026-02-25"
                    }
                },
                {
                    "item_type": "announcement",
                    "source_type": "announcement",
                    "source_id": "announcement-uuid",
                    "title": "Republic Day Celebration",
                    "summary": "Join us for Republic Day celebration on January 26",
                    "priority": "high"
                }
            ]
        }

class FeedItemSummary(BaseModel):
    """
    Compact summary for feed listing
    """
    id: UUID
    item_type: str
    title: str
    summary: Optional[str] = None
    feed_date: datetime
    priority: str
    is_pinned: bool
    views_count: int
    is_new: bool = False  # Based on user's last seen timestamp

class UserFeedPreferences(BaseModel):
    """
    User preferences for feed content
    """
    user_id: UUID
    show_birthdays: bool = True
    show_announcements: bool = True
    show_exams: bool = True
    show_events: bool = True
    show_concerns: bool = False  # Parents might not want to see other students' concerns
    show_achievements: bool = True
    max_items_per_day: int = Field(default=20, ge=5, le=100)
    auto_mark_as_read: bool = False
    notification_on_new_items: bool = True

class FeedFilter(BaseModel):
    """
    Filter schema for feed queries
    """
    school_id: UUID
    user_id: Optional[UUID] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    item_types: Optional[List[str]] = None
    priority: Optional[str] = None
    only_pinned: bool = False
    exclude_seen: bool = False
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v and values.get('date_from') and v < values['date_from']:
            raise ValueError('date_to must be after date_from')
        return v

class FeedAnalytics(BaseModel):
    """
    Feed engagement analytics
    """
    date: datetime
    total_items: int = 0
    total_views: int = 0
    unique_viewers: int = 0
    avg_engagement_time_seconds: float = 0.0
    most_engaged_item_type: Optional[str] = None
    items_by_type: Dict[str, int] = Field(default_factory=dict)
    engagement_by_role: Dict[str, int] = Field(default_factory=dict)
    peak_viewing_hour: Optional[int] = None

class FeedItemInteraction(BaseModel):
    """
    Track user interactions with feed items
    """
    feed_item_id: UUID
    user_id: UUID
    interaction_type: str = Field(..., pattern=r"^(view|like|comment|share|hide)$")
    interaction_at: datetime
    comment_text: Optional[str] = Field(None, max_length=500)
    user: Optional[UserReference] = None

class BirthdayFeedItem(BaseModel):
    """
    Specialized schema for birthday feed items
    """
    student_id: UUID
    student_name: str
    class_section: str
    age: int
    profile_image_url: Optional[str] = None
    message: str = "Happy Birthday!"

# Resolve forward references
FeedItemResponse.model_rebuild()
FeedItemInteraction.model_rebuild()