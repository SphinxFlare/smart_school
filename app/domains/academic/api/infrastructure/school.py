# academic/api/infrastructure/school.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

from academic.api.deps import get_context
from app.deps.roles import require_roles

from academic.services.infrastructure.school_service import SchoolService


router = APIRouter(prefix="/academic/schools", tags=["Schools"])
service = SchoolService()


class SchoolResponse(BaseModel):
    id: str
    name: str
    code: str
    is_active: bool


@router.get("/me", response_model=SchoolResponse)
def get_my_school(ctx=Depends(get_context)):
    db, _, school_id = ctx

    school = service.get_by_id(db, school_id=school_id)
    return SchoolResponse.model_validate(school, from_attributes=True)


@router.get("/active", response_model=List[SchoolResponse])
def list_active(ctx=Depends(get_context)):
    db, _, _ = ctx
    data = service.list_active(db)
    return [SchoolResponse.model_validate(x, from_attributes=True) for x in data]