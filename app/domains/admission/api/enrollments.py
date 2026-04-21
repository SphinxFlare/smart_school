# app/domains/admission/api/enrollments.py


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from db.dependencies import get_db

from admission.services.admission.enrollment_service import EnrollmentService

from admission.schemas.enrollments import (
    EnrollmentRead,
    EnrollmentListItem,
    EnrollmentByNumberResponse,
)


router = APIRouter(
    prefix="/enrollments",
    tags=["Admission Enrollments"],
)


# -----------------------------------------------------
# Get enrollment by id
# -----------------------------------------------------

@router.get(
    "/{enrollment_id}",
    response_model=EnrollmentRead,
)
def get_enrollment(
    enrollment_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        service = EnrollmentService(db=db)

        enrollment = service.get_enrollment(
            enrollment_id=enrollment_id,
        )

        if not enrollment:
            raise HTTPException(
                status_code=404,
                detail="Enrollment not found",
            )

        return enrollment

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------
# Get enrollment by number
# -----------------------------------------------------

@router.get(
    "/number/{enrollment_number}",
    response_model=Optional[EnrollmentByNumberResponse],
)
def get_by_enrollment_number(
    enrollment_number: str,
    school_id: UUID = Query(..., description="School ID (temporary until tenant context)"),
    db: Session = Depends(get_db),
):
    try:
        service = EnrollmentService(db=db)

        enrollment = service.get_by_enrollment_number(
            school_id=school_id,
            enrollment_number=enrollment_number,
        )

        return enrollment

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------
# List by student
# -----------------------------------------------------

@router.get(
    "/student/{student_id}",
    response_model=List[EnrollmentListItem],
)
def list_by_student(
    student_id: UUID,
    school_id: UUID = Query(..., description="School ID (temporary until tenant context)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    try:
        service = EnrollmentService(db=db)

        enrollments = service.list_by_student(
            school_id=school_id,
            student_id=student_id,
            skip=skip,
            limit=limit,
        )

        return enrollments

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------
# List by academic year
# -----------------------------------------------------

@router.get(
    "/",
    response_model=List[EnrollmentListItem],
)
def list_by_academic_year(
    school_id: UUID = Query(..., description="School ID (temporary until tenant context)"),
    academic_year_id: UUID = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    try:
        service = EnrollmentService(db=db)

        enrollments = service.list_by_academic_year(
            school_id=school_id,
            academic_year_id=academic_year_id,
            skip=skip,
            limit=limit,
        )

        return enrollments

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))