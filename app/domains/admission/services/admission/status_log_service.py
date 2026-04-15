# admission/services/admission/status_log_service.py


# admission/services/admission/status_log_service.py

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from admission.models.applications import ApplicationStatusLog
from admission.repositories.status_logs import ApplicationStatusLogRepository
from types.admissions import ApplicationStatus as ApplicationStatusEnum


class StatusLogService:
    """
    Service for managing Admission Application status audit logs.
    
    Responsibilities:
    - Appending status change logs (append-only).
    - Retrieving status history (ordered chronologically).
    - Retrieving the latest status log.
    
    Constraints:
    - No business logic (does not validate if status transition is allowed).
    - No updates or deletes (audit trail immutability).
    - No transaction management (commit/rollback delegated to caller).
    - No direct SQL (uses Repository).
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = ApplicationStatusLogRepository()

    def log_status_change(
        self,
        application_id: UUID,
        from_status: ApplicationStatusEnum,
        to_status: ApplicationStatusEnum,
        changed_by_id: UUID,
        remark: Optional[str] = None
    ) -> ApplicationStatusLog:
        """
        Record a status change event for an application.
        
        This method creates an immutable audit record. It does not validate 
        whether the transition is permitted (that is the responsibility of 
        the ApplicationService or Workflow layer).
        
        Args:
            application_id: The UUID of the admission application.
            from_status: The status before the change.
            to_status: The status after the change.
            changed_by_id: The UUID of the user performing the change.
            remark: Optional text remark explaining the change.
            
        Returns:
            The created ApplicationStatusLog ORM object.
        """
        log_entry = ApplicationStatusLog(
            application_id=application_id,
            from_status=from_status,
            to_status=to_status,
            changed_by_id=changed_by_id,
            remark=remark,
            changed_at=datetime.utcnow()
        )

        # Repository handles flush, Caller handles commit
        return self.repository.create(self.db, log_entry)

    def get_history(
        self,
        application_id: UUID
    ) -> List[ApplicationStatusLog]:
        """
        Retrieve the complete chronological history of status changes.
        
        Args:
            application_id: The UUID of the admission application.
            
        Returns:
            List of ApplicationStatusLog objects ordered by changed_at (asc).
        """
        return self.repository.get_history_by_application(
            db=self.db,
            application_id=application_id
        )

    def get_latest_log(
        self,
        application_id: UUID
    ) -> Optional[ApplicationStatusLog]:
        """
        Retrieve the most recent status change record.
        
        Args:
            application_id: The UUID of the admission application.
            
        Returns:
            The most recent ApplicationStatusLog object, or None.
        """
        return self.repository.get_latest_log_by_application(
            db=self.db,
            application_id=application_id
        )