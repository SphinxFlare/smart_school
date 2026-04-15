# academic/schemas/subject.py

from pydantic import BaseModel, Field, validator
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from .base import DomainBase, TimestampSchema

if TYPE_CHECKING:
    from app.domains.identity.schemas.class_section import ClassSectionReference
else:
    ClassSectionReference = "ClassSectionReference"

class SubjectBase(DomainBase):
    name: str = Field(..., min_length=2, max_length=100, description="Subject name (Mathematics, Science, etc.)")
    code: str = Field(..., min_length=3, max_length=20, pattern=r"^[A-Z]{2,4}\d{2,4}$", description="Subject code (MATH101, SCI002)")
    description: Optional[str] = Field(None, max_length=500)
    credit_hours: Optional[int] = Field(None, ge=1, le=10)
    is_core_subject: bool = Field(default=True, description="Core subject vs elective")
    syllabus_url: Optional[str] = Field(None, max_length=500)

    @validator('name')
    def validate_name_case(cls, v):
        return v.strip().title()

class SubjectCreate(SubjectBase):
    school_id: UUID

class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    credit_hours: Optional[int] = None
    is_core_subject: Optional[bool] = None
    syllabus_url: Optional[str] = None
    is_active: Optional[bool] = None

class SubjectTeachingAssignment(BaseModel):
    """Minimal teaching assignment context"""
    class_section: ClassSectionReference
    teacher_name: str
    academic_year: str

class SubjectResponse(SubjectBase, TimestampSchema):
    id: UUID
    school_id: UUID
    is_active: bool
    is_deleted: bool
    teaching_assignments: List[SubjectTeachingAssignment] = []
    total_classes_offered: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "school_id": "school-uuid",
                "name": "Mathematics",
                "code": "MATH101",
                "description": "Core mathematics curriculum covering algebra, geometry, and calculus fundamentals",
                "credit_hours": 5,
                "is_core_subject": True,
                "syllabus_url": "https://school.edu/syllabus/math101.pdf",
                "is_active": True,
                "created_at": "2026-01-10T08:00:00Z",
                "is_deleted": False,
                "teaching_assignments": [
                    {
                        "class_section": {
                            "class_id": "class-uuid-1",
                            "class_name": "Grade 10",
                            "section_id": "section-uuid-1",
                            "section_name": "A"
                        },
                        "teacher_name": "Dr. Anjali Sharma",
                        "academic_year": "2025-2026"
                    },
                    {
                        "class_section": {
                            "class_id": "class-uuid-2",
                            "class_name": "Grade 12",
                            "section_id": "section-uuid-2",
                            "section_name": "Science"
                        },
                        "teacher_name": "Mr. Rajesh Kumar",
                        "academic_year": "2025-2026"
                    }
                ],
                "total_classes_offered": 8
            }
        }

class SubjectReference(BaseModel):
    id: UUID
    name: str
    code: str
    is_core_subject: bool

# Resolve forward references
SubjectResponse.model_rebuild()