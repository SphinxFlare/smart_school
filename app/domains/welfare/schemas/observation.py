# welfare/schemas/observation.py


from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, TYPE_CHECKING
from uuid import UUID
from datetime import datetime, timedelta
from .base import DomainBase, TimestampSchema

if TYPE_CHECKING:
    from app.domains.identity.schemas.student import StudentReference
    from app.domains.identity.schemas.staff import StaffReference
    from app.domains.identity.schemas.class_section import ClassSectionReference
    from .concern import ConcernReference
else:
    StudentReference = "StudentReference"
    StaffReference = "StaffReference"
    ClassSectionReference = "ClassSectionReference"
    ConcernReference = "ConcernReference"

class StudentObservationBase(DomainBase):
    """
    Base schema for teacher micro-observations
    """
    observation_date: datetime
    category: str = Field(
        ...,
        pattern=r"^(academic|behaviour|social|emotional|health|safety|attention|participation)$",
        description="Observation category"
    )
    description: str = Field(..., min_length=10, max_length=1000)
    severity: str = Field(
        ...,
        pattern=r"^(positive|neutral|concerning|critical)$",
        description="Severity level"
    )
    context: Optional[str] = Field(None, max_length=200)
    action_taken: Optional[str] = Field(None, max_length=500)
    shared_with_parents: bool = False
    shared_with_counselor: bool = False
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None
    tags: Optional[List[str]] = Field(None, max_items=10)
    evidence_attachments: Optional[List[Dict]] = Field(
        None,
        description="Evidence files: [{'name': str, 'path': str, 'type': str}]"
    )

    @validator('observation_date')
    def validate_observation_date(cls, v):
        if v > datetime.utcnow() + timedelta(minutes=5):
            raise ValueError('Observation date cannot be in the future')
        return v

class StudentObservationCreate(StudentObservationBase):
    student_id: UUID
    teacher_id: UUID
    class_id: UUID
    section_id: UUID
    subject_id: Optional[UUID] = None

class StudentObservationUpdate(BaseModel):
    description: Optional[str] = None
    severity: Optional[str] = None
    action_taken: Optional[str] = None
    shared_with_parents: Optional[bool] = None
    shared_with_counselor: Optional[bool] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime] = None

class StudentObservationResponse(StudentObservationBase, TimestampSchema):
    id: UUID
    student_id: UUID
    teacher_id: UUID
    class_id: UUID
    section_id: UUID
    subject_id: Optional[UUID] = None
    is_deleted: bool
    student: StudentReference
    teacher: StaffReference
    class_section: ClassSectionReference
    related_concerns: List[ConcernReference] = []
    has_follow_up: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "student_id": "student-uuid",
                "teacher_id": "teacher-uuid",
                "class_id": "class-uuid",
                "section_id": "section-uuid",
                "subject_id": "subject-uuid",
                "observation_date": "2026-02-15T10:30:00Z",
                "category": "behaviour",
                "description": "Jamie was disruptive during mathematics class today. Interrupted lesson 3 times by talking to neighboring students. When asked to focus, responded with disrespectful tone. This is the third incident this week.",
                "severity": "concerning",
                "context": "During quadratic equations lesson, period 3",
                "action_taken": "Student was given a warning and moved to front row. Will monitor closely tomorrow.",
                "shared_with_parents": False,
                "shared_with_counselor": True,
                "follow_up_required": True,
                "follow_up_date": "2026-02-18T00:00:00Z",
                "tags": ["classroom_behavior", "mathematics", "repeated_incident"],
                "evidence_attachments": None,
                "created_at": "2026-02-15T11:00:00Z",
                "is_deleted": False,
                "student": {
                    "id": "student-uuid",
                    "admission_number": "STU2026045",
                    "full_name": "Jamie Smith",
                    "class_name": "Grade 10",
                    "section_name": "A"
                },
                "teacher": {
                    "id": "teacher-uuid",
                    "employee_id": "TEACH2026001",
                    "full_name": "Ms. Sarah Chen",
                    "position": "Mathematics Teacher",
                    "department": "Science & Mathematics"
                },
                "class_section": {
                    "class_id": "class-uuid",
                    "class_name": "Grade 10",
                    "section_id": "section-uuid",
                    "section_name": "A"
                },
                "related_concerns": [
                    {
                        "id": "concern-uuid",
                        "type": "behaviour",
                        "title": "Repeated classroom disruptions",
                        "status": "assigned"
                    }
                ],
                "has_follow_up": True
            }
        }

class ObservationSummary(BaseModel):
    """
    Summary of observations for a student or period
    """
    student_id: UUID
    student_name: str
    total_observations: int = 0
    positive_count: int = 0
    neutral_count: int = 0
    concerning_count: int = 0
    critical_count: int = 0
    most_recent_observation: Optional[datetime] = None
    categories_breakdown: Dict[str, int] = Field(default_factory=dict)
    requires_attention: bool = False

class ObservationTrend(BaseModel):
    """
    Trend analysis for observations over time
    """
    period_start: datetime
    period_end: datetime
    total_observations: int = 0
    trend_direction: str = Field(..., pattern=r"^(improving|stable|declining)$")
    category_trends: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        description="{'academic': {'positive': 5, 'concerning': 2}, ...}"
    )
    notable_changes: List[str] = []

