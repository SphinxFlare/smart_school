# academic/services/attendance/student_attendance_service.py

from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from academic.models.attendance import StudentAttendance
from academic.repositories.attendance.student_attendance_repository import StudentAttendanceRepository
from academic.services.common.validator_service import ValidatorService, ValidationError
from academic.services.common.ownership_service import OwnershipService


class StudentAttendanceService:

    def __init__(self):
        self.repo = StudentAttendanceRepository()
        self.validator = ValidatorService()
        self.ownership = OwnershipService()

    # ---------------------------------------------------------
    # MARK ATTENDANCE
    # ---------------------------------------------------------
    def mark_attendance(
        self,
        db: Session,
        *,
        school_id: UUID,
        student_id: UUID,
        section_id: UUID,
        academic_year_id: UUID,
        status,
        date: datetime,
        marked_by_id: UUID,
        reason: str | None = None
    ):
        # validate ownership
        self.ownership.validate_section(db, section_id, school_id)

        # prevent duplicate (student_id + date)
        existing = self.repo.get_by_student_and_date(db, student_id, date)
        if existing:
            raise ValidationError("Attendance already marked for this date")

        with db.begin():
            obj = StudentAttendance(
                student_id=student_id,
                section_id=section_id,
                academic_year_id=academic_year_id,
                status=status,
                date=date,
                marked_by_id=marked_by_id,
                reason=reason,
            )
            return self.repo.create(db, obj)

    # ---------------------------------------------------------
    # GET
    # ---------------------------------------------------------
    def get_by_student_date(self, db: Session, *, student_id: UUID, date: datetime):
        return self.repo.get_by_student_and_date(db, student_id, date)

    def list_by_section(self, db: Session, *, section_id: UUID, date: datetime):
        return self.repo.list_by_section_and_date(db, section_id, date)

    def list_by_student(self, db: Session, *, student_id: UUID, skip=0, limit=100):
        return self.repo.list_by_student(db, student_id, skip, limit)