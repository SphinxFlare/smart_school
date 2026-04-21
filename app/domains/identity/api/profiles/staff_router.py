# identity/api/profiles/staff_router.py


from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps.common import get_db
from app.deps.roles import require_roles
from app.deps.auth import get_current_user

from domains.identity.schemas.staff import (
    StaffCreate,
    StaffUpdate,
    StaffResponse,
)

from domains.identity.services.profiles.staff_service import StaffService


router = APIRouter(prefix="/staff", tags=["Staff"])


# ---------------------------------------------------------------------
# Create Staff Profile
# ---------------------------------------------------------------------

@router.post("/", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
def create_staff(
    payload: StaffCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN"]))
):
    service = StaffService(db)

    try:
        return service.create_staff(
            school_id=current_user.school_id,
            user_id=payload.user_id,
            employee_id=payload.employee_id,
            position=payload.position,
            date_of_joining=payload.date_of_joining,
            department=payload.department,
            qualifications=payload.qualifications,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------
# Get Staff by ID (admin/staff)
# ---------------------------------------------------------------------

@router.get("/{staff_id}", response_model=StaffResponse)
def get_staff(
    staff_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN", "STAFF"]))
):
    service = StaffService(db)

    staff = service.get_staff(
        school_id=current_user.school_id,
        staff_id=staff_id
    )

    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    return staff


# ---------------------------------------------------------------------
# Get My Staff Profile (self)
# ---------------------------------------------------------------------

@router.get("/me", response_model=StaffResponse)
def get_my_staff(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = StaffService(db)

    staff = service.get_by_user(
        school_id=current_user.school_id,
        user_id=current_user.id
    )

    if not staff:
        raise HTTPException(status_code=404, detail="Staff profile not found")

    return staff


# ---------------------------------------------------------------------
# Get Staff by User (admin/staff)
# ---------------------------------------------------------------------

@router.get("/by-user/{user_id}", response_model=StaffResponse)
def get_staff_by_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN", "STAFF"]))
):
    service = StaffService(db)

    staff = service.get_by_user(
        school_id=current_user.school_id,
        user_id=user_id
    )

    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    return staff


# ---------------------------------------------------------------------
# Update Staff
# ---------------------------------------------------------------------

@router.put("/{staff_id}", response_model=StaffResponse)
def update_staff(
    staff_id: UUID,
    payload: StaffUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN"]))
):
    service = StaffService(db)

    try:
        return service.update_staff(
            school_id=current_user.school_id,
            staff_id=staff_id,
            update_data=payload.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))