# identity/schemas/base.py

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class DomainBase(BaseModel):
    """Base schema configuration for all domain schemas"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        arbitrary_types_allowed=True
    )

class TimestampSchema(DomainBase):
    """Standard timestamp fields"""
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

class AuditSchema(DomainBase):
    """Standard audit fields"""
    created_by_id: UUID
    updated_by_id: Optional[UUID] = None