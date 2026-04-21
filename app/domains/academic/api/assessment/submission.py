# academic/api/assessment/submission.py

from fastapi import APIRouter, Depends
from uuid import UUID
from typing import List

from academic.api.deps import get_context
from app.deps.roles import require_roles

from academic.services.assessment.submission_service import SubmissionService
from academic.schemas.homework import HomeworkSubmissionCreate, HomeworkSubmissionResponse


router = APIRouter(prefix="/academic/submissions", tags=["Submissions"])
service = SubmissionService()


@router.post("/", response_model=HomeworkSubmissionResponse)
def submit_homework(
    payload: HomeworkSubmissionCreate,
    ctx=Depends(get_context),
    user=Depends(require_roles(["STUDENT"]))
):
    db, _, school_id = ctx

    obj = service.submit_homework(
        db,
        school_id=school_id,
        homework_id=payload.homework_id,
        student_id=payload.student_id
    )

    return HomeworkSubmissionResponse.model_validate(obj, from_attributes=True)