# admission/services/workflows/approval_service.py

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from admission.services.admission.application_service import ApplicationService
from admission.services.admission.document_service import DocumentService
from admission.services.admission.enrollment_service import EnrollmentService
from types.admissions import ApplicationStatus as ApplicationStatusEnum, EnrollmentType
from admission.services.validators.application_validators import (
    validate_not_enrolled,
    validate_student_linked,
    validate_documents_verified,
    validate_no_existing_enrollment,
)


class ApprovalService:
    """
    Orchestration Service for Admission Approval Workflows.
    
    Responsibilities:
    - Coordinating the full approval lifecycle (Documents -> Enrollment -> Status).
    - Ensuring atomicity across multiple services (transaction boundary controlled by caller).
    - Enforcing concurrency safety via underlying service locking mechanisms.
    - Ensuring idempotency (preventing duplicate enrollments/logs).
    
    Constraints:
    - Does NOT modify underlying services (Open/Closed Principle).
    - Does NOT call repositories directly (Dependency Inversion).
    - Does NOT commit transactions (delegated to API/Controller layer).
    - Does NOT contain raw SQL.
    - Multi-tenant safety enforced via school_id propagation.
    """

    def __init__(
        self, 
        db: Session, 
        application_service: ApplicationService,
        document_service: DocumentService,
        enrollment_service: EnrollmentService
    ):
        """
        Initialize with dependent services.
        
        Injecting services allows for easier testing and adheres to 
        Dependency Inversion Principle.
        """
        self.db = db
        self.application_service = application_service
        self.document_service = document_service
        self.enrollment_service = enrollment_service

    def approve_application(
        self,
        school_id: UUID,
        application_id: UUID,
        section_id: UUID,
        approved_by_id: UUID,
        remark: Optional[str] = None
    ) -> dict:
        """
        Execute the full approval workflow as a single atomic operation.
        
        Workflow Steps:
        1. Idempotency Check: Ensure application is not already approved/enrolled.
        2. Validation: Check status allows approval.
        3. Document Verification: Ensure all uploaded documents are verified.
        4. Student Linkage: Ensure student_id is linked (future-safe hook).
        5. Enrollment Integrity: Check no existing enrollment for student/year.
        6. Create Enrollment: Generate number (locked) and create record.
        7. Update Status: Transition application to APPROVED (locked).
        8. Audit: StatusLogService called internally by ApplicationService.
        
        Args:
            school_id: Tenant identifier.
            application_id: The admission application UUID.
            section_id: The section to assign upon enrollment.
            approved_by_id: The admin/user approving the application.
            remark: Optional remark for the status change log.
            
        Returns:
            Dict containing application and enrollment details.
            
        Raises:
            ValueError: If validation checks fail (status, documents, duplicates).
            IntegrityError: If DB constraints violate (handled by caller).
        """
        # -----------------------------------------------------------------
        # 1. Initial Retrieval & Idempotency Check
        # -----------------------------------------------------------------
        # Note: get_application is non-locking. Final consistency is guaranteed 
        # by the locked transition_status call at the end.
        application = self.application_service.get_locked_for_approval(
            db=self.db,
            school_id=school_id,
            application_id=application_id
        )

        if not application:
            raise ValueError(f"Application {application_id} not found")

        # Idempotency: If already approved or enrolled, return existing state
        if application.status in [ApplicationStatusEnum.APPROVED, ApplicationStatusEnum.ENROLLED]:
            # Check if enrollment exists to return complete info
            enrollment = None
            if application.student_id:
                enrollment = self.enrollment_service.get_by_student_and_year(
                    school_id=school_id,
                    student_id=application.student_id,
                    academic_year_id=application.academic_year_id
                )
            
            return {
                "application": application,
                "enrollment": enrollment,
                "message": "Application already approved/enrolled"
            }

        # -----------------------------------------------------------------
        # 2. Status Validation
        # -----------------------------------------------------------------
        # Only SUBMITTED or UNDER_REVIEW applications can be approved
        if application.status not in [ApplicationStatusEnum.SUBMITTED, ApplicationStatusEnum.UNDER_REVIEW]:
            raise ValueError(
                f"Cannot approve application with status {application.status.value}"
            )

        # -----------------------------------------------------------------
        # 3. Document Verification Check
        # -----------------------------------------------------------------
        # Ensure all uploaded documents are verified before approval
        documents = self.document_service.list_documents(
            application_id=application_id
        )

        validate_documents_verified(documents)

        # -----------------------------------------------------------------
        # 4. Student Linkage Check (Future-Safe)
        # -----------------------------------------------------------------
        # Enrollment requires a student_id. If null, approval cannot proceed 
        # until student profile is created/linked.
        validate_student_linked(application)

        # -----------------------------------------------------------------
        # 5. Enrollment Integrity Check
        # -----------------------------------------------------------------
        # Ensure student isn't already enrolled in this academic year
        # (Double check despite status check, for data safety)
        existing_enrollment = self.enrollment_service.get_by_student_and_year(
            school_id=school_id,
            student_id=application.student_id,
            academic_year_id=application.academic_year_id
        )

        validate_no_existing_enrollment(existing_enrollment)

        # -----------------------------------------------------------------
        # 6. Create Enrollment (Locked Internally)
        # -----------------------------------------------------------------
        # EnrollmentService handles row-level locking for number generation
        enrollment = self.enrollment_service.create_enrollment(
            school_id=school_id,
            academic_year_id=application.academic_year_id,
            student_id=application.student_id,
            class_id=application.applying_class_id,
            section_id=section_id,
            enrollment_type=EnrollmentType.NEW, # Or derive from logic
            created_by_id=approved_by_id
        )

        # -----------------------------------------------------------------
        # 7. Update Application Status (Locked Internally)
        # -----------------------------------------------------------------
        # ApplicationService handles row-level locking for status transition
        # and delegates audit logging to StatusLogService internally.
        updated_application = self.application_service.transition_status(
            school_id=school_id,
            application_id=application_id,
            new_status=ApplicationStatusEnum.APPROVED,
            changed_by_id=approved_by_id,
            remark=remark or "Application approved and enrolled"
        )

        # -----------------------------------------------------------------
        # 8. Return Result
        # -----------------------------------------------------------------
        # Do NOT commit here. Caller (API/Controller) must commit the transaction.
        # If any step above failed, an exception was raised, and caller should rollback.
        return {
            "application": updated_application,
            "enrollment": enrollment,
            "message": "Approval workflow completed successfully"
        }