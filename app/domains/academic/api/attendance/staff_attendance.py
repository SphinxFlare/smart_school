# academic/api/attendance/staff_attendance.py

from fastapi import APIRouter, Depends
from typing import List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from academic.api.deps import get_context, get_pagination
from app.deps.roles import require_roles

from academic.services.attendance.staff_attendance_service import StaffAttendanceService


router = APIRouter(prefix="/academic/staff-attendance", tags=["Staff Attendance"])
service = StaffAttendanceService()


# ---------------------------------------------------------
# Schemas
# ---------------------------------------------------------
class PunchLogCreate(BaseModel):
    staff_member_id: UUID
    punch_type: str
    punch_time: datetime
    latitude: float | None = None
    longitude: float | None = None
    device_id: str | None = None
    ip_address: str | None = None


class StaffAttendanceUpsert(BaseModel):
    staff_member_id: UUID
    date: datetime
    status: str
    check_in: datetime | None = None
    check_out: datetime | None = None
    working_hours: float | None = None


class StaffAttendanceResponse(BaseModel):
    id: UUID
    staff_member_id: UUID
    date: datetime
    status: str
    check_in: datetime | None = None
    check_out: datetime | None = None
    working_hours: float | None = None
    is_locked: bool


# ---------------------------------------------------------
# PUNCH LOG
# ---------------------------------------------------------
@router.post("/punch")
def log_punch(
    payload: PunchLogCreate,
    ctx=Depends(get_context),
    user=Depends(require_roles(["STAFF", "ADMIN"]))
):
    db, _, _ = ctx

    obj = service.log_punch(
        db,
        staff_member_id=payload.staff_member_id,
        punch_type=payload.punch_type,
        punch_time=payload.punch_time,
        latitude=payload.latitude,
        longitude=payload.longitude,
        device_id=payload.device_id,
        ip_address=payload.ip_address
    )

    return {"id": obj.id}


# ---------------------------------------------------------
# UPSERT DAILY ATTENDANCE
# ---------------------------------------------------------
@router.post("/", response_model=StaffAttendanceResponse)
def upsert_attendance(
    payload: StaffAttendanceUpsert,
    ctx=Depends(get_context),
    user=Depends(require_roles(["ADMIN"]))
):
    db, _, _ = ctx

    obj = service.upsert_attendance(
        db,
        staff_member_id=payload.staff_member_id,
        date=payload.date,
        status=payload.status,
        check_in=payload.check_in,
        check_out=payload.check_out,
        working_hours=payload.working_hours
    )

    return StaffAttendanceResponse.model_validate(obj, from_attributes=True)


# ---------------------------------------------------------
# GET BY STAFF + DATE
# ---------------------------------------------------------
@router.get("/staff-date", response_model=StaffAttendanceResponse | None)
def get_by_staff_date(
    staff_member_id: UUID,
    date: datetime,
    ctx=Depends(get_context)
):
    db, _, _ = ctx

    obj = service.get_by_staff_date(db, staff_member_id=staff_member_id, date=date)
    if not obj:
        return None

    return StaffAttendanceResponse.model_validate(obj, from_attributes=True)


# ---------------------------------------------------------
# LIST BY STAFF
# ---------------------------------------------------------
@router.get("/staff", response_model=List[StaffAttendanceResponse])
def list_by_staff(
    staff_member_id: UUID,
    pagination=Depends(get_pagination),
    ctx=Depends(get_context)
):
    db, _, _ = ctx
    skip, limit = pagination

    data = service.list_by_staff(db, staff_member_id=staff_member_id, skip=skip, limit=limit)
    return [StaffAttendanceResponse.model_validate(x, from_attributes=True) for x in data]


# ---------------------------------------------------------
# LOCK ATTENDANCE
# ---------------------------------------------------------
@router.post("/lock")
def lock_attendance(
    staff_member_id: UUID,
    date: datetime,
    ctx=Depends(get_context),
    user=Depends(require_roles(["ADMIN"]))
):
    db, _, _ = ctx

    obj = service.lock_attendance(db, staff_member_id=staff_member_id, date=date)
    return {"id": obj.id, "locked": obj.is_locked}