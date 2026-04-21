# academic/api/infrastructure/section.py

from fastapi import APIRouter, Depends
from typing import List
from uuid import UUID
from pydantic import BaseModel

from academic.api.deps import get_context, get_pagination
from app.deps.roles import require_roles

from academic.services.infrastructure.section_service import SectionService


router = APIRouter(prefix="/academic/sections", tags=["Sections"])
service = SectionService()


class SectionCreate(BaseModel):
    class_id: UUID
    name: str
    capacity: int | None = None


class SectionResponse(BaseModel):
    id: UUID
    class_id: UUID
    name: str
    capacity: int | None = None


@router.post("/", response_model=SectionResponse)
def create_section(payload: SectionCreate, ctx=Depends(get_context), user=Depends(require_roles(["ADMIN"]))):
    db, _, school_id = ctx

    obj = service.create_section(
        db,
        school_id=school_id,
        class_id=payload.class_id,
        name=payload.name,
        capacity=payload.capacity
    )

    return SectionResponse.model_validate(obj, from_attributes=True)


@router.get("/by-class/{class_id}", response_model=List[SectionResponse])
def list_sections(class_id: UUID, pagination=Depends(get_pagination), ctx=Depends(get_context)):
    db, _, school_id = ctx
    skip, limit = pagination

    data = service.list_by_class(db, school_id=school_id, class_id=class_id, skip=skip, limit=limit)
    return [SectionResponse.model_validate(x, from_attributes=True) for x in data]