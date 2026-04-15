# welfare/schemas/meeting.py


from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, TYPE_CHECKING
from uuid import UUID
from datetime import datetime, timedelta
from .base import DomainBase, TimestampSchema

if TYPE_CHECKING:
    from app.domains.identity.schemas.user import UserReference
    from app.domains.identity.schemas.student import StudentReference
    from app.domains.identity.schemas.class_section import ClassSectionReference
else:
    UserReference = "UserReference"
    StudentReference = "StudentReference"
    ClassSectionReference = "ClassSectionReference"

class MeetingParticipantBase(BaseModel):
    """
    Base schema for meeting participants
    """
    user_id: UUID
    role: str = Field(
        ...,
        pattern=r"^(parent|student|teacher|counselor|admin|staff|observer)$",
        description="Role in the meeting"
    )
    invitation_status: str = Field(
        default="pending",
        pattern=r"^(pending|accepted|declined|tentative)$"
    )
    attendance_status: Optional[str] = Field(
        None,
        pattern=r"^(present|absent|late|excused)$"
    )
    attendance_confirmed_at: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)
    requires_interpreter: bool = False
    dietary_requirements: Optional[str] = Field(None, max_length=200)

class MeetingParticipantCreate(MeetingParticipantBase):
    meeting_id: UUID

class MeetingParticipantUpdate(BaseModel):
    invitation_status: Optional[str] = None
    attendance_status: Optional[str] = None
    notes: Optional[str] = None

class MeetingParticipantResponse(MeetingParticipantBase, TimestampSchema):
    id: UUID
    meeting_id: UUID
    user: UserReference
    is_primary_contact: bool = False

class MeetingAgendaBase(BaseModel):
    """
    Base schema for meeting agenda items
    """
    item_order: int = Field(..., ge=1)
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    assigned_to_id: Optional[UUID] = None
    estimated_duration_minutes: int = Field(..., ge=1, le=120)
    status: str = Field(
        default="pending",
        pattern=r"^(pending|in_progress|completed|deferred)$"
    )
    notes: Optional[str] = Field(None, max_length=500)

class MeetingAgendaCreate(MeetingAgendaBase):
    meeting_id: UUID

class MeetingAgendaUpdate(BaseModel):
    item_order: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to_id: Optional[UUID] = None
    estimated_duration_minutes: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class MeetingAgendaResponse(MeetingAgendaBase, TimestampSchema):
    id: UUID
    meeting_id: UUID
    assigned_to: Optional[UserReference] = None
    completed_at: Optional[datetime] = None

class MeetingOutcomeBase(BaseModel):
    """
    Base schema for meeting outcomes and action items
    """
    outcome_text: str = Field(..., min_length=10, max_length=2000)
    action_items: List[Dict] = Field(
        default_factory=list,
        description="List of action items: [{'description': str, 'assigned_to': UUID, 'due_date': datetime, 'status': str}]"
    )
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None
    shared_with_parents: bool = False
    confidential_notes: Optional[str] = Field(None, max_length=1000)

    @validator('action_items')
    def validate_action_items(cls, v):
        for item in v:
            if 'description' not in item or not item['description'].strip():
                raise ValueError('Action item must have description')
            if 'due_date' in item and item['due_date'] < datetime.utcnow():
                raise ValueError('Action item due date cannot be in the past')
        return v

class MeetingOutcomeCreate(MeetingOutcomeBase):
    meeting_id: UUID
    recorded_by_id: UUID

class MeetingOutcomeUpdate(BaseModel):
    outcome_text: Optional[str] = None
    action_items: Optional[List[Dict]] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime] = None
    shared_with_parents: Optional[bool] = None

class MeetingOutcomeResponse(MeetingOutcomeBase, TimestampSchema):
    id: UUID
    meeting_id: UUID
    recorded_by_id: UUID
    recorded_at: datetime
    recorded_by: UserReference
    completed_action_items: int = 0
    pending_action_items: int = 0

class MeetingAttendanceBase(BaseModel):
    """
    Base schema for detailed meeting attendance tracking
    """
    participant_id: UUID
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    attendance_duration_minutes: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=500)

    @validator('check_out_time')
    def validate_checkout_after_checkin(cls, v, values):
        if v and values.get('check_in_time') and v < values['check_in_time']:
            raise ValueError('Check-out time must be after check-in time')
        return v

