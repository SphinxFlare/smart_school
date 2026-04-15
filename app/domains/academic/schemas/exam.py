# academic/schemas/exam.py


from pydantic import BaseModel, Field, validator
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from .base import DomainBase, TimestampSchema
from types.types import ExamType

if TYPE_CHECKING:
    from app.domains.identity.schemas.class_section import ClassSectionReference
    from .subject import SubjectReference
    from app.domains.identity.schemas.staff import StaffReference
else:
    ClassSectionReference = "ClassSectionReference"
    SubjectReference = "SubjectReference"
    StaffReference = "StaffReference"

class ExamBase(DomainBase):
    name: str = Field(..., min_length=3, max_length=150)
    type: ExamType = Field(..., description="Weekly, Monthly, or Quarterly")
    start_date: datetime
    end_date: datetime
    description: Optional[str] = Field(None, max_length=1000)
    max_marks: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    passing_marks: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    is_published: bool = False

    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    @validator('passing_marks')
    def validate_passing_marks(cls, v, values):
        if v and 'max_marks' in values and values['max_marks'] and v > values['max_marks']:
            raise ValueError('Passing marks cannot exceed maximum marks')
        return v

class ExamCreate(ExamBase):
    school_id: UUID
    academic_year_id: UUID
    created_by_id: UUID

class ExamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_marks: Optional[Decimal] = None
    passing_marks: Optional[Decimal] = None
    is_published: Optional[bool] = None

class ExamScheduleBase(BaseModel):
    date: date
    start_time: datetime
    end_time: datetime
    room: Optional[str] = Field(None, max_length=50)
    instructions: Optional[str] = Field(None, max_length=500)

    @validator('end_time')
    def validate_time_order(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v

class ExamScheduleCreate(ExamScheduleBase):
    exam_id: UUID
    class_id: UUID
    section_id: UUID
    subject_id: UUID
    invigilator_id: Optional[UUID] = None

class ExamScheduleUpdate(BaseModel):
    date: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    room: Optional[str] = None
    invigilator_id: Optional[UUID] = None
    is_active: Optional[bool] = None

class ExamScheduleResponse(ExamScheduleBase):
    id: UUID
    exam_id: UUID
    class_section: ClassSectionReference
    subject: SubjectReference
    invigilator: Optional[StaffReference] = None
    is_active: bool
    created_at: datetime

class ExamResponse(ExamBase, TimestampSchema):
    id: UUID
    school_id: UUID
    academic_year_id: UUID
    created_by_id: UUID
    is_deleted: bool
    schedules: List[ExamScheduleResponse] = []
    total_schedules: int = 0
    published_schedules: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                "school_id": "school-uuid",
                "academic_year_id": "academic-year-uuid",
                "name": "Quarterly Examination - Term 2",
                "type": "quarterly",
                "start_date": "2026-03-10T00:00:00Z",
                "end_date": "2026-03-15T00:00:00Z",
                "description": "Comprehensive assessment covering syllabus from January to March",
                "max_marks": 500.00,
                "passing_marks": 200.00,
                "is_published": True,
                "created_by_id": "user-uuid",
                "created_at": "2026-02-01T10:00:00Z",
                "is_deleted": False,
                "schedules": [
                    {
                        "id": "sched-uuid-1",
                        "exam_id": "exam-uuid",
                        "class_section": {
                            "class_id": "class-uuid",
                            "class_name": "Grade 10",
                            "section_id": "section-uuid",
                            "section_name": "A"
                        },
                        "subject": {
                            "id": "subject-uuid",
                            "name": "Mathematics",
                            "code": "MATH101",
                            "is_core_subject": True
                        },
                        "date": "2026-03-11",
                        "start_time": "2026-03-11T09:00:00Z",
                        "end_time": "2026-03-11T11:30:00Z",
                        "room": "Room 101",
                        "invigilator": {
                            "id": "staff-uuid",
                            "employee_id": "TEACH2026001",
                            "full_name": "Dr. Anjali Sharma",
                            "position": "Senior Mathematics Teacher"
                        },
                        "is_active": True,
                        "created_at": "2026-02-05T14:30:00Z"
                    }
                ],
                "total_schedules": 12,
                "published_schedules": 12
            }
        }

class ExamResultSummary(BaseModel):
    """Student exam result summary"""
    exam_id: UUID
    exam_name: str
    exam_type: ExamType
    subject: SubjectReference
    marks_obtained: Optional[Decimal] = None
    max_marks: Decimal
    percentage: Optional[float] = None
    grade: Optional[str] = None
    status: str  # "completed", "absent", "pending"
    exam_date: date

    @validator('percentage', always=True)
    def calculate_percentage(cls, v, values):
        if values.get('marks_obtained') and values.get('max_marks'):
            return round((float(values['marks_obtained']) / float(values['max_marks'])) * 100, 2)
        return None

# Resolve forward references
ExamResponse.model_rebuild()
ExamScheduleResponse.model_rebuild()
ExamResultSummary.model_rebuild()