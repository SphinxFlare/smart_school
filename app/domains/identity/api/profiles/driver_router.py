# identity/api/profiles/driver_router.py


from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps.common import get_db
from app.deps.roles import require_roles

from domains.identity.schemas.driver import (
    DriverCreate,
    DriverUpdate,
    DriverResponse,
)

from domains.identity.services.profiles.driver_service import DriverService


router = APIRouter(prefix="/drivers", tags=["Drivers"])


# ---------------------------------------------------------------------
# Create Driver Profile
# ---------------------------------------------------------------------

@router.post("/", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
def create_driver(
    payload: DriverCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN"]))
):
    service = DriverService(db)

    try:
        return service.create_driver(
            school_id=current_user.school_id,
            staff_member_id=payload.staff_member_id,
            license_number=payload.license_number,
            license_type=payload.license_type,
            license_expiry=payload.license_expiry,
            status=payload.status,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------
# Get Driver by ID
# ---------------------------------------------------------------------

@router.get("/{driver_id}", response_model=DriverResponse)
def get_driver(
    driver_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN", "STAFF"]))
):
    service = DriverService(db)

    driver = service.get_driver(
        school_id=current_user.school_id,
        driver_id=driver_id
    )

    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    return driver


# ---------------------------------------------------------------------
# Get Driver by Staff Member
# ---------------------------------------------------------------------

@router.get("/by-staff/{staff_member_id}", response_model=DriverResponse)
def get_driver_by_staff(
    staff_member_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN", "STAFF"]))
):
    service = DriverService(db)

    driver = service.get_by_staff_member(
        school_id=current_user.school_id,
        staff_member_id=staff_member_id
    )

    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    return driver


# ---------------------------------------------------------------------
# Update Driver
# ---------------------------------------------------------------------

@router.put("/{driver_id}", response_model=DriverResponse)
def update_driver(
    driver_id: UUID,
    payload: DriverUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN"]))
):
    service = DriverService(db)

    try:
        return service.update_driver(
            school_id=current_user.school_id,
            driver_id=driver_id,
            update_data=payload.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))