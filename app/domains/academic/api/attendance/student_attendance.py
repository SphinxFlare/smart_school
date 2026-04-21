# academic/api/attendance/student_attendance.py

from fastapi import APIRouter, Depends
from typing import List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from academic.api.deps import get_context, get_pagination
from app.deps.roles import require_roles

from academic.services.attendance.student_attendance_service import StudentAttendanceService


router = APIRouter(prefix="/academic/student-attendance", tags=["Student Attendance"])
service = StudentAttendanceService()


# ---------------------------------------------------------
# Schemas
# ---------------------------------------------------------
class MarkAttendance(BaseModel):
    student_id: UUID
    section_id: UUID
    academic_year_id: UUID
    status: str
    date: datetime
    reason: str | None = None


class AttendanceResponse(BaseModel):
    id: UUID
    student_id: UUID
    section_id: UUID
    academic_year_id: UUID
    status: str
    date: datetime
    reason: str | None = None


# ---------------------------------------------------------
# MARK ATTENDANCE
# ---------------------------------------------------------
@router.post("/", response_model=AttendanceResponse)
def mark_attendance(
    payload: MarkAttendance,
    ctx=Depends(get_context),
    user=Depends(require_roles(["STAFF", "ADMIN"]))
):
    db, current_user, school_id = ctx

    obj = service.mark_attendance(
        db,
        school_id=school_id,
        student_id=payload.student_id,
        section_id=payload.section_id,
        academic_year_id=payload.academic_year_id,
        status=payload.status,
        date=payload.date,
        marked_by_id=current_user.id,
        reason=payload.reason
    )

    return AttendanceResponse.model_validate(obj, from_attributes=True)


# ---------------------------------------------------------
# GET BY STUDENT + DATE
# ---------------------------------------------------------
@router.get("/student-date", response_model=AttendanceResponse | None)
def get_by_student_date(
    student_id: UUID,
    date: datetime,
    ctx=Depends(get_context)
):
    db, _, _ = ctx

    obj = service.get_by_student_date(db, student_id=student_id, date=date)
    if not obj:
        return None

    return AttendanceResponse.model_validate(obj, from_attributes=True)


# ---------------------------------------------------------
# LIST BY SECTION (DAILY)
# ---------------------------------------------------------
@router.get("/section", response_model=List[AttendanceResponse])
def list_by_section(
    section_id: UUID,
    date: datetime,
    ctx=Depends(get_context)
):
    db, _, _ = ctx

    data = service.list_by_section(db, section_id=section_id, date=date)
    return [AttendanceResponse.model_validate(x, from_attributes=True) for x in data]


# ---------------------------------------------------------
# LIST BY STUDENT
# ---------------------------------------------------------
@router.get("/student", response_model=List[AttendanceResponse])
def list_by_student(
    student_id: UUID,
    pagination=Depends(get_pagination),
    ctx=Depends(get_context)
):
    db, _, _ = ctx
    skip, limit = pagination

    data = service.list_by_student(db, student_id=student_id, skip=skip, limit=limit)
    return [AttendanceResponse.model_validate(x, from_attributes=True) for x in data]