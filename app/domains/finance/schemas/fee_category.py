# finance/schemas/fee_category.py

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from .base import DomainBase, TimestampSchema
from types.types import FeeType

if TYPE_CHECKING:
    from app.domains.identity.schemas.user import UserReference
else:
    UserReference = "UserReference"

class CustomFeeType(BaseModel):
    """
    User-defined fee type structure for extensibility
    Example: {"type": "field_trip", "label": "Annual Field Trip Fee", "description": "Educational trip expenses"}
    """
    type: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-z0-9_]+$")
    label: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=200)

class FeeCategoryBase(DomainBase):
    type: FeeType = Field(..., description="System-defined fee type")
    custom_type: Optional[CustomFeeType] = Field(
        None,
        description="User-defined fee type (only when type='other')"
    )
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_school_defined: bool = Field(default=True, description="False = user-defined category")
    is_active: bool = True

    @validator('custom_type')
    def validate_custom_type(cls, v, values):
        if v and values.get('type') != FeeType.OTHER:
            raise ValueError('Custom type only allowed when type is "other"')
        if not v and values.get('type') == FeeType.OTHER:
            raise ValueError('Custom type required when type is "other"')
        return v

class FeeCategoryCreate(FeeCategoryBase):
    school_id: UUID
    created_by_id: UUID

class FeeCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    custom_type: Optional[CustomFeeType] = None
    is_active: Optional[bool] = None

class FeeCategoryResponse(FeeCategoryBase, TimestampSchema):
    id: UUID
    school_id: UUID
    created_by_id: UUID
    is_deleted: bool
    created_by: UserReference
    total_structures: int = 0
    total_students_affected: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "school_id": "school-uuid",
                "type": "yearly",
                "name": "Annual Tuition Fee",
                "description": "Annual tuition fee covering academic year expenses",
                "is_school_defined": True,
                "is_active": True,
                "created_by_id": "user-uuid",
                "created_at": "2026-01-10T09:00:00Z",
                "updated_at": "2026-01-15T14:30:00Z",
                "is_deleted": False,
                "created_by": {
                    "id": "user-uuid",
                    "full_name": "Admin User",
                    "email": "admin@school.edu",
                    "role": "admin"
                },
                "total_structures": 15,
                "total_students_affected": 1250
            }
        }

class CustomFeeCategoryExample(BaseModel):
    """Example of user-defined fee category"""
    id: UUID
    type: FeeType
    custom_type: CustomFeeType
    name: str
    description: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "custom-fee-uuid",
                "type": "other",
                "custom_type": {
                    "type": "olympiad_registration",
                    "label": "Science Olympiad Registration",
                    "description": "Fee for national science olympiad participation"
                },
                "name": "Science Olympiad Registration Fee",
                "description": "One-time registration fee for students participating in national science olympiad"
            }
        }

class FeeCategoryReference(BaseModel):
    id: UUID
    name: str
    type: FeeType
    custom_type: Optional[CustomFeeType] = None

# Resolve forward references
FeeCategoryResponse.model_rebuild()