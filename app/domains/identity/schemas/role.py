# identity/schemas/role.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from .base import DomainBase, TimestampSchema
from types.types import UserRoleType

class RoleBase(DomainBase):
    name: UserRoleType = Field(..., description="System-defined role type")
    description: Optional[str] = Field(None, max_length=500)
    permissions: Optional[Dict[str, Any]] = Field(
        None,
        description="Permission structure: {'module': {'action': true}}"
    )

class RoleCreate(RoleBase):
    pass  # Name is required enum

class RoleUpdate(BaseModel):
    description: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class RoleResponse(RoleBase, TimestampSchema):
    id: UUID
    is_active: bool
    user_count: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "id": "e5f6a7b8-c9d0-1234-ef56-789012345678",
                "name": "teacher",
                "description": "Academic staff responsible for teaching and student evaluation",
                "permissions": {
                    "academic": {
                        "attendance": ["read", "write"],
                        "exams": ["read", "write", "grade"],
                        "homework": ["assign", "grade", "view"]
                    },
                    "communication": {
                        "messages": ["send_to_parents", "receive_from_parents"],
                        "announcements": ["view"]
                    },
                    "welfare": {
                        "concerns": ["report", "view_own"],
                        "observations": ["create", "view"]
                    }
                },
                "is_active": True,
                "created_at": "2026-01-01T00:00:00Z",
                "user_count": 45
            }
        }

class RoleReference(BaseModel):
    id: UUID
    name: UserRoleType
    description: Optional[str] = None

class UserRoleAssignment(BaseModel):
    """Represents a user's role assignment"""
    role: RoleReference
    assigned_at: datetime
    assigned_by: Optional["UserReference"] = None  # Forward reference
    is_active: bool

    class Config:
        json_schema_extra = {
            "example": {
                "role": {
                    "id": "role-uuid",
                    "name": "counselor",
                    "description": "Student welfare and guidance specialist"
                },
                "assigned_at": "2026-01-15T10:30:00Z",
                "assigned_by": {
                    "id": "admin-uuid",
                    "full_name": "Admin User",
                    "email": "admin@school.edu",
                    "role": "admin"
                },
                "is_active": True
            }
        }

# Handle forward reference for UserReference
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .user import UserReference
else:
    UserReference = "UserReference"

UserRoleAssignment.model_rebuild()