# acadamic/models/attendance.py


from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, Boolean, Numeric, Enum as SQLEnum, Text, UniqueConstraint, Float, CheckConstraint, Index, Date
from datetime import datetime
import uuid
from types.types import AttendanceStatus, PunchType, StaffAttendanceStatus
from db.base import Base 


class StudentAttendance(Base):
    __tablename__ = "student_attendance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)  # Cross-domain
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    status = Column(SQLEnum(AttendanceStatus), nullable=False)
    reason = Column(Text)  # Optional absence reason
    marked_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # Teacher marking
    marked_at = Column(DateTime, default=datetime.utcnow)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        UniqueConstraint('student_id', 'date', name='uq_student_attendance_date'),
        Index("ix_student_attendance_student_date", "student_id", "date")
    )

# ==========================================================
# STAFF PUNCH LOG (RAW EVENTS - FUTURE PROOF)
# ==========================================================

class StaffPunchLog(Base):
    __tablename__ = "staff_punch_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    staff_member_id = Column(UUID(as_uuid=True), ForeignKey("staff_members.id"), nullable=False)

    punch_type = Column(SQLEnum(PunchType), nullable=False)  
    # CHECK_IN / CHECK_OUT

    punch_time = Column(Date, nullable=False)

    # Security Fields
    latitude = Column(Numeric(9, 6))
    longitude = Column(Numeric(9, 6))
    device_id = Column(String)
    ip_address = Column(String)

    # Validation
    is_valid = Column(Boolean, default=True)
    validation_reason = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_staff_punch_staff", "staff_member_id"),
        Index("ix_staff_punch_time", "punch_time"),
    )


# ==========================================================
# STAFF DAILY ATTENDANCE (DERIVED SUMMARY)
# ==========================================================

class StaffAttendance(Base):
    __tablename__ = "staff_attendance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    staff_member_id = Column(UUID(as_uuid=True), ForeignKey("staff_members.id"), nullable=False)

    date = Column(DateTime, nullable=False)

    check_in = Column(DateTime)
    check_out = Column(DateTime)

    working_hours = Column(Numeric(4, 2))  # Example: 8.50 hours

    status = Column(SQLEnum(StaffAttendanceStatus), nullable=False)

    is_locked = Column(Boolean, default=False)  # Prevent edits after closing day

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("staff_member_id", "date", name="uq_staff_attendance_date"),
        CheckConstraint(
            "check_out IS NULL OR check_out >= check_in",
            name="ck_checkout_after_checkin",
        ),
        Index("ix_staff_attendance_staff", "staff_member_id"),
        Index("ix_staff_attendance_staff_date", "staff_member_id", "date")
    )
