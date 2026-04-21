# app/domains/admission/api/applications.py


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from db.dependencies import get_db

from admission.services.admission.application_service import ApplicationService

from admission.schemas.applications import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
    ApplicationListItem,
    ApplicationStatusCounts,
    ApplicationSubmitRequest,
)

from types.admissions import ApplicationStatus


router = APIRouter(
    prefix="/applications",
    tags=["Admission Applications"],
)


# -----------------------------------------------------
# Status counts
# -----------------------------------------------------

@router.get("/status-counts", response_model=ApplicationStatusCounts)
def get_status_counts(
    school_id: UUID = Query(..., description="School ID (temporary until tenant context)"),
    academic_year_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
):
    try:
        service = ApplicationService(db=db)

        counts = service.get_status_counts(
            school_id=school_id,
            academic_year_id=academic_year_id,
        )

        return ApplicationStatusCounts(counts=counts)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------
# List applications
# -----------------------------------------------------

@router.get("/", response_model=List[ApplicationListItem])
def list_applications(
    school_id: UUID = Query(..., description="School ID (temporary until tenant context)"),
    academic_year_id: Optional[UUID] = Query(None),
    status: Optional[ApplicationStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    try:
        service = ApplicationService(db=db)

        applications = service.list_applications(
            school_id=school_id,
            academic_year_id=academic_year_id,
            status=status,
            skip=skip,
            limit=limit,
        )

        return applications

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------
# Get single application
# -----------------------------------------------------

@router.get("/{application_id}", response_model=ApplicationRead)
def get_application(
    application_id: UUID,
    school_id: UUID = Query(..., description="School ID (temporary until tenant context)"),
    db: Session = Depends(get_db),
):
    try:
        service = ApplicationService(db=db)

        application = service.get_application(
            school_id=school_id,
            application_id=application_id,
        )

        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        return application

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------
# Create application
# -----------------------------------------------------

@router.post("/", response_model=ApplicationRead)
def create_application(
    application_data: ApplicationCreate,
    school_id: UUID = Query(..., description="School ID (temporary until tenant context)"),
    db: Session = Depends(get_db),
):
    try:
        service = ApplicationService(db=db)

        student_data = application_data.model_dump(
            exclude={
                "school_id",
                "academic_year_id",
                "student_id",
                "applying_class_id",
            }
        )

        application = service.create_application(
            school_id=school_id,
            academic_year_id=application_data.academic_year_id,
            student_data=student_data,
            applying_class_id=application_data.applying_class_id,
            created_by_id=None,
        )

        return application

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------
# Update application
# -----------------------------------------------------

@router.put("/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: UUID,
    application_data: ApplicationUpdate,
    school_id: UUID = Query(..., description="School ID (temporary until tenant context)"),
    db: Session = Depends(get_db),
):
    try:
        service = ApplicationService(db=db)

        update_data = application_data.model_dump(exclude_unset=True)

        application = service.update_application(
            school_id=school_id,
            application_id=application_id,
            update_data=update_data,
        )

        return application

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------
# Submit application
# -----------------------------------------------------

@router.post("/{application_id}/submit", response_model=ApplicationRead)
def submit_application(
    application_id: UUID,
    _: ApplicationSubmitRequest,
    school_id: UUID = Query(..., description="School ID (temporary until tenant context)"),
    db: Session = Depends(get_db),
):
    try:
        service = ApplicationService(db=db)

        application = service.submit_application(
            school_id=school_id,
            application_id=application_id,
            submitted_by_id=None,
        )

        return application

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))