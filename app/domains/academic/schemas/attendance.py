# academic/schemas/attendance.py


from pydantic import BaseModel, Field, validator
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import date, datetime
from .base import DomainBase, TimestampSchema
from types.types import AttendanceStatus

if TYPE_CHECKING:
    from app.domains.identity.schemas.student import StudentReference
    from app.domains.identity.schemas.user import UserReference
else:
    StudentReference = "StudentReference"
    UserReference = "UserReference"

class AttendanceBase(DomainBase):
    """
    Base schema for attendance records
    """
    status: AttendanceStatus = Field(..., description="Attendance status: present, absent, late, excused")
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for absence/lateness (optional for present)"
    )
    is_excused: bool = Field(default=False, description="Whether absence is excused")
    excused_by_id: Optional[UUID] = None
    excused_at: Optional[datetime] = None

    @validator('reason')
    def validate_reason_required(cls, v, values):
        if values.get('status') in [AttendanceStatus.ABSENT, AttendanceStatus.LATE] and not v:
            # Reason is optional but recommended for absent/late
            pass
        return v

class StudentAttendanceCreate(AttendanceBase):
    """
    Schema for creating student attendance record
    """
    student_id: UUID
    date: datetime = Field(..., description="Date of attendance")
    marked_by_id: UUID = Field(..., description="Teacher who marked attendance")
    academic_year_id: UUID
    class_id: UUID
    section_id: UUID

    @validator('date')
    def validate_date_not_future(cls, v):
        if v > date.today():
            raise ValueError('Attendance date cannot be in the future')
        return v

class StudentAttendanceUpdate(BaseModel):
    """
    Schema for updating student attendance
    """
    status: Optional[AttendanceStatus] = None
    reason: Optional[str] = Field(None, max_length=500)
    is_excused: Optional[bool] = None
    excused_by_id: Optional[UUID] = None

    @validator('reason')
    def validate_reason_on_update(cls, v, values):
        if values.get('status') in [AttendanceStatus.ABSENT, AttendanceStatus.LATE] and not v:
            # Allow updating without reason if already exists
            pass
        return v

class AttendanceSummary(BaseModel):
    """
    Summary statistics for attendance
    """
    total_days: int = 0
    present_days: int = 0
    absent_days: int = 0
    late_days: int = 0
    excused_days: int = 0
    attendance_percentage: float = Field(default=0.0, ge=0, le=100)
    current_streak: int = 0  # Consecutive present days

    @validator('attendance_percentage', always=True)
    def calculate_percentage(cls, v, values):
        total = values.get('total_days', 0)
        present = values.get('present_days', 0)
        if total > 0:
            return round((present / total) * 100, 2)
        return 0.0

class StudentAttendanceResponse(AttendanceBase, TimestampSchema):
    """
    Response schema for student attendance with relationships
    """
    id: UUID
    student_id: UUID
    date: date
    marked_by_id: UUID
    marked_at: datetime
    academic_year_id: UUID
    class_id: UUID
    section_id: UUID
    is_deleted: bool
    student: StudentReference
    marked_by: UserReference
    excused_by: Optional[UserReference] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "student_id": "student-uuid",
                "date": "2026-02-17",
                "status": "present",
                "reason": None,
                "is_excused": False,
                "excused_by_id": None,
                "excused_at": None,
                "marked_by_id": "teacher-uuid",
                "marked_at": "2026-02-17T08:30:00Z",
                "academic_year_id": "academic-year-uuid",
                "class_id": "class-uuid",
                "section_id": "section-uuid",
                "created_at": "2026-02-17T08:30:00Z",
                "is_deleted": False,
                "student": {
                    "id": "student-uuid",
                    "admission_number": "STU2026045",
                    "full_name": "Jamie Smith",
                    "class_name": "Grade 10",
                    "section_name": "A"
                },
                "marked_by": {
                    "id": "teacher-uuid",
                    "full_name": "Ms. Sarah Chen",
                    "email": "s.chen@school.edu",
                    "role": "teacher"
                },
                "excused_by": None
            }
        }

class AttendanceHistoryResponse(BaseModel):
    """
    Historical attendance records for a student
    """
    student_id: UUID
    student_name: str
    admission_number: str
    attendance_records: List[StudentAttendanceResponse]
    summary: AttendanceSummary
    period_start: date
    period_end: date

class BulkAttendanceCreate(BaseModel):
    """
    Schema for bulk creating attendance for multiple students
    """
    date: date
    academic_year_id: UUID
    class_id: UUID
    section_id: UUID
    marked_by_id: UUID
    attendance_records: List[StudentAttendanceCreate] = Field(..., min_items=1)

    @validator('attendance_records')
    def validate_all_same_date(cls, v, values):
        date_val = values.get('date')
        for record in v:
            if record.date != date_val:
                raise ValueError('All attendance records must have the same date')
        return v

class AttendanceFilter(BaseModel):
    """
    Filter schema for attendance queries
    """
    student_id: Optional[UUID] = None
    class_id: Optional[UUID] = None
    section_id: Optional[UUID] = None
    academic_year_id: Optional[UUID] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    status: Optional[AttendanceStatus] = None
    marked_by_id: Optional[UUID] = None
    include_deleted: bool = False
    page: int = Field(default=1, ge=1)
    size: int = Field(default=50, ge=1, le=100)

    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v and values.get('date_from') and v < values['date_from']:
            raise ValueError('date_to must be after date_from')
        return v

class MonthlyAttendanceReport(BaseModel):
    """
    Monthly attendance report for a student or class
    """
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2000, le=2100)
    class_name: Optional[str] = None
    section_name: Optional[str] = None
    total_students: int = 0
    attendance_summary: AttendanceSummary
    daily_attendance: dict[str, dict] = Field(
        default_factory=dict,
        description="Key: date string, Value: {present: int, absent: int, late: int}"
    )

class AttendanceAlert(BaseModel):
    """
    Attendance alert for students with poor attendance
    """
    student_id: UUID
    student_name: str
    admission_number: str
    class_section: str
    attendance_percentage: float
    consecutive_absences: int
    alert_level: str  # "low", "medium", "high", "critical"
    alert_message: str
    last_attendance_date: Optional[date] = None

class AttendanceExportFormat(BaseModel):
    """
    Supported export formats for attendance reports
    """
    format: str = Field(
        default="csv",
        pattern=r"^(csv|excel|pdf|json)$",
        description="Export format: csv, excel, pdf, json"
    )
    include_student_details: bool = True
    include_teacher_details: bool = False
    include_reasons: bool = True
    date_range: Optional[tuple[date, date]] = None

# Resolve forward references
StudentAttendanceResponse.model_rebuild()
AttendanceHistoryResponse.model_rebuild()
AttendanceAlert.model_rebuild()