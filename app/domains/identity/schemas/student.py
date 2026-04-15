# identity/schemas/student.py


from pydantic import BaseModel, Field
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from .base import DomainBase, TimestampSchema

if TYPE_CHECKING:
    from .user import UserReference
    from .parent import ParentWithRelationship, ParentReference
    from .class_section import ClassSectionReference
else:
    UserReference = "UserReference"
    ParentWithRelationship = "ParentWithRelationship"
    ClassSectionReference = "ClassSectionReference"

class StudentBase(DomainBase):
    admission_number: str = Field(..., max_length=20)
    date_of_birth: datetime
    blood_group: Optional[str] = Field(None, max_length=10)
    emergency_contact_name: str
    emergency_contact_phone: str

class StudentCreate(StudentBase):
    user_id: UUID
    class_id: UUID
    section_id: UUID

class StudentUpdate(BaseModel):
    blood_group: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    class_id: Optional[UUID] = None
    section_id: Optional[UUID] = None

class StudentResponse(StudentBase, TimestampSchema):
    id: UUID
    user_id: UUID
    class_id: UUID
    section_id: UUID
    is_deleted: bool
    user: UserReference
    class_section: ClassSectionReference
    parent: List[ParentWithRelationship] = []

class StudentReference(BaseModel):
    id: UUID
    admission_number: str
    full_name: str
    class_name: str
    section_name: str

class ParentWithRelationship(BaseModel):
    parent: "ParentReference"  # Forward reference
    relationship: str
    is_primary: bool

StudentResponse.model_rebuild()
ParentWithRelationship.model_rebuild()