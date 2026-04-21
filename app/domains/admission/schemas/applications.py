# app/domains/admission/schemas/applications.py


from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict

from types.admissions import ApplicationStatus


# =====================================================
# Base
# =====================================================

class ApplicationBase(BaseModel):
    """
    Common fields shared across application schemas.
    """

    first_name: str = Field(..., description="Student first name")
    last_name: str = Field(..., description="Student last name")
    date_of_birth: datetime = Field(..., description="Date of birth")
    gender: str = Field(..., description="Gender")
    nationality: Optional[str] = None

    applying_class_id: UUID

    previous_school_name: Optional[str] = None
    previous_school_last_class: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# =====================================================
# Create
# =====================================================

class ApplicationCreate(ApplicationBase):
    """
    Request schema for creating application.
    """

    school_id: UUID
    academic_year_id: UUID

    student_id: Optional[UUID] = None


# =====================================================
# Update
# =====================================================

class ApplicationUpdate(BaseModel):
    """
    Request schema for updating application.
    All fields optional.
    """

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None

    applying_class_id: Optional[UUID] = None

    previous_school_name: Optional[str] = None
    previous_school_last_class: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# =====================================================
# Read (full)
# =====================================================

class ApplicationRead(ApplicationBase):
    """
    Full application response schema.
    """

    id: UUID

    school_id: UUID
    academic_year_id: UUID
    student_id: Optional[UUID] = None

    status: ApplicationStatus

    submitted_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =====================================================
# List item
# =====================================================

class ApplicationListItem(BaseModel):
    """
    Lightweight schema for list endpoints.
    """

    id: UUID

    first_name: str
    last_name: str

    status: ApplicationStatus

    applying_class_id: UUID

    submitted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =====================================================
# Status counts
# =====================================================

class ApplicationStatusCounts(BaseModel):
    """
    Dashboard counts.

    Repository returns:
        dict[ApplicationStatus, int]
    """

    counts: Dict[ApplicationStatus, int]

    model_config = ConfigDict(from_attributes=True)


# =====================================================
# Submit request
# =====================================================

class ApplicationSubmitRequest(BaseModel):
    """
    Empty body schema for submit endpoint.
    Keeps API consistent.
    """

    model_config = ConfigDict(from_attributes=True)