# admission/services/admission/application_service.py

from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from admission.models.applications import AdmissionApplication
from admission.services.rules.status_transitions import is_valid_transition
from admission.services.validators.application_validators import (
    validate_required_fields,
    validate_can_submit,
)
from admission.repositories.application import AdmissionApplicationRepository
from admission.services.admission.status_log_service import StatusLogService
from admission.services.admission.document_service import DocumentService
from types.admissions import ApplicationStatus as ApplicationStatusEnum


class ApplicationService:
    """
    Service for managing Admission Application lifecycle.

    Responsibilities:
    - Creating and updating application drafts.
    - Submitting applications (Draft -> Submitted).
    - Validating and executing status transitions.
    - Retrieving applications and metrics.
    - Delegating audit logging to StatusLogService.

    Constraints:
    - No direct enrollment creation.
    - No direct document verification logic.
    - No transaction management.
    - No direct SQL.
    - Multi-tenant safety enforced via school_id.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = AdmissionApplicationRepository()
        self.status_log_service = StatusLogService(db)
        self.document_service = DocumentService(db)

    # ---------------------------------------------------------------------
    # Lifecycle Methods
    # ---------------------------------------------------------------------

    def create_application(
        self,
        school_id: UUID,
        academic_year_id: UUID,
        student_data: dict,
        applying_class_id: UUID,
        created_by_id: Optional[UUID] = None
    ) -> AdmissionApplication:
        
        validate_required_fields(student_data)

        application = AdmissionApplication(
            school_id=school_id,
            academic_year_id=academic_year_id,
            first_name=student_data.get("first_name"),
            last_name=student_data.get("last_name"),
            date_of_birth=student_data.get("date_of_birth"),
            gender=student_data.get("gender"),
            applying_class_id=applying_class_id,
            status=ApplicationStatusEnum.DRAFT,
        )

        return self.repository.create(self.db, application)

    def update_application(
        self,
        school_id: UUID,
        application_id: UUID,
        update_data: dict
    ) -> AdmissionApplication:

        application = self.repository.get_by_school(
            db=self.db,
            id=application_id,
            school_id=school_id
        )

        if not application:
            raise ValueError(f"Application {application_id} not found")

        if application.status != ApplicationStatusEnum.DRAFT:
            raise ValueError("Cannot update application unless it is in DRAFT status")

        for key, value in update_data.items():
            if hasattr(application, key) and key not in [
                "id",
                "school_id",
                "status",
                "created_at",
            ]:
                setattr(application, key, value)

        application.updated_at = datetime.now()

        self.db.flush()
        return application

    def submit_application(
        self,
        school_id: UUID,
        application_id: UUID,
        submitted_by_id: Optional[UUID] = None
    ) -> AdmissionApplication:

        application = self.get_application(
            school_id=school_id,
            application_id=application_id,
        )

        if not application:
            raise ValueError(f"Application {application_id} not found")

        validate_can_submit(application)

        return self.transition_status(
            school_id=school_id,
            application_id=application_id,
            new_status=ApplicationStatusEnum.SUBMITTED,
            changed_by_id=submitted_by_id,
            remark="Application submitted",
        )

    # ---------------------------------------------------------------------
    # Status Transition
    # ---------------------------------------------------------------------

    def transition_status(
        self,
        school_id: UUID,
        application_id: UUID,
        new_status: ApplicationStatusEnum,
        changed_by_id: Optional[UUID],
        remark: Optional[str] = None
    ) -> AdmissionApplication:

        application = self.repository.get_locked_for_approval(
            db=self.db,
            school_id=school_id,
            application_id=application_id,
        )

        if not application:
            raise ValueError(f"Application {application_id} not found")

        current_status = application.status

        if not is_valid_transition(current_status, new_status):
            raise ValueError(
                f"Invalid status transition from "
                f"{current_status.value} to {new_status.value}"
            )

        application.status = new_status
        application.updated_at = datetime.now()

        if (
            new_status == ApplicationStatusEnum.SUBMITTED
            and not application.submitted_at
        ):
            application.submitted_at = datetime.now()

        self.db.flush()

        self.status_log_service.log_status_change(
            application_id=application.id,
            from_status=current_status,
            to_status=new_status,
            changed_by_id=changed_by_id,
            remark=remark,
        )

        return application

    # ---------------------------------------------------------------------
    # Queries
    # ---------------------------------------------------------------------

    def get_application(
        self,
        school_id: UUID,
        application_id: UUID
    ) -> Optional[AdmissionApplication]:

        return self.repository.get_by_school(
            db=self.db,
            id=application_id,
            school_id=school_id,
        )

    def list_applications(
        self,
        school_id: UUID,
        academic_year_id: Optional[UUID] = None,
        status: Optional[ApplicationStatusEnum] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AdmissionApplication]:

        return self.repository.list_filtered(
            db=self.db,
            school_id=school_id,
            academic_year_id=academic_year_id,
            status=status,
            skip=skip,
            limit=limit,
        )

    def get_status_counts(
        self,
        school_id: UUID,
        academic_year_id: Optional[UUID] = None
    ) -> Dict[ApplicationStatusEnum, int]:

        return self.repository.count_by_status(
            db=self.db,
            school_id=school_id,
            academic_year_id=academic_year_id,
        )

    def check_duplicate_application(
        self,
        school_id: UUID,
        student_id: UUID,
        academic_year_id: UUID
    ) -> bool:

        existing = self.repository.get_by_student_and_academic_year(
            db=self.db,
            school_id=school_id,
            student_id=student_id,
            academic_year_id=academic_year_id,
        )

        return existing is not None
    

    def get_locked_for_approval(
        self,
        school_id: UUID,
        application_id: UUID
    ) -> Optional[AdmissionApplication]:
        """
        Retrieve an application with a row-level lock for approval or workflow operations.

        This method is used in workflows where the application must not be modified
        concurrently by another transaction (e.g., approval, enrollment, status change).
        It delegates the locking query to the repository and ensures the operation
        remains inside the service layer instead of exposing repository access.

        The row lock (SELECT ... FOR UPDATE) guarantees that only one transaction
        can process the application at a time, preventing duplicate approvals,
        duplicate enrollments, or inconsistent state transitions.

        Args:
            school_id: Tenant identifier to enforce multi-tenant safety.
            application_id: The UUID of the admission application.

        Returns:
            The locked AdmissionApplication ORM object if found, else None.
        """

        return self.repository.get_locked_for_approval(
            db=self.db,
            school_id=school_id,
            application_id=application_id,
        )