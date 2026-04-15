# identity/schemas/parent.py


from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from .base import DomainBase, TimestampSchema

if TYPE_CHECKING:
    from .student import StudentWithRelationship
    from .user import UserReference
else:
    StudentWithRelationship = "StudentWithRelationship"
    UserReference = "UserReference"

class ParentBase(DomainBase):
    occupation: Optional[str] = Field(None, max_length=100)
    employer: Optional[str] = Field(None, max_length=150)
    annual_income: Optional[float] = Field(None, ge=0)

class ParentCreate(ParentBase):
    user_id: UUID

class ParentUpdate(BaseModel):
    occupation: Optional[str] = None
    employer: Optional[str] = None
    annual_income: Optional[float] = None

class ParentResponse(ParentBase, TimestampSchema):
    id: UUID
    user_id: UUID
    is_deleted: bool
    user: UserReference
    students: List[StudentWithRelationship] = []

    class Config:
        json_schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "user_id": "user-uuid",
                "occupation": "Software Engineer",
                "employer": "Tech Innovations Inc.",
                "annual_income": 120000.0,
                "created_at": "2026-01-15T10:30:00Z",
                "updated_at": "2026-02-01T14:22:15Z",
                "is_deleted": False,
                "user": {
                    "id": "user-uuid",
                    "full_name": "Maria Rodriguez",
                    "email": "maria.rodriguez@email.com",
                    "role": "parent"
                },
                "students": [
                    {
                        "student": {
                            "id": "student-uuid-1",
                            "admission_number": "STU2026045",
                            "full_name": "Jamie Smith",
                            "class_name": "Grade 8",
                            "section_name": "B"
                        },
                        "relationship": "mother",
                        "is_primary": True
                    },
                    {
                        "student": {
                            "id": "student-uuid-2",
                            "admission_number": "STU2026078",
                            "full_name": "Alex Smith",
                            "class_name": "Grade 5",
                            "section_name": "A"
                        },
                        "relationship": "mother",
                        "is_primary": False
                    }
                ]
            }
        }

class ParentReference(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    occupation: Optional[str] = None

# Rebuild models with forward references
ParentResponse.model_rebuild()