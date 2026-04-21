# identity/schemas/student.py


from pydantic import Field
from typing import Optional
from uuid import UUID
from datetime import date

from .base import DomainBase, TimestampSchema
from .class_section import ClassSectionReference


# ---------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------

class StudentBase(DomainBase):
    admission_number: str = Field(..., max_length=20)
    date_of_birth: date
    blood_group: Optional[str] = Field(None, max_length=10)
    emergency_contact_name: str
    emergency_contact_phone: str


# ---------------------------------------------------------------------
# Create / Update
# ---------------------------------------------------------------------

class StudentCreate(StudentBase):
    user_id: UUID
    class_id: UUID
    section_id: UUID


class StudentUpdate(DomainBase):
    blood_group: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    class_id: Optional[UUID] = None
    section_id: Optional[UUID] = None


# ---------------------------------------------------------------------
# Response (LEAN)
# ---------------------------------------------------------------------

class StudentResponse(StudentBase, TimestampSchema):
    id: UUID
    user_id: UUID
    class_id: UUID
    section_id: UUID
    is_deleted: bool
    class_section: Optional[ClassSectionReference] = None


# ---------------------------------------------------------------------
# Reference (used across domain)
# ---------------------------------------------------------------------

class StudentReference(DomainBase):
    id: UUID
    admission_number: str
    full_name: str
    class_name: str
    section_name: str