class MeetingAttendanceCreate(MeetingAttendanceBase):
    meeting_id: UUID

class MeetingAttendanceUpdate(BaseModel):
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    notes: Optional[str] = None

class MeetingAttendanceResponse(MeetingAttendanceBase, TimestampSchema):
    id: UUID
    meeting_id: UUID
    participant: MeetingParticipantResponse

class MeetingBase(DomainBase):
    """
    Base schema for welfare meetings
    """
    title: str = Field(..., min_length=5, max_length=200)
    purpose: str = Field(..., min_length=10, max_length=1000)
    description: Optional[str] = Field(None, max_length=2000)
    scheduled_at: datetime
    duration_minutes: int = Field(..., ge=15, le=300)
    location: Optional[str] = Field(None, max_length=200)
    meeting_type: str = Field(
        ...,
        pattern=r"^(parent_teacher|counselor_student|staff_meeting|disciplinary|iep|wellness_review|emergency)$",
        description="Type of meeting"
    )
    status: str = Field(
        default="scheduled",
        pattern=r"^(scheduled|confirmed|in_progress|completed|cancelled|rescheduled)$"
    )
    priority: str = Field(default="normal", pattern=r"^(low|normal|high|urgent)$")
    is_confidential: bool = False
    requires_parent_consent: bool = False
    virtual_meeting_link: Optional[str] = Field(None, max_length=500)
    virtual_meeting_id: Optional[str] = Field(None, max_length=100)
    virtual_meeting_password: Optional[str] = Field(None, max_length=50)
    pre_meeting_notes: Optional[str] = Field(None, max_length=2000)
    post_meeting_notes: Optional[str] = Field(None, max_length=2000)

    @validator('scheduled_at')
    def validate_future_scheduling(cls, v):
        if v < datetime.utcnow():
            raise ValueError('Meeting cannot be scheduled in the past')
        return v

class MeetingCreate(MeetingBase):
    school_id: UUID
    created_by_id: UUID
    participant_ids: List[UUID] = Field(..., min_items=2, max_items=50)
    student_ids: Optional[List[UUID]] = Field(None, max_items=20)
    class_section_ids: Optional[List[UUID]] = Field(None, max_items=10)

    @validator('participant_ids')
    def validate_unique_participants(cls, v):
        if len(set(v)) != len(v):
            raise ValueError('Duplicate participants not allowed')
        return v

class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    purpose: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    virtual_meeting_link: Optional[str] = None
    pre_meeting_notes: Optional[str] = None

