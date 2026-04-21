# domains/identity/schemas/staff.py


from pydantic import Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from .base import DomainBase, TimestampSchema


# ---------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------

class StaffBase(DomainBase):
    employee_id: str = Field(..., max_length=20, pattern=r"^[A-Z]{2,4}\d{4,6}$")
    position: str = Field(..., min_length=3, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    date_of_joining: datetime
    qualifications: Optional[List[str]] = Field(None, max_items=10)
    emergency_contact_name: str = Field(..., min_length=2, max_length=100)
    emergency_contact_phone: str = Field(..., min_length=10, max_length=20)


# ---------------------------------------------------------------------
# Create / Update
# ---------------------------------------------------------------------

class StaffCreate(StaffBase):
    user_id: UUID


class StaffUpdate(DomainBase):
    position: Optional[str] = None
    department: Optional[str] = None
    qualifications: Optional[List[str]] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


# ---------------------------------------------------------------------
# Response (LEAN)
# ---------------------------------------------------------------------

class StaffResponse(StaffBase, TimestampSchema):
    id: UUID
    user_id: UUID
    is_deleted: bool


# ---------------------------------------------------------------------
# Reference (used across domain)
# ---------------------------------------------------------------------

class StaffReference(DomainBase):
    id: UUID
    employee_id: str
    full_name: str
    position: str
    department: Optional[str] = None