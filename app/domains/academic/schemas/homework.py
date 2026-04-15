# academic/schemas/homework.py


from pydantic import BaseModel, Field, validator, HttpUrl
from typing import List, Optional, TYPE_CHECKING, Dict
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from .base import DomainBase, TimestampSchema

if TYPE_CHECKING:
    from app.domains.identity.schemas.student import StudentReference
    from app.domains.identity.schemas.user import UserReference
    from .subject import SubjectReference
    from app.domains.identity.schemas.class_section import ClassSectionReference
else:
    StudentReference = "StudentReference"
    UserReference = "UserReference"
    SubjectReference = "SubjectReference"
    ClassSectionReference = "ClassSectionReference"

class Attachment(BaseModel):
    """Homework attachment metadata"""
    name: str = Field(..., min_length=1, max_length=200)
    file_path: str = Field(..., max_length=500)
    file_type: str = Field(..., pattern=r"^(pdf|docx|jpg|png|zip|mp4)$")
    file_size_kb: int = Field(..., ge=1, le=102400)  # Max 100MB
    uploaded_at: datetime

class HomeworkBase(DomainBase):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    assigned_date: datetime
    due_date: datetime
    max_marks: Optional[Decimal] = Field(None, decimal_places=2, ge=0, le=100)
    allow_late_submission: bool = True
    late_penalty_percent: Optional[float] = Field(None, ge=0, le=100)
    attachments: List[Attachment] = Field(default_factory=list)
    instructions: Optional[str] = Field(None, max_length=1000)

    @validator('due_date')
    def validate_due_date(cls, v, values):
        if 'assigned_date' in values and v < values['assigned_date']:
            raise ValueError('Due date must be after assigned date')
        return v
    
    @validator('attachments')
    def validate_attachments(cls, v):
        if len(v) > 10:
            raise ValueError('Maximum 10 attachments allowed')
        return v

class HomeworkCreate(HomeworkBase):
    teacher_assignment_id: UUID

class HomeworkUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    max_marks: Optional[Decimal] = None
    allow_late_submission: Optional[bool] = None
    late_penalty_percent: Optional[float] = None
    instructions: Optional[str] = None
    is_active: Optional[bool] = None

class SubmissionAttachment(BaseModel):
    """Student submission attachment"""
    name: str
    file_path: str
    uploaded_at: datetime

class HomeworkSubmissionBase(BaseModel):
    status: str = Field(..., pattern=r"^(pending|submitted|late|missing|graded)$")
    submitted_at: Optional[datetime] = None
    file_path: Optional[str] = Field(None, max_length=500)
    remarks: Optional[str] = Field(None, max_length=500)
    marks_awarded: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    submission_attachments: List[SubmissionAttachment] = Field(default_factory=list)

    @validator('marks_awarded')
    def validate_marks(cls, v, values, **kwargs):
        # Validation will be handled at service layer with max_marks context
        return v

class HomeworkSubmissionCreate(HomeworkSubmissionBase):
    homework_id: UUID
    student_id: UUID

class HomeworkSubmissionUpdate(BaseModel):
    status: Optional[str] = None
    remarks: Optional[str] = None
    marks_awarded: Optional[Decimal] = None

class HomeworkSubmissionResponse(HomeworkSubmissionBase):
    id: UUID
    homework_id: UUID
    student_id: UUID
    graded_by_id: Optional[UUID] = None
    graded_at: Optional[datetime] = None
    created_at: datetime
    student: StudentReference
    graded_by: Optional[UserReference] = None

class HomeworkResponse(HomeworkBase, TimestampSchema):
    id: UUID
    teacher_assignment_id: UUID
    subject: SubjectReference
    class_section: ClassSectionReference
    teacher: UserReference
    is_active: bool
    is_deleted: bool
    total_submissions: int = 0
    submitted_count: int = 0
    graded_count: int = 0
    average_score: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "d4e5f6a7-b8c9-0123-def4-567890123456",
                "teacher_assignment_id": "assignment-uuid",
                "subject": {
                    "id": "subject-uuid",
                    "name": "Mathematics",
                    "code": "MATH101",
                    "is_core_subject": True
                },
                "class_section": {
                    "class_id": "class-uuid",
                    "class_name": "Grade 10",
                    "section_id": "section-uuid",
                    "section_name": "A"
                },
                "teacher": {
                    "id": "user-uuid",
                    "full_name": "Dr. Anjali Sharma",
                    "email": "a.sharma@school.edu",
                    "role": "teacher"
                },
                "title": "Quadratic Equations Practice Set",
                "description": "Solve all problems from Chapter 4, Exercise 4.3. Show all steps clearly.",
                "assigned_date": "2026-02-15T09:00:00Z",
                "due_date": "2026-02-22T23:59:59Z",
                "max_marks": 20.00,
                "allow_late_submission": True,
                "late_penalty_percent": 10.0,
                "attachments": [
                    {
                        "name": "quadratic_equations_worksheet.pdf",
                        "file_path": "/homework/2026/feb/quadratic_equations_worksheet.pdf",
                        "file_type": "pdf",
                        "file_size_kb": 1250,
                        "uploaded_at": "2026-02-15T08:45:00Z"
                    }
                ],
                "instructions": "Submit as PDF. Late submissions accepted with 10% penalty per day.",
                "is_active": True,
                "created_at": "2026-02-15T08:50:00Z",
                "is_deleted": False,
                "total_submissions": 38,
                "submitted_count": 32,
                "graded_count": 28,
                "average_score": 16.75
            }
        }

class HomeworkWithSubmissions(HomeworkResponse):
    submissions: List[HomeworkSubmissionResponse] = []

class StudentHomeworkSummary(BaseModel):
    """Student's homework performance summary"""
    homework_id: UUID
    title: str
    subject: SubjectReference
    due_date: datetime
    status: str
    submitted_at: Optional[datetime] = None
    marks_obtained: Optional[Decimal] = None
    max_marks: Optional[Decimal] = None
    feedback: Optional[str] = None
    is_late: bool = False

# Resolve forward references
HomeworkResponse.model_rebuild()
HomeworkSubmissionResponse.model_rebuild()
HomeworkWithSubmissions.model_rebuild()
StudentHomeworkSummary.model_rebuild()