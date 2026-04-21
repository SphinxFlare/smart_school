# identity/api/profiles/parent_router.py


from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps.common import get_db
from app.deps.roles import require_roles
from app.deps.auth import get_current_user

from domains.identity.schemas.parent import (
    ParentCreate,
    ParentResponse,
)

from domains.identity.services.profiles.parent_service import ParentService


router = APIRouter(prefix="/parents", tags=["Parents"])


# ---------------------------------------------------------------------
# Create Parent Profile
# ---------------------------------------------------------------------

@router.post("/", response_model=ParentResponse, status_code=status.HTTP_201_CREATED)
def create_parent(
    payload: ParentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN"]))
):
    service = ParentService(db)

    try:
        return service.create_parent(
            school_id=current_user.school_id,
            user_id=payload.user_id,
            occupation=payload.occupation,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------
# Get Parent by ID (admin/staff)
# ---------------------------------------------------------------------

@router.get("/{parent_id}", response_model=ParentResponse)
def get_parent(
    parent_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN", "STAFF"]))
):
    service = ParentService(db)

    parent = service.get_parent(
        school_id=current_user.school_id,
        parent_id=parent_id
    )

    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")

    return parent


# ---------------------------------------------------------------------
# Get My Parent Profile (self)
# ---------------------------------------------------------------------

@router.get("/me", response_model=ParentResponse)
def get_my_parent(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = ParentService(db)

    parent = service.get_by_user(
        school_id=current_user.school_id,
        user_id=current_user.id
    )

    if not parent:
        raise HTTPException(status_code=404, detail="Parent profile not found")

    return parent


# ---------------------------------------------------------------------
# Get Parent by User (admin/staff)
# ---------------------------------------------------------------------

@router.get("/by-user/{user_id}", response_model=ParentResponse)
def get_parent_by_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN", "STAFF"]))
):
    service = ParentService(db)

    parent = service.get_by_user(
        school_id=current_user.school_id,
        user_id=user_id
    )

    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")

    return parent


# ---------------------------------------------------------------------
# Link Parent ↔ Student
# ---------------------------------------------------------------------

@router.post("/link-student", status_code=status.HTTP_201_CREATED)
def link_parent_to_student(
    student_id: UUID,
    parent_id: UUID,
    relationship: str,
    is_primary: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN"]))
):
    service = ParentService(db)

    try:
        return service.link_parent_to_student(
            school_id=current_user.school_id,
            student_id=student_id,
            parent_id=parent_id,
            relationship=relationship,
            is_primary=is_primary
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))