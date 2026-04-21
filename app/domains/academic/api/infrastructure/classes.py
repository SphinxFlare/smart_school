# academic/api/infrastructure/class.py

from fastapi import APIRouter, Depends, Query
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from pydantic import BaseModel

from academic.api.deps import get_context, get_pagination
from app.deps.roles import require_roles

from academic.services.infrastructure.class_service import ClassService


router = APIRouter(prefix="/academic/classes", tags=["Classes"])
service = ClassService()


class ClassCreate(BaseModel):
    name: str
    level: int
    academic_year_id: UUID


class ClassResponse(BaseModel):
    id: UUID
    school_id: UUID
    name: str
    level: int
    academic_year_id: UUID


@router.post("/", response_model=ClassResponse)
def create_class(payload: ClassCreate, ctx=Depends(get_context), user=Depends(require_roles(["ADMIN"]))):
    db, _, school_id = ctx

    obj = service.create_class(
        db,
        school_id=school_id,
        name=payload.name,
        level=payload.level,
        academic_year_id=payload.academic_year_id
    )

    return ClassResponse.model_validate(obj, from_attributes=True)


@router.get("/", response_model=List[ClassResponse])
def list_classes(pagination=Depends(get_pagination), ctx=Depends(get_context)):
    db, _, school_id = ctx
    skip, limit = pagination

    data = service.list_by_school(db, school_id=school_id, skip=skip, limit=limit)
    return [ClassResponse.model_validate(x, from_attributes=True) for x in data]