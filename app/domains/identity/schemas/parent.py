# identity/schemas/parent.py


from pydantic import Field, EmailStr
from typing import Optional
from uuid import UUID

from .base import DomainBase, TimestampSchema


# ---------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------

class ParentBase(DomainBase):
    occupation: Optional[str] = Field(None, max_length=100)
    employer: Optional[str] = Field(None, max_length=150)
    annual_income: Optional[float] = Field(None, ge=0)


# ---------------------------------------------------------------------
# Create / Update
# ---------------------------------------------------------------------

class ParentCreate(ParentBase):
    user_id: UUID


class ParentUpdate(DomainBase):
    occupation: Optional[str] = None
    employer: Optional[str] = None
    annual_income: Optional[float] = None


# ---------------------------------------------------------------------
# Response (LEAN — no students list)
# ---------------------------------------------------------------------

class ParentResponse(ParentBase, TimestampSchema):
    id: UUID
    user_id: UUID
    is_deleted: bool


# ---------------------------------------------------------------------
# Reference (used in aggregates)
# ---------------------------------------------------------------------

class ParentReference(DomainBase):
    id: UUID
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    occupation: Optional[str] = None