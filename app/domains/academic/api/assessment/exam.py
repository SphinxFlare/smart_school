# academic/api/assessment/exam.py

from fastapi import APIRouter, Depends
from typing import List
from uuid import UUID

from academic.api.deps import get_context, get_pagination
from app.deps.roles import require_roles

from academic.services.assessment.exam_service import ExamService
from academic.schemas.exam import ExamCreate, ExamResponse


router = APIRouter(prefix="/academic/exams", tags=["Exams"])
service = ExamService()


@router.post("/", response_model=ExamResponse)
def create_exam(
    payload: ExamCreate,
    ctx=Depends(get_context),
    user=Depends(require_roles(["ADMIN", "STAFF"]))
):
    db, _, school_id = ctx

    obj = service.create_exam(
        db,
        school_id=school_id,
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date
    )

    return ExamResponse.model_validate(obj, from_attributes=True)


@router.get("/", response_model=List[ExamResponse])
def list_exams(
    pagination=Depends(get_pagination),
    ctx=Depends(get_context)
):
    db, _, school_id = ctx
    skip, limit = pagination

    data = service.repo.list_by_school(db, school_id, skip, limit)  # repo allowed for read
    return [ExamResponse.model_validate(x, from_attributes=True) for x in data]