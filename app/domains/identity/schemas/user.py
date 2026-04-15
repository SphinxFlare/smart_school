# domains/identity/schemas/user.py

from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from .base import DomainBase, TimestampSchema
from types.types import UserRoleType

# Forward references to avoid circular imports
if TYPE_CHECKING:
    from .student import StudentReference
    from .parent import ParentReference
    from .staff import StaffReference
else:
    StudentReference = "StudentReference"
    ParentReference = "ParentReference"
    StaffReference = "StaffReference"

class UserBase(DomainBase):
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: Optional[datetime] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    school_id: UUID

    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    date_of_birth: Optional[datetime] = None

class UserRoleAssignment(BaseModel):
    role: UserRoleType
    assigned_at: datetime
    is_active: bool

class UserResponse(UserBase, TimestampSchema):
    id: UUID
    school_id: UUID
    is_active: bool
    last_login: Optional[datetime] = None
    is_deleted: bool
    roles: List[UserRoleAssignment]
    student_profile: Optional[StudentReference] = None
    parent_profile: Optional[ParentReference] = None
    staff_profile: Optional[StaffReference] = None

class UserReference(BaseModel):
    id: UUID
    full_name: str
    email: str
    role: str

# Update forward references
UserResponse.model_rebuild()