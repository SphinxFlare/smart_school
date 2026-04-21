# academic/api/curriculum/timetable.py

from fastapi import APIRouter, Depends
from typing import List
from uuid import UUID

from academic.api.deps import get_context, get_pagination
from app.deps.roles import require_roles

from academic.services.curriculum.timetable_service import TimetableService
from academic.schemas.timetable import ClassTimetableCreate, ClassTimetableResponse


router = APIRouter(prefix="/academic/timetable", tags=["Timetable"])
service = TimetableService()


# ---------------------------------------------------------
# UPSERT SLOT
# ---------------------------------------------------------
@router.post("/", response_model=ClassTimetableResponse)
def upsert_slot(
    payload: ClassTimetableCreate,
    ctx=Depends(get_context),
    user=Depends(require_roles(["ADMIN", "STAFF"]))
):
    db, _, school_id = ctx

    obj = service.upsert_slot(
        db,
        school_id=school_id,
        class_id=payload.class_id,
        section_id=payload.section_id,
        academic_year_id=payload.academic_year_id,
        day_of_week=payload.day_of_week,
        period_number=payload.period_number,
        subject_id=payload.subject_id,
        teacher_assignment_id=payload.teacher_assignment_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        room=payload.room
    )

    return ClassTimetableResponse.model_validate(obj, from_attributes=True)


# ---------------------------------------------------------
# GET TIMETABLE
# ---------------------------------------------------------
@router.get("/", response_model=List[ClassTimetableResponse])
def get_timetable(
    class_id: UUID,
    section_id: UUID,
    academic_year_id: UUID,
    pagination=Depends(get_pagination),
    ctx=Depends(get_context)
):
    db, _, _ = ctx
    skip, limit = pagination

    data = service.get_timetable(
        db,
        class_id=class_id,
        section_id=section_id,
        academic_year_id=academic_year_id,
        skip=skip,
        limit=limit
    )

    return [ClassTimetableResponse.model_validate(x, from_attributes=True) for x in data]


# ---------------------------------------------------------
# DELETE SLOT
# ---------------------------------------------------------
@router.delete("/slot")
def delete_slot(
    class_id: UUID,
    section_id: UUID,
    day_of_week: int,
    period_number: int,
    academic_year_id: UUID,
    ctx=Depends(get_context),
    user=Depends(require_roles(["ADMIN"]))
):
    db, _, _ = ctx

    service.delete_slot(
        db,
        class_id=class_id,
        section_id=section_id,
        day_of_week=day_of_week,
        period_number=period_number,
        academic_year_id=academic_year_id
    )

    return {"success": True}