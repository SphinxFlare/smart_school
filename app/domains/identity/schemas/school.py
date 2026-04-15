# domains/identity/schemas/school.py


from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from .base import DomainBase, TimestampSchema
import re

class SchoolBase(DomainBase):
    name: str = Field(..., min_length=3, max_length=200)
    code: str = Field(
        ...,
        min_length=3,
        max_length=20,
        pattern=r"^[A-Z0-9]{3,20}$",
        description="Unique school identifier (e.g., SCH001, DELHI_CAMPUS)"
    )
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field("India", max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    contact_email: EmailStr
    contact_phone: str = Field(..., min_length=10, max_length=20)
    website: Optional[str] = Field(None, max_length=200)
    timezone: Optional[str] = Field("Asia/Kolkata", max_length=50)

    @validator('contact_phone')
    def validate_phone(cls, v):
        # Remove spaces and validate format
        cleaned = re.sub(r'\s+', '', v)
        if not re.match(r'^\+?[0-9]{10,15}$', cleaned):
            raise ValueError('Invalid phone number format')
        return cleaned

class SchoolCreate(SchoolBase):
    pass

class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None

class SchoolStats(BaseModel):
    """Aggregated statistics for school dashboard"""
    total_students: int = 0
    total_staff: int = 0
    total_classes: int = 0
    active_academic_year: Optional[str] = None
    attendance_rate: Optional[float] = Field(None, ge=0, le=100)
    fee_collection_rate: Optional[float] = Field(None, ge=0, le=100)

class SchoolResponse(SchoolBase, TimestampSchema):
    id: UUID
    is_active: bool
    is_deleted: bool
    stats: Optional[SchoolStats] = None
    principal_name: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "f6a7b8c9-d0e1-2345-f678-901234567890",
                "name": "Delhi Public School - Rohini Campus",
                "code": "DPS_ROHINI",
                "address": "Sector 10, Rohini, New Delhi",
                "city": "New Delhi",
                "state": "Delhi",
                "country": "India",
                "postal_code": "110085",
                "contact_email": "principal.rohini@dps.edu.in",
                "contact_phone": "+91 11 27563412",
                "website": "https://dpsrohini.edu.in",
                "timezone": "Asia/Kolkata",
                "is_active": True,
                "created_at": "2020-04-15T00:00:00Z",
                "updated_at": "2026-01-20T11:45:30Z",
                "is_deleted": False,
                "stats": {
                    "total_students": 2450,
                    "total_staff": 185,
                    "total_classes": 65,
                    "active_academic_year": "2025-2026",
                    "attendance_rate": 96.8,
                    "fee_collection_rate": 92.5
                },
                "principal_name": "Dr. Sunita Menon"
            }
        }

class SchoolReference(BaseModel):
    id: UUID
    name: str
    code: str
    city: Optional[str] = None
    contact_email: EmailStr

class SchoolSettings(BaseModel):
    """School-specific configuration settings"""
    academic_year_start_month: int = Field(4, ge=1, le=12, description="April = 4")
    academic_year_end_month: int = Field(3, ge=1, le=12, description="March = 3")
    working_days_per_week: int = Field(6, ge=5, le=7)
    school_start_time: str = Field("08:00", pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    school_end_time: str = Field("15:30", pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    attendance_threshold_percent: float = Field(75.0, ge=50, le=100)
    fee_due_reminder_days: int = Field(3, ge=1, le=30)
    updated_at: datetime