class WellnessCheckBase(BaseModel):
    """
    Base schema for counselor wellness checks
    """
    check_date: datetime
    academic_wellness: int = Field(..., ge=1, le=5, description="1=Poor, 5=Excellent")
    emotional_wellness: int = Field(..., ge=1, le=5)
    social_wellness: int = Field(..., ge=1, le=5)
    physical_wellness: int = Field(..., ge=1, le=5)
    overall_wellness_score: int = Field(..., ge=1, le=5)
    notes: Optional[str] = Field(None, max_length=2000)
    recommendations: Optional[str] = Field(None, max_length=1000)
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None
    shared_with_parents: bool = False
    shared_with_teachers: bool = False
    confidentiality_level: str = Field(
        default="standard",
        pattern=r"^(standard|sensitive|highly_confidential)$"
    )

    @validator('overall_wellness_score', always=True)
    def calculate_overall_score(cls, v, values):
        if v == 0:
            scores = [
                values.get('academic_wellness', 3),
                values.get('emotional_wellness', 3),
                values.get('social_wellness', 3),
                values.get('physical_wellness', 3)
            ]
            return sum(scores) // len(scores)
        return v

class WellnessCheckCreate(WellnessCheckBase):
    student_id: UUID
    counselor_id: UUID

class WellnessCheckUpdate(BaseModel):
    academic_wellness: Optional[int] = None
    emotional_wellness: Optional[int] = None
    social_wellness: Optional[int] = None
    physical_wellness: Optional[int] = None
    notes: Optional[str] = None
    recommendations: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime] = None

class WellnessCheckResponse(WellnessCheckBase, TimestampSchema):
    id: UUID
    student_id: UUID
    counselor_id: UUID
    is_deleted: bool
    student: StudentReference
    counselor: StaffReference
    previous_check: Optional["WellnessCheckReference"] = None
    wellness_change: Optional[Dict[str, int]] = None  # {"academic": +1, "emotional": -1, ...}

    class Config:
        json_schema_extra = {
            "example": {
                "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                "student_id": "student-uuid",
                "counselor_id": "counselor-uuid",
                "check_date": "2026-02-10T14:00:00Z",
                "academic_wellness": 3,
                "emotional_wellness": 2,
                "social_wellness": 4,
                "physical_wellness": 5,
                "overall_wellness_score": 3,
                "notes": "Jamie appears stressed about upcoming quarterly exams. Reports difficulty sleeping. Social interactions remain positive with peer group. Physical health is good with active participation in sports.",
                "recommendations": "Schedule follow-up in 2 weeks. Recommend relaxation techniques before exams. Consider meeting with parents to discuss exam stress management.",
                "follow_up_required": True,
                "follow_up_date": "2026-02-24T00:00:00Z",
                "shared_with_parents": False,
                "shared_with_teachers": False,
                "confidentiality_level": "sensitive",
                "created_at": "2026-02-10T14:30:00Z",
                "is_deleted": False,
                "student": {
                    "id": "student-uuid",
                    "admission_number": "STU2026045",
                    "full_name": "Jamie Smith",
                    "class_name": "Grade 10",
                    "section_name": "A"
                },
                "counselor": {
                    "id": "counselor-uuid",
                    "employee_id": "COUN2026001",
                    "full_name": "Dr. Anjali Patel",
                    "position": "School Counselor",
                    "department": "Student Welfare"
                },
                "previous_check": {
                    "id": "prev-check-uuid",
                    "check_date": "2026-01-15T13:00:00Z",
                    "overall_wellness_score": 4
                },
                "wellness_change": {
                    "academic": 0,
                    "emotional": -1,
                    "social": 0,
                    "physical": 0,
                    "overall": -1
                }
            }
        }

class WellnessCheckReference(BaseModel):
    id: UUID
    check_date: datetime
    overall_wellness_score: int

class WellnessCheckSummary(BaseModel):
    """
    Summary of wellness checks for reporting
    """
    student_id: UUID
    student_name: str
    total_checks: int = 0
    latest_check_date: Optional[datetime] = None
    latest_overall_score: int = 3
    score_trend: str = Field(..., pattern=r"^(improving|stable|declining)$")
    areas_of_concern: List[str] = []
    follow_up_pending: bool = False

class BulkObservationCreate(BaseModel):
    """
    Create multiple observations for different students
    """
    observations: List[StudentObservationCreate] = Field(..., min_items=1, max_items=50)
    auto_create_concerns: bool = Field(default=False, description="Auto-create concerns for critical observations")

    @validator('observations')
    def validate_unique_students(cls, v):
        student_ids = [obs.student_id for obs in v]
        if len(student_ids) != len(set(student_ids)):
            raise ValueError('Cannot create multiple observations for same student in bulk operation')
        return v

class ObservationReportFilter(BaseModel):
    """
    Filter for observation reports
    """
    school_id: UUID
    class_id: Optional[UUID] = None
    section_id: Optional[UUID] = None
    student_id: Optional[UUID] = None
    teacher_id: Optional[UUID] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    include_deleted: bool = False

    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v and values.get('date_from') and v < values['date_from']:
            raise ValueError('date_to must be after date_from')
        return v

# Resolve forward references
StudentObservationResponse.model_rebuild()
WellnessCheckResponse.model_rebuild()
WellnessCheckReference.model_rebuild()