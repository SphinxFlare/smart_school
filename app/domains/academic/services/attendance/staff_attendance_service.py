# academic/services/attendance/staff_attendance_service.py

from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from academic.models.attendance import StaffAttendance, StaffPunchLog
from academic.repositories.attendance.staff_attendance_repository import StaffAttendanceRepository
from academic.repositories.attendance.punch_log_repository import StaffPunchLogRepository
from academic.services.common.validator_service import ValidationError


class StaffAttendanceService:

    def __init__(self):
        self.att_repo = StaffAttendanceRepository()
        self.punch_repo = StaffPunchLogRepository

    # ---------------------------------------------------------
    # PUNCH LOG
    # ---------------------------------------------------------
    def log_punch(
        self,
        db: Session,
        *,
        staff_member_id: UUID,
        punch_type,
        punch_time,
        latitude=None,
        longitude=None,
        device_id=None,
        ip_address=None
    ):
        with db.begin():
            obj = StaffPunchLog(
                staff_member_id=staff_member_id,
                punch_type=punch_type,
                punch_time=punch_time,
                latitude=latitude,
                longitude=longitude,
                device_id=device_id,
                ip_address=ip_address,
            )
            return self.punch_repo.create(db, obj)

    # ---------------------------------------------------------
    # DAILY ATTENDANCE (DERIVED)
    # ---------------------------------------------------------
    def upsert_attendance(
        self,
        db: Session,
        *,
        staff_member_id: UUID,
        date: datetime,
        status,
        check_in=None,
        check_out=None,
        working_hours=None
    ):
        with db.begin():
            attendance = self.att_repo.get_by_staff_and_date(db, staff_member_id, date)

            if attendance:
                if attendance.is_locked:
                    raise ValidationError("Attendance is locked")

                attendance.check_in = check_in
                attendance.check_out = check_out
                attendance.working_hours = working_hours
                attendance.status = status
                return attendance

            obj = StaffAttendance(
                staff_member_id=staff_member_id,
                date=date,
                check_in=check_in,
                check_out=check_out,
                working_hours=working_hours,
                status=status,
            )
            return self.att_repo.create(db, obj)

    # ---------------------------------------------------------
    # GET
    # ---------------------------------------------------------
    def get_by_staff_date(self, db: Session, *, staff_member_id: UUID, date: datetime):
        return self.att_repo.get_by_staff_and_date(db, staff_member_id, date)

    def list_by_staff(self, db: Session, *, staff_member_id: UUID, skip=0, limit=100):
        return self.att_repo.list_by_staff(db, staff_member_id, skip, limit)

    # ---------------------------------------------------------
    # LOCK DAY
    # ---------------------------------------------------------
    def lock_attendance(self, db: Session, *, staff_member_id: UUID, date: datetime):
        with db.begin():
            attendance = self.att_repo.get_by_staff_and_date(db, staff_member_id, date)
            if not attendance:
                raise ValidationError("Attendance not found")

            attendance.is_locked = True
            return attendance