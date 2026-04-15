# welfare/schemas/concern.py


from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, TYPE_CHECKING
from uuid import UUID
from datetime import datetime, timedelta
from .base import DomainBase, TimestampSchema
from types.types import ConcernType

if TYPE_CHECKING:
    from app.domains.identity.schemas.student import StudentReference
    from app.domains.identity.schemas.user import UserReference
    from app.domains.identity.schemas.staff import StaffReference
else:
    StudentReference = "StudentReference"
    UserReference = "UserReference"
    StaffReference = "StaffReference"

class CustomConcernType(BaseModel):
    """
    User-defined concern type for extensibility
    Example: {"type": "bullying", "label": "Bullying Incident", "description": "Peer harassment or intimidation"}
    """
    type: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-z0-9_]+$")
    label: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=200)

class ConcernBase(DomainBase):
    """
    Base schema for student concerns/flags
    """
    type: ConcernType = Field(..., description="Predefined concern category")
    custom_type: Optional[CustomConcernType] = Field(
        None,
        description="User-defined concern type (only when type='other')"
    )
    title: str = Field(..., min_length=5, max_length=200, description="Brief concern title")
    description: str = Field(..., min_length=10, max_length=2000, description="Detailed description")
    severity: str = Field(
        ...,
        pattern=r"^(low|medium|high|critical)$",
        description="Severity level of concern"
    )
    priority: str = Field(
        default="normal",
        pattern=r"^(low|normal|high|urgent)$",
        description="Handling priority"
    )
    status: str = Field(
        default="reported",
        pattern=r"^(reported|under_review|assigned|in_progress|resolved|closed|escalated)$",
        description="Current workflow status"
    )
    is_anonymous: bool = Field(default=False, description="Reported anonymously")
    requires_immediate_attention: bool = Field(default=False, description="Needs urgent intervention")
    tags: Optional[List[str]] = Field(None, max_items=10, description="Searchable tags")
    evidence_attachments: Optional[List[Dict]] = Field(
        None,
        description="Evidence files: [{'name': str, 'path': str, 'type': str, 'uploaded_at': datetime}]"
    )
    context_notes: Optional[str] = Field(None, max_length=1000, description="Additional context")
    recommended_actions: Optional[List[str]] = Field(None, max_items=10)

    @validator('custom_type')
    def validate_custom_type(cls, v, values):
        if v and values.get('type') != ConcernType.OTHER:
            raise ValueError('Custom type only allowed when type is "other"')
        if not v and values.get('type') == ConcernType.OTHER:
            raise ValueError('Custom type required when type is "other"')
        return v

class ConcernCreate(ConcernBase):
    """
    Schema for creating a concern
    """
    school_id: UUID
    student_id: UUID
    reported_by_id: UUID
    reported_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('reported_at')
    def validate_reported_time(cls, v):
        if v > datetime.utcnow() + timedelta(minutes=5):
            raise ValueError('Reported time cannot be in the future')
        return v

class ConcernUpdate(BaseModel):
    """
    Schema for updating a concern
    """
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    recommended_actions: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class ConcernAssignmentBase(BaseModel):
    """
    Base schema for concern assignments
    """
    assigned_to_id: UUID
    assigned_by_id: UUID
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    priority: str = Field(
        default="normal",
        pattern=r"^(low|normal|high|urgent)$"
    )
    status: str = Field(
        default="pending",
        pattern=r"^(pending|in_progress|completed|overdue)$"
    )
    notes: Optional[str] = Field(None, max_length=1000)
    handover_notes: Optional[str] = Field(None, max_length=1000)

    @validator('due_date')
    def validate_due_date(cls, v):
        if v and v < datetime.utcnow():
            raise ValueError('Due date cannot be in the past')
        return v

class ConcernAssignmentCreate(ConcernAssignmentBase):
    concern_id: UUID

class ConcernAssignmentUpdate(BaseModel):
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class ConcernAssignmentResponse(ConcernAssignmentBase, TimestampSchema):
    id: UUID
    concern_id: UUID
    is_deleted: bool
    assigned_to: StaffReference
    assigned_by: UserReference
    completed_at: Optional[datetime] = None
    time_to_resolution_hours: Optional[float] = None

