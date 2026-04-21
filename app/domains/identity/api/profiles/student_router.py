# identity/api/profiles/student_router.py


from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps.common import get_db
from app.deps.roles import require_roles
from app.deps.auth import get_current_user

from domains.identity.schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
)

from domains.identity.services.profiles.student_service import StudentService


router = APIRouter(prefix="/students", tags=["Students"])


# ---------------------------------------------------------------------
# Create Student Profile
# ---------------------------------------------------------------------

@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN"]))
):
    service = StudentService(db)

    try:
        return service.create_student(
            school_id=current_user.school_id,
            user_id=payload.user_id,
            admission_number=payload.admission_number,
            date_of_birth=payload.date_of_birth,
            emergency_contact_name=payload.emergency_contact_name,
            emergency_contact_phone=payload.emergency_contact_phone,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------
# Get Student by ID (admin/staff)
# ---------------------------------------------------------------------

@router.get("/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN", "STAFF"]))
):
    service = StudentService(db)

    student = service.get_student(
        school_id=current_user.school_id,
        student_id=student_id
    )

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    return student


# ---------------------------------------------------------------------
# Get My Student Profile (self)
# ---------------------------------------------------------------------

@router.get("/me", response_model=StudentResponse)
def get_my_student(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = StudentService(db)

    student = service.get_by_user(
        school_id=current_user.school_id,
        user_id=current_user.id
    )

    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    return student


# ---------------------------------------------------------------------
# Get Student by User (admin/staff only)
# ---------------------------------------------------------------------

@router.get("/by-user/{user_id}", response_model=StudentResponse)
def get_student_by_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN", "STAFF"]))
):
    service = StudentService(db)

    student = service.get_by_user(
        school_id=current_user.school_id,
        user_id=user_id
    )

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    return student


# ---------------------------------------------------------------------
# Update Student
# ---------------------------------------------------------------------

@router.put("/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: UUID,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN"]))
):
    service = StudentService(db)

    try:
        return service.update_student(
            school_id=current_user.school_id,
            student_id=student_id,
            update_data=payload.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))