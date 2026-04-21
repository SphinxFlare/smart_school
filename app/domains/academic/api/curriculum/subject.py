# academic/api/curriculum/subject.py

from fastapi import APIRouter, Depends, Query
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session

from academic.api.deps import get_context, get_pagination
from app.deps.roles import require_roles

from academic.services.curriculum.subject_service import SubjectService
from academic.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse


router = APIRouter(prefix="/academic/subjects", tags=["Subjects"])
service = SubjectService()


# ---------------------------------------------------------
# CREATE
# ---------------------------------------------------------
@router.post("/", response_model=SubjectResponse)
def create_subject(
    payload: SubjectCreate,
    ctx=Depends(get_context),
    user=Depends(require_roles(["ADMIN", "STAFF"]))
):
    db, _, school_id = ctx

    obj = service.create_subject(
        db,
        school_id=school_id,
        name=payload.name,
        code=payload.code,
        description=payload.description
    )

    return SubjectResponse.model_validate(obj, from_attributes=True)


# ---------------------------------------------------------
# LIST
# ---------------------------------------------------------
@router.get("/", response_model=List[SubjectResponse])
def list_subjects(
    is_active: bool | None = None,
    pagination=Depends(get_pagination),
    ctx=Depends(get_context)
):
    db, _, school_id = ctx
    skip, limit = pagination

    data = service.list_subjects(
        db,
        school_id=school_id,
        is_active=is_active,
        skip=skip,
        limit=limit
    )

    return [SubjectResponse.model_validate(x, from_attributes=True) for x in data]


# ---------------------------------------------------------
# GET
# ---------------------------------------------------------
@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject(subject_id: UUID, ctx=Depends(get_context)):
    db, _, school_id = ctx

    obj = service.get_by_id(db, school_id=school_id, subject_id=subject_id)
    return SubjectResponse.model_validate(obj, from_attributes=True)


# ---------------------------------------------------------
# UPDATE
# ---------------------------------------------------------
@router.put("/{subject_id}", response_model=SubjectResponse)
def update_subject(
    subject_id: UUID,
    payload: SubjectUpdate,
    ctx=Depends(get_context),
    user=Depends(require_roles(["ADMIN"]))
):
    db, _, school_id = ctx

    obj = service.update_subject(
        db,
        school_id=school_id,
        subject_id=subject_id,
        name=payload.name,
        description=payload.description,
        is_active=payload.is_active
    )

    return SubjectResponse.model_validate(obj, from_attributes=True)


# ---------------------------------------------------------
# DELETE
# ---------------------------------------------------------
@router.delete("/{subject_id}")
def delete_subject(subject_id: UUID, ctx=Depends(get_context), user=Depends(require_roles(["ADMIN"]))):
    db, _, school_id = ctx

    service.delete_subject(db, school_id=school_id, subject_id=subject_id)
    return {"success": True}