# academic/api/assessment/result.py

from fastapi import APIRouter, Depends
from uuid import UUID
from pydantic import BaseModel

from academic.api.deps import get_context
from app.deps.roles import require_roles

from academic.services.assessment.result_service import ResultService


router = APIRouter(prefix="/academic/results", tags=["Results"])
service = ResultService()


class ResultCreate(BaseModel):
    student_id: UUID
    exam_id: UUID
    total_marks: float
    percentage: float


@router.post("/")
def create_result(
    payload: ResultCreate,
    ctx=Depends(get_context),
    user=Depends(require_roles(["ADMIN"]))
):
    db, _, _ = ctx

    obj = service.create_result(
        db,
        student_id=payload.student_id,
        exam_id=payload.exam_id,
        total_marks=payload.total_marks,
        percentage=payload.percentage
    )

    return {"id": obj.id, "percentage": obj.percentage}