# identity/schemas/driver.py


from pydantic import Field
from typing import Optional
from uuid import UUID
from datetime import datetime

from .base import DomainBase, TimestampSchema
from types.transport import DriverStatus


# ---------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------

class DriverBase(DomainBase):
    license_number: str = Field(..., max_length=50)
    license_type: str = Field(..., max_length=50)
    license_expiry: datetime
    status: DriverStatus


# ---------------------------------------------------------------------
# Create / Update
# ---------------------------------------------------------------------

class DriverCreate(DriverBase):
    staff_member_id: UUID


class DriverUpdate(DomainBase):
    license_type: Optional[str] = None
    license_expiry: Optional[datetime] = None
    status: Optional[DriverStatus] = None


# ---------------------------------------------------------------------
# Response (LEAN)
# ---------------------------------------------------------------------

class DriverResponse(DriverBase, TimestampSchema):
    id: UUID
    staff_member_id: UUID


# ---------------------------------------------------------------------
# Reference (optional, for future use)
# ---------------------------------------------------------------------

class DriverReference(DomainBase):
    id: UUID
    license_number: str
    status: DriverStatus