class MeetingResponse(MeetingBase, TimestampSchema):
    id: UUID
    school_id: UUID
    created_by_id: UUID
    is_deleted: bool
    created_by: UserReference
    participants: List[MeetingParticipantResponse] = []
    agenda_items: List[MeetingAgendaResponse] = []
    outcomes: Optional[MeetingOutcomeResponse] = None
    attendance_records: List[MeetingAttendanceResponse] = []
    related_students: List[StudentReference] = []
    related_classes: List[ClassSectionReference] = []
    total_participants: int = 0
    confirmed_participants: int = 0
    attendance_rate: float = Field(default=0.0, ge=0, le=100)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "school_id": "school-uuid",
                "title": "Parent-Teacher Meeting: Jamie Smith's Academic Progress",
                "purpose": "Discuss Jamie's recent performance in mathematics and address concerns about classroom behavior",
                "description": "Follow-up meeting after teacher observation on February 15. Focus on strategies to improve engagement and address disruptive behavior during math lessons.",
                "scheduled_at": "2026-02-25T15:30:00Z",
                "duration_minutes": 45,
                "location": "Counselor's Office, Room 205",
                "meeting_type": "parent_teacher",
                "status": "confirmed",
                "priority": "high",
                "is_confidential": False,
                "requires_parent_consent": False,
                "virtual_meeting_link": "https://meet.school.edu/jamie-smith-ptm",
                "created_by_id": "counselor-uuid",
                "created_at": "2026-02-18T10:15:00Z",
                "is_deleted": False,
                "created_by": {
                    "id": "counselor-uuid",
                    "full_name": "Dr. Anjali Patel",
                    "email": "a.patel@school.edu",
                    "role": "counselor"
                },
                "participants": [
                    {
                        "id": "participant-uuid-1",
                        "meeting_id": "meeting-uuid",
                        "user_id": "parent-uuid",
                        "role": "parent",
                        "invitation_status": "accepted",
                        "attendance_status": None,
                        "user": {
                            "id": "parent-uuid",
                            "full_name": "Maria Rodriguez",
                            "email": "maria.rodriguez@email.com",
                            "role": "parent"
                        },
                        "is_primary_contact": True
                    },
                    {
                        "id": "participant-uuid-2",
                        "meeting_id": "meeting-uuid",
                        "user_id": "teacher-uuid",
                        "role": "teacher",
                        "invitation_status": "accepted",
                        "attendance_status": None,
                        "user": {
                            "id": "teacher-uuid",
                            "full_name": "Ms. Sarah Chen",
                            "email": "s.chen@school.edu",
                            "role": "teacher"
                        },
                        "is_primary_contact": False
                    }
                ],
                "agenda_items": [
                    {
                        "id": "agenda-uuid-1",
                        "meeting_id": "meeting-uuid",
                        "item_order": 1,
                        "title": "Review recent academic performance",
                        "description": "Discuss mathematics test scores and homework completion rates",
                        "assigned_to_id": "teacher-uuid",
                        "estimated_duration_minutes": 15,
                        "status": "pending",
                        "assigned_to": {
                            "id": "teacher-uuid",
                            "full_name": "Ms. Sarah Chen",
                            "email": "s.chen@school.edu",
                            "role": "teacher"
                        }
                    }
                ],
                "outcomes": None,
                "attendance_records": [],
                "related_students": [
                    {
                        "id": "student-uuid",
                        "admission_number": "STU2026045",
                        "full_name": "Jamie Smith",
                        "class_name": "Grade 10",
                        "section_name": "A"
                    }
                ],
                "related_classes": [],
                "total_participants": 3,
                "confirmed_participants": 2,
                "attendance_rate": 0.0
            }
        }

class MeetingSummary(BaseModel):
    """
    Compact summary for meeting listings
    """
    id: UUID
    title: str
    meeting_type: str
    scheduled_at: datetime
    status: str
    priority: str
    total_participants: int
    has_outcome_recorded: bool = False
    is_overdue: bool = False

class MeetingFilter(BaseModel):
    """
    Filter schema for meeting queries
    """
    school_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    student_id: Optional[UUID] = None
    meeting_type: Optional[str] = None
    status: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    include_past: bool = True
    include_cancelled: bool = False
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v and values.get('date_from') and v < values['date_from']:
            raise ValueError('date_to must be after date_from')
        return v

class MeetingStatistics(BaseModel):
    """
    Meeting analytics and statistics
    """
    total_meetings: int = 0
    completed_meetings: int = 0
    cancelled_meetings: int = 0
    upcoming_meetings: int = 0
    average_duration_minutes: float = 0.0
    meetings_by_type: Dict[str, int] = Field(default_factory=dict)
    meetings_by_status: Dict[str, int] = Field(default_factory=dict)
    attendance_rate: float = Field(default=0.0, ge=0, le=100)
    meetings_with_outcomes: int = 0
    pending_action_items: int = 0

class MeetingReminder(BaseModel):
    """
    Meeting reminder configuration
    """
    meeting_id: UUID
    reminder_type: str = Field(..., pattern=r"^(email|sms|notification|all)$")
    reminder_time_minutes: int = Field(..., ge=5, le=10080)  # Up to 7 days
    recipients: List[UUID] = Field(..., min_items=1)
    custom_message: Optional[str] = Field(None, max_length=500)

# Resolve forward references
MeetingParticipantResponse.model_rebuild()
MeetingAgendaResponse.model_rebuild()
MeetingOutcomeResponse.model_rebuild()
MeetingAttendanceResponse.model_rebuild()
MeetingResponse.model_rebuild()