class ConcernCommentBase(BaseModel):
    """
    Base schema for concern comments/collaboration
    """
    comment: str = Field(..., min_length=1, max_length=2000)
    is_internal: bool = Field(
        default=False,
        description="True = only visible to staff, False = visible to parents"
    )
    parent_visibility: str = Field(
        default="visible",
        pattern=r"^(visible|hidden|partial|redacted)$",
        description="How comment appears to parents"
    )
    attachments: Optional[List[Dict]] = Field(
        None,
        description="Comment attachments: [{'name': str, 'path': str, 'type': str}]"
    )
    mentions: Optional[List[UUID]] = Field(None, description="User IDs mentioned")
    is_action_required: bool = False
    action_description: Optional[str] = Field(None, max_length=500)

class ConcernCommentCreate(ConcernCommentBase):
    concern_id: UUID
    user_id: UUID

class ConcernCommentUpdate(BaseModel):
    comment: Optional[str] = None
    is_internal: Optional[bool] = None
    parent_visibility: Optional[str] = None

class ConcernCommentResponse(ConcernCommentBase, TimestampSchema):
    id: UUID
    concern_id: UUID
    user_id: UUID
    is_deleted: bool
    user: UserReference
    likes_count: int = 0
    replies_count: int = 0

class ConcernHistoryEntry(BaseModel):
    """
    Audit trail entry for concern changes
    """
    concern_id: UUID
    action: str = Field(
        ...,
        pattern=r"^(status_changed|assigned|escalated|resolved|reopened|comment_added|priority_changed|severity_changed)$"
    )
    previous_value: Optional[Dict] = None
    new_value: Optional[Dict] = None
    changed_by_id: UUID
    changed_at: datetime
    notes: Optional[str] = Field(None, max_length=1000)
    changed_by: Optional[UserReference] = None

class EscalationBase(BaseModel):
    """
    Base schema for concern escalations
    """
    escalated_by_id: UUID
    escalated_to_id: UUID
    escalated_at: datetime = Field(default_factory=datetime.utcnow)
    reason: str = Field(..., min_length=10, max_length=1000)
    priority: str = Field(
        default="high",
        pattern=r"^(medium|high|urgent|critical)$"
    )
    due_date: Optional[datetime] = None
    status: str = Field(
        default="pending",
        pattern=r"^(pending|acknowledged|in_progress|resolved|rejected)$"
    )
    escalation_level: int = Field(..., ge=1, le=5, description="Level 1-5 (5 = highest)")
    requires_principal_approval: bool = False
    notification_sent: bool = False
    notes: Optional[str] = Field(None, max_length=1000)

    @validator('due_date')
    def validate_due_date(cls, v):
        if v and v < datetime.utcnow():
            raise ValueError('Due date cannot be in the past')
        return v

class EscalationCreate(EscalationBase):
    concern_id: UUID

class EscalationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

class EscalationResponse(EscalationBase, TimestampSchema):
    id: UUID
    concern_id: UUID
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolved_by_id: Optional[UUID] = None
    resolution_notes: Optional[str] = Field(None, max_length=2000)
    escalated_by: UserReference
    escalated_to: UserReference
    resolved_by: Optional[UserReference] = None
    time_to_acknowledgment_hours: Optional[float] = None
    time_to_resolution_hours: Optional[float] = None

class ConcernResponse(ConcernBase, TimestampSchema):
    """
    Response schema for concern with full context
    """
    id: UUID
    school_id: UUID
    student_id: UUID
    reported_by_id: UUID
    reported_at: datetime
    reviewed_by_id: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = Field(None, max_length=2000)
    closed_at: Optional[datetime] = None
    closed_by_id: Optional[UUID] = None
    is_deleted: bool
    student: StudentReference
    reported_by: UserReference
    reviewed_by: Optional[UserReference] = None
    closed_by: Optional[UserReference] = None
    assignments: List[ConcernAssignmentResponse] = []
    comments: List[ConcernCommentResponse] = []
    escalations: List[EscalationResponse] = []
    history: List[ConcernHistoryEntry] = []
    related_observations: int = 0
    attachment_count: int = 0
    days_open: int = 0
    time_to_first_response_hours: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "school_id": "school-uuid",
                "student_id": "student-uuid",
                "reported_by_id": "teacher-uuid",
                "reported_at": "2026-02-15T10:30:00Z",
                "type": "behaviour",
                "custom_type": None,
                "title": "Repeated classroom disruptions during mathematics",
                "description": "Jamie has been disrupting mathematics class repeatedly over the past week. During today's lesson on quadratic equations, Jamie interrupted the teacher 3 times, talked to neighboring students despite warnings, and used a disrespectful tone when asked to focus. This is the third incident this week. Previous discussions with Jamie have not resulted in behavior improvement.",
                "severity": "medium",
                "priority": "high",
                "status": "assigned",
                "is_anonymous": False,
                "requires_immediate_attention": False,
                "tags": ["classroom_behavior", "mathematics", "repeated_incident"],
                "recommended_actions": [
                    "Schedule meeting with parents",
                    "Create behavior improvement plan",
                    "Increase monitoring during math class"
                ],
                "reviewed_by_id": "counselor-uuid",
                "reviewed_at": "2026-02-15T14:00:00Z",
                "resolved_at": None,
                "resolution_notes": None,
                "closed_at": None,
                "is_deleted": False,
                "student": {
                    "id": "student-uuid",
                    "admission_number": "STU2026045",
                    "full_name": "Jamie Smith",
                    "class_name": "Grade 10",
                    "section_name": "A"
                },
                "reported_by": {
                    "id": "teacher-uuid",
                    "full_name": "Ms. Sarah Chen",
                    "email": "s.chen@school.edu",
                    "role": "teacher"
                },
                "reviewed_by": {
                    "id": "counselor-uuid",
                    "full_name": "Dr. Anjali Patel",
                    "email": "a.patel@school.edu",
                    "role": "counselor"
                },
                "assignments": [
                    {
                        "id": "assignment-uuid",
                        "concern_id": "concern-uuid",
                        "assigned_to_id": "counselor-uuid",
                        "assigned_by_id": "admin-uuid",
                        "assigned_at": "2026-02-15T14:05:00Z",
                        "due_date": "2026-02-22T23:59:59Z",
                        "priority": "high",
                        "status": "in_progress",
                        "notes": "Schedule parent-teacher meeting and create behavior plan",
                        "assigned_to": {
                            "id": "counselor-uuid",
                            "employee_id": "COUN2026001",
                            "full_name": "Dr. Anjali Patel",
                            "position": "School Counselor"
                        },
                        "assigned_by": {
                            "id": "admin-uuid",
                            "full_name": "Admin User",
                            "email": "admin@school.edu",
                            "role": "admin"
                        },
                        "completed_at": None,
                        "time_to_resolution_hours": None
                    }
                ],
                "comments": [
                    {
                        "id": "comment-uuid",
                        "concern_id": "concern-uuid",
                        "user_id": "counselor-uuid",
                        "comment": "I've reviewed the concern and will schedule a meeting with Jamie's parents this week. I've also spoken with Jamie briefly and he seemed receptive to discussing the issues.",
                        "is_internal": False,
                        "parent_visibility": "visible",
                        "created_at": "2026-02-15T14:10:00Z",
                        "user": {
                            "id": "counselor-uuid",
                            "full_name": "Dr. Anjali Patel",
                            "email": "a.patel@school.edu",
                            "role": "counselor"
                        },
                        "likes_count": 1,
                        "replies_count": 0
                    }
                ],
                "escalations": [],
                "history": [
                    {
                        "concern_id": "concern-uuid",
                        "action": "status_changed",
                        "previous_value": {"status": "reported"},
                        "new_value": {"status": "under_review"},
                        "changed_by_id": "counselor-uuid",
                        "changed_at": "2026-02-15T14:00:00Z",
                        "changed_by": {
                            "id": "counselor-uuid",
                            "full_name": "Dr. Anjali Patel",
                            "email": "a.patel@school.edu",
                            "role": "counselor"
                        }
                    }
                ],
                "related_observations": 3,
                "attachment_count": 0,
                "days_open": 2,
                "time_to_first_response_hours": 3.5
            }
        }

class ConcernReference(BaseModel):
    """
    Compact reference schema for concern
    """
    id: UUID
    type: ConcernType
    title: str
    status: str
    severity: str
    reported_at: datetime

class ConcernSummary(BaseModel):
    """
    Summary statistics for concerns
    """
    total_concerns: int = 0
    open_concerns: int = 0
    resolved_concerns: int = 0
    closed_concerns: int = 0
    escalated_concerns: int = 0
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_severity: Dict[str, int] = Field(default_factory=dict)
    by_status: Dict[str, int] = Field(default_factory=dict)
    avg_resolution_time_hours: float = 0.0
    overdue_concerns: int = 0
    concerns_requiring_attention: int = 0

class ConcernFilter(BaseModel):
    """
    Filter schema for concern queries
    """
    school_id: Optional[UUID] = None
    student_id: Optional[UUID] = None
    reported_by_id: Optional[UUID] = None
    assigned_to_id: Optional[UUID] = None
    concern_type: Optional[ConcernType] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    include_resolved: bool = True
    include_closed: bool = False
    require_immediate_attention: Optional[bool] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v and values.get('date_from') and v < values['date_from']:
            raise ValueError('date_to must be after date_from')
        return v

class BulkConcernCreate(BaseModel):
    """
    Create multiple concerns for different students
    """
    concerns: List[ConcernCreate] = Field(..., min_items=1, max_items=50)
    auto_assign: bool = Field(default=False, description="Auto-assign to default counselor")
    send_notifications: bool = Field(default=True)

    @validator('concerns')
    def validate_unique_students(cls, v):
        student_ids = [(c.student_id, c.type) for c in v]
        if len(student_ids) != len(set(student_ids)):
            raise ValueError('Cannot create duplicate concern types for same student in bulk operation')
        return v

class ConcernAnalytics(BaseModel):
    """
    Comprehensive concern analytics
    """
    period_start: datetime
    period_end: datetime
    total_concerns: int = 0
    concerns_by_month: Dict[str, int] = Field(default_factory=dict)
    concerns_by_type: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        description="{'behaviour': {'low': 5, 'medium': 3, 'high': 2}, ...}"
    )
    concerns_by_class: Dict[str, int] = Field(default_factory=dict)
    avg_time_to_assignment_hours: float = 0.0
    avg_time_to_resolution_hours: float = 0.0
    resolution_rate: float = Field(default=0.0, ge=0, le=100)
    escalation_rate: float = Field(default=0.0, ge=0, le=100)
    repeat_concerns: int = 0
    top_concern_types: List[str] = []
    trend_direction: str = Field(..., pattern=r"^(increasing|stable|decreasing)$")

class ConcernExportFormat(BaseModel):
    """
    Export format options for concern reports
    """
    format: str = Field(
        default="pdf",
        pattern=r"^(pdf|excel|csv|json)$",
        description="Export format"
    )
    include_comments: bool = True
    include_assignments: bool = True
    include_escalations: bool = True
    include_history: bool = False
    include_attachments: bool = False
    date_range: Optional[tuple[datetime, datetime]] = None
    filter_criteria: Optional[Dict] = None

class ConcernNotificationSettings(BaseModel):
    """
    Notification settings for concern updates
    """
    user_id: UUID
    notify_on_new_concern: bool = True
    notify_on_assignment: bool = True
    notify_on_status_change: bool = True
    notify_on_comment: bool = True
    notify_on_escalation: bool = True
    notification_channels: List[str] = Field(
        default=["push", "email"],
        min_items=1,
        unique_items=True,
        pattern=r"^(push|email|sms|whatsapp)$"
    )
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    quiet_hours_end: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")

# Resolve forward references
ConcernAssignmentResponse.model_rebuild()
ConcernCommentResponse.model_rebuild()
EscalationResponse.model_rebuild()
ConcernResponse.model_rebuild()
ConcernHistoryEntry.model_rebuild()