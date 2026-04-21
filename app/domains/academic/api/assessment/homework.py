# academic/api/assessment/homework.py

from fastapi import APIRouter, Depends
from uuid import UUID
from typing import List

from academic.api.deps import get_context, get_pagination
from app.deps.roles import require_roles

from academic.services.assessment.homework_service import HomeworkService
from academic.schemas.homework import HomeworkCreate, HomeworkResponse


router = APIRouter(prefix="/academic/homework", tags=["Homework"])
service = HomeworkService()


@router.post("/", response_model=HomeworkResponse)
def create_homework(
    payload: HomeworkCreate,
    ctx=Depends(get_context),
    user=Depends(require_roles(["STAFF"]))
):
    db, _, school_id = ctx

    obj = service.create_homework(
        db,
        school_id=school_id,
        teacher_assignment_id=payload.teacher_assignment_id,
        title=payload.title,
        due_date=payload.due_date
    )

    return HomeworkResponse.model_validate(obj, from_attributes=True)