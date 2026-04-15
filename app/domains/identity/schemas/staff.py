# domains/identity/schemas/staff.py


from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from .base import DomainBase, TimestampSchema

if TYPE_CHECKING:
    from .user import UserReference
    from app.domains.academic.schemas.subject import SubjectReference
else:
    UserReference = "UserReference"
    SubjectReference = "SubjectReference"

class StaffBase(DomainBase):
    employee_id: str = Field(..., max_length=20, pattern=r"^[A-Z]{2,4}\d{4,6}$")
    position: str = Field(..., min_length=3, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    date_of_joining: datetime
    qualifications: Optional[List[str]] = Field(None, max_items=10)
    emergency_contact_name: str = Field(..., min_length=2, max_length=100)
    emergency_contact_phone: str = Field(..., min_length=10, max_length=20)

    @field_validator('date_of_joining')
    def validate_joining_date(cls, v):
        if v > datetime.utcnow():
            raise ValueError('Joining date cannot be in the future')
        if v.year < 1950:
            raise ValueError('Invalid joining date')
        return v

class StaffCreate(StaffBase):
    user_id: UUID

class StaffUpdate(BaseModel):
    position: Optional[str] = None
    department: Optional[str] = None
    qualifications: Optional[List[str]] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

class StaffAssignmentSummary(BaseModel):
    class_name: str
    section_name: str
    subject_name: str
    is_primary: bool

class StaffResponse(StaffBase, TimestampSchema):
    id: UUID
    user_id: UUID
    is_deleted: bool
    user: UserReference
    current_assignments: List[StaffAssignmentSummary] = []
    total_classes_handled: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "user_id": "user-uuid",
                "employee_id": "TEACH2026001",
                "position": "Senior Mathematics Teacher",
                "department": "Science & Mathematics",
                "date_of_joining": "2020-08-01T00:00:00Z",
                "qualifications": ["B.Ed Mathematics", "M.Sc Applied Mathematics"],
                "emergency_contact_name": "John Rodriguez",
                "emergency_contact_phone": "+91 9876543210",
                "created_at": "2026-01-10T09:15:00Z",
                "is_deleted": False,
                "user": {
                    "id": "user-uuid",
                    "full_name": "Dr. Anjali Sharma",
                    "email": "a.sharma@school.edu",
                    "role": "teacher"
                },
                "current_assignments": [
                    {
                        "class_name": "Grade 10",
                        "section_name": "A",
                        "subject_name": "Mathematics",
                        "is_primary": True
                    },
                    {
                        "class_name": "Grade 12",
                        "section_name": "Science",
                        "subject_name": "Advanced Calculus",
                        "is_primary": False
                    }
                ],
                "total_classes_handled": 5
            }
        }

class StaffReference(BaseModel):
    id: UUID
    employee_id: str
    full_name: str
    position: str
    department: Optional[str] = None

# Rebuild models with forward references
StaffResponse.model_rebuild()