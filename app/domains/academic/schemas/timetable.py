# academic/schemas/timetable.py


from pydantic import BaseModel, Field, validator
from typing import Optional, TYPE_CHECKING
from uuid import UUID
from datetime import time, datetime
from .base import DomainBase

if TYPE_CHECKING:
    from app.domains.identity.schemas.class_section import ClassSectionReference
    from .subject import SubjectReference
    from app.domains.identity.schemas.staff import StaffReference
else:
    ClassSectionReference = "ClassSectionReference"
    SubjectReference = "SubjectReference"
    StaffReference = "StaffReference"

class ClassTimetableBase(DomainBase):
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    period_number: int = Field(..., ge=1, le=15)
    start_time: time
    end_time: time
    room: Optional[str] = Field(None, max_length=20)
    is_elective: bool = False

    @validator('end_time')
    def validate_time_order(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v

class ClassTimetableCreate(ClassTimetableBase):
    class_id: UUID
    section_id: UUID
    subject_id: UUID
    teacher_assignment_id: UUID
    academic_year_id: UUID

class ClassTimetableUpdate(BaseModel):
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    room: Optional[str] = None
    teacher_assignment_id: Optional[UUID] = None
    is_active: Optional[bool] = None

class TimetablePeriod(BaseModel):
    """Period details for daily schedule"""
    period_number: int
    subject: SubjectReference
    teacher: StaffReference
    room: Optional[str] = None
    start_time: time
    end_time: time

class ClassTimetableResponse(ClassTimetableBase):
    id: UUID
    class_section: ClassSectionReference
    subject: SubjectReference
    teacher: StaffReference
    academic_year_id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
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
                "teacher": {
                    "id": "staff-uuid",
                    "employee_id": "TEACH2026001",
                    "full_name": "Dr. Anjali Sharma",
                    "position": "Senior Mathematics Teacher"
                },
                "day_of_week": 1,  # Tuesday
                "period_number": 3,
                "start_time": "10:15:00",
                "end_time": "11:00:00",
                "room": "Room 101",
                "is_elective": False,
                "academic_year_id": "academic-year-uuid",
                "is_active": True,
                "created_at": "2026-01-15T09:30:00Z"
            }
        }

class DailyScheduleResponse(BaseModel):
    """Consolidated daily timetable for a class-section"""
    date: datetime
    day_of_week: int
    class_section: ClassSectionReference
    periods: list[TimetablePeriod]
    total_periods: int
    school_start_time: time
    school_end_time: time

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2026-02-18T00:00:00Z",
                "day_of_week": 2,  # Wednesday
                "class_section": {
                    "class_id": "class-uuid",
                    "class_name": "Grade 10",
                    "section_id": "section-uuid",
                    "section_name": "A"
                },
                "periods": [
                    {
                        "period_number": 1,
                        "subject": {"id": "sub1", "name": "English", "code": "ENG101", "is_core_subject": True},
                        "teacher": {"id": "t1", "employee_id": "TEACH2026005", "full_name": "Ms. Priya Singh", "position": "English Teacher"},
                        "room": "Room 105",
                        "start_time": "08:00:00",
                        "end_time": "08:45:00"
                    },
                    {
                        "period_number": 2,
                        "subject": {"id": "sub2", "name": "Mathematics", "code": "MATH101", "is_core_subject": True},
                        "teacher": {"id": "t2", "employee_id": "TEACH2026001", "full_name": "Dr. Anjali Sharma", "position": "Senior Mathematics Teacher"},
                        "room": "Room 101",
                        "start_time": "08:45:00",
                        "end_time": "09:30:00"
                    }
                ],
                "total_periods": 8,
                "school_start_time": "08:00:00",
                "school_end_time": "15:30:00"
            }
        }

# Resolve forward references
ClassTimetableResponse.model_rebuild()
DailyScheduleResponse.model_rebuild()