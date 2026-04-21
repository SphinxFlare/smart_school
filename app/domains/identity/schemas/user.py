# domains/identity/schemas/user.py

from pydantic import EmailStr, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date

from .base import DomainBase, TimestampSchema
from types.types import UserRoleType


# ---------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------

class UserBase(DomainBase):
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: Optional[date] = None


# ---------------------------------------------------------------------
# Create / Update
# ---------------------------------------------------------------------

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    school_id: UUID


class UserUpdate(DomainBase):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    date_of_birth: Optional[date] = None


# ---------------------------------------------------------------------
# Role (lightweight, no joins)
# ---------------------------------------------------------------------

class UserRoleAssignment(DomainBase):
    role: UserRoleType
    assigned_at: datetime
    is_active: bool


# ---------------------------------------------------------------------
# Response (LEAN — no profiles)
# ---------------------------------------------------------------------

class UserResponse(UserBase, TimestampSchema):
    id: UUID
    school_id: UUID
    is_active: bool
    is_deleted: bool
    last_login: Optional[datetime] = None
    roles: List[UserRoleAssignment] = []


# ---------------------------------------------------------------------
# Reference (for embedding)
# ---------------------------------------------------------------------

class UserReference(DomainBase):
    id: UUID
    full_name: str
    email: EmailStr