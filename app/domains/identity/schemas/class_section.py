# identity/schemas/class_section.py

from pydantic import BaseModel, Field, validator
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from .base import DomainBase, TimestampSchema

if TYPE_CHECKING:
    from .staff import StaffReference
else:
    StaffReference = "StaffReference"

class ClassBase(DomainBase):
    name: str = Field(..., min_length=2, max_length=100, description="e.g., 'Grade 1', 'Class X', 'KG'")
    level: int = Field(..., ge=0, le=15, description="Numeric level for sorting (0=KG, 1=Grade 1, etc.)")
    description: Optional[str] = Field(None, max_length=500)

class ClassCreate(ClassBase):
    school_id: UUID
    academic_year_id: UUID

class ClassUpdate(BaseModel):
    name: Optional[str] = None
    level: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ClassResponse(ClassBase, TimestampSchema):
    id: UUID
    school_id: UUID
    academic_year_id: UUID
    is_active: bool
    is_deleted: bool
    total_students: int = 0
    total_sections: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                "school_id": "school-uuid",
                "academic_year_id": "academic-year-uuid",
                "name": "Grade 10",
                "level": 10,
                "description": "Secondary education final year",
                "is_active": True,
                "created_at": "2026-01-05T08:00:00Z",
                "is_deleted": False,
                "total_students": 120,
                "total_sections": 4
            }
        }

class ClassReference(BaseModel):
    id: UUID
    name: str
    level: int

class SectionBase(DomainBase):
    name: str = Field(..., min_length=1, max_length=20, description="Section identifier (A, B, C, Science, Commerce, etc.)")
    capacity: Optional[int] = Field(None, ge=1, le=100, description="Maximum students allowed")
    room_number: Optional[str] = Field(None, max_length=20)
    class_teacher_id: Optional[UUID] = None

class SectionCreate(SectionBase):
    class_id: UUID

class SectionUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    room_number: Optional[str] = None
    class_teacher_id: Optional[UUID] = None
    is_active: Optional[bool] = None

class SectionResponse(SectionBase, TimestampSchema):
    id: UUID
    class_id: UUID
    is_active: bool
    is_deleted: bool
    current_student_count: int = 0
    class_teacher: Optional[StaffReference] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "d4e5f6a7-b8c9-0123-def4-567890123456",
                "class_id": "class-uuid",
                "name": "A",
                "capacity": 40,
                "room_number": "Room 101",
                "class_teacher_id": "staff-uuid",
                "is_active": True,
                "created_at": "2026-01-05T08:30:00Z",
                "is_deleted": False,
                "current_student_count": 38,
                "class_teacher": {
                    "id": "staff-uuid",
                    "employee_id": "TEACH2026001",
                    "full_name": "Dr. Anjali Sharma",
                    "position": "Senior Mathematics Teacher",
                    "department": "Science & Mathematics"
                }
            }
        }

class SectionReference(BaseModel):
    id: UUID
    name: str
    class_id: UUID

class ClassSectionReference(BaseModel):
    """Combined reference for student context"""
    class_id: UUID
    class_name: str
    section_id: UUID
    section_name: str
    room_number: Optional[str] = None

# Rebuild models with forward references
SectionResponse.model_rebuild()