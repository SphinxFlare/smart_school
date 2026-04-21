# academic/api/assessment/marks.py

from fastapi import APIRouter, Depends
from uuid import UUID
from pydantic import BaseModel

from academic.api.deps import get_context
from app.deps.roles import require_roles

from academic.services.assessment.mark_service import MarkService


router = APIRouter(prefix="/academic/marks", tags=["Marks"])
service = MarkService()


class MarkAssign(BaseModel):
    student_id: UUID
    schedule_id: UUID
    marks: float


@router.post("/")
def assign_mark(
    payload: MarkAssign,
    ctx=Depends(get_context),
    user=Depends(require_roles(["STAFF"]))
):
    db, _, school_id = ctx

    obj = service.assign_mark(
        db,
        school_id=school_id,
        student_id=payload.student_id,
        schedule_id=payload.schedule_id,
        marks=payload.marks
    )

    return {"id": obj.id, "marks": obj.marks_obtained}