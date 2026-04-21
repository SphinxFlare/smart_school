# academic/api/infrastructure/academic_year.py

from fastapi import APIRouter, Depends, Query
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session

from academic.api.deps import get_context, get_pagination
from app.deps.roles import require_roles

from academic.services.infrastructure.academic_year_service import AcademicYearService
from academic.schemas.base import DomainBase
from pydantic import BaseModel
from datetime import datetime


router = APIRouter(prefix="/academic/academic-years", tags=["Academic Years"])
service = AcademicYearService()


# -------------------------
# Schemas (local minimal)
# -------------------------
class AcademicYearCreate(BaseModel):
    name: str
    start_date: datetime
    end_date: datetime
    is_current: bool = False


class AcademicYearResponse(BaseModel):
    id: UUID
    school_id: UUID
    name: str
    start_date: datetime
    end_date: datetime
    is_current: bool


# -------------------------
# CREATE
# -------------------------
@router.post("/", response_model=AcademicYearResponse)
def create_academic_year(
    payload: AcademicYearCreate,
    ctx=Depends(get_context),
    user=Depends(require_roles(["ADMIN"]))
):
    db, current_user, school_id = ctx

    obj = service.create_academic_year(
        db,
        school_id=school_id,
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        is_current=payload.is_current
    )

    return AcademicYearResponse.model_validate(obj, from_attributes=True)


# -------------------------
# LIST
# -------------------------
@router.get("/", response_model=List[AcademicYearResponse])
def list_academic_years(
    pagination=Depends(get_pagination),
    ctx=Depends(get_context)
):
    db, _, school_id = ctx
    skip, limit = pagination

    data = service.list_academic_years(db, school_id=school_id, skip=skip, limit=limit)
    return [AcademicYearResponse.model_validate(x, from_attributes=True) for x in data]


# -------------------------
# SET CURRENT
# -------------------------
@router.patch("/{academic_year_id}/set-current")
def set_current(
    academic_year_id: UUID,
    ctx=Depends(get_context),
    user=Depends(require_roles(["ADMIN"]))
):
    db, _, school_id = ctx

    obj = service.set_current_year(db, school_id=school_id, academic_year_id=academic_year_id)
    return AcademicYearResponse.model_validate(obj, from_attributes=True)