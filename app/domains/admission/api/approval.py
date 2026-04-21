# app/domains/admission/api/approval.py


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from db.dependencies import get_db

from admission.services.workflows.approval_service import ApprovalService
from admission.services.admission.application_service import ApplicationService
from admission.services.admission.document_service import DocumentService
from admission.services.admission.enrollment_service import EnrollmentService

from admission.schemas.approval import (
    ApprovalRequest,
    ApprovalResponse,
)


router = APIRouter(
    prefix="/approval",
    tags=["Admission Approval"],
)


# -----------------------------------------------------
# Approve application
# -----------------------------------------------------

@router.post(
    "/applications/{application_id}/approve",
    response_model=ApprovalResponse,
)
def approve_application(
    application_id: UUID,
    request_data: ApprovalRequest,
    school_id: UUID = Query(..., description="School ID (temporary until tenant context)"),
    approved_by_id: UUID = Query(..., description="User performing approval"),
    db: Session = Depends(get_db),
):
    try:
        application_service = ApplicationService(db=db)
        document_service = DocumentService(db=db)
        enrollment_service = EnrollmentService(db=db)

        service = ApprovalService(
            db=db,
            application_service=application_service,
            document_service=document_service,
            enrollment_service=enrollment_service,
        )

        result = service.approve_application(
            school_id=school_id,
            application_id=application_id,
            section_id=request_data.section_id,
            approved_by_id=approved_by_id,
            remark=request_data.remark,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))