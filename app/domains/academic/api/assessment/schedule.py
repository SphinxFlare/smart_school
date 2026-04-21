# academic/api/assessment/schedule.py

from fastapi import APIRouter, Depends
from uuid import UUID
from typing import List

from academic.api.deps import get_context
from app.deps.roles import require_roles

from academic.services.assessment.schedule_service import ScheduleService
from academic.schemas.exam import ExamScheduleCreate, ExamScheduleResponse


router = APIRouter(prefix="/academic/exam-schedules", tags=["Exam Schedule"])
service = ScheduleService()


@router.post("/", response_model=ExamScheduleResponse)
def create_schedule(
    payload: ExamScheduleCreate,
    ctx=Depends(get_context),
    user=Depends(require_roles(["ADMIN"]))
):
    db, _, school_id = ctx

    obj = service.create_schedule(
        db,
        school_id=school_id,
        exam_id=payload.exam_id,
        class_id=payload.class_id,
        subject_id=payload.subject_id,
        exam_date=payload.date
    )

    return ExamScheduleResponse.model_validate(obj, from_attributes=True)