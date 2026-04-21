# academic/api/curriculum/assignment.py

from fastapi import APIRouter, Depends, Query
from typing import List
from uuid import UUID
from pydantic import BaseModel

from academic.api.deps import get_context, get_pagination
from app.deps.roles import require_roles

from academic.services.curriculum.teacher_assignment_service import TeacherAssignmentService


router = APIRouter(prefix="/academic/assignments", tags=["Teacher Assignments"])
service = TeacherAssignmentService()


class AssignmentCreate(BaseModel):
    staff_member_id: UUID
    class_id: UUID
    section_id: UUID
    subject_id: UUID
    academic_year_id: UUID
    is_primary: bool = True


class AssignmentResponse(BaseModel):
    id: UUID
    staff_member_id: UUID
    class_id: UUID
    section_id: UUID
    subject_id: UUID
    academic_year_id: UUID
    is_primary: bool


# ---------------------------------------------------------
# CREATE
# ---------------------------------------------------------
@router.post("/", response_model=AssignmentResponse)
def create_assignment(
    payload: AssignmentCreate,
    ctx=Depends(get_context),
    user=Depends(require_roles(["ADMIN"]))
):
    db, _, school_id = ctx

    obj = service.create_assignment(
        db,
        school_id=school_id,
        staff_member_id=payload.staff_member_id,
        class_id=payload.class_id,
        section_id=payload.section_id,
        subject_id=payload.subject_id,
        academic_year_id=payload.academic_year_id,
        is_primary=payload.is_primary
    )

    return AssignmentResponse.model_validate(obj, from_attributes=True)


# ---------------------------------------------------------
# LIST BY STAFF
# ---------------------------------------------------------
@router.get("/staff/{staff_id}", response_model=List[AssignmentResponse])
def list_by_staff(
    staff_id: UUID,
    academic_year_id: UUID,
    pagination=Depends(get_pagination),
    ctx=Depends(get_context)
):
    db, _, _ = ctx
    skip, limit = pagination

    data = service.list_by_staff(
        db,
        staff_member_id=staff_id,
        academic_year_id=academic_year_id,
        skip=skip,
        limit=limit
    )

    return [AssignmentResponse.model_validate(x, from_attributes=True) for x in data]


# ---------------------------------------------------------
# LIST BY CLASS+SECTION
# ---------------------------------------------------------
@router.get("/class-section", response_model=List[AssignmentResponse])
def list_by_class_section(
    class_id: UUID,
    section_id: UUID,
    academic_year_id: UUID,
    pagination=Depends(get_pagination),
    ctx=Depends(get_context)
):
    db, _, _ = ctx
    skip, limit = pagination

    data = service.list_by_class_section(
        db,
        class_id=class_id,
        section_id=section_id,
        academic_year_id=academic_year_id,
        skip=skip,
        limit=limit
    )

    return [AssignmentResponse.model_validate(x, from_attributes=True) for x in data]


# ---------------------------------------------------------
# DELETE
# ---------------------------------------------------------
@router.delete("/{assignment_id}")
def delete_assignment(
    assignment_id: UUID,
    ctx=Depends(get_context),
    user=Depends(require_roles(["ADMIN"]))
):
    db, _, _ = ctx

    service.delete_assignment(db, assignment_id=assignment_id)
    return {"success": True}