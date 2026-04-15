# admission/repositories/status_logs.py

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select

from admission.models.applications import ApplicationStatusLog
from repositories.base import BaseRepository


class ApplicationStatusLogRepository(BaseRepository[ApplicationStatusLog]):
    """
    Repository for ApplicationStatusLog persistence operations.
    
    Extends BaseRepository as this model is an audit log without tenant 
    isolation columns (school_id) or soft-delete flags (is_deleted).
    
    Responsibilities:
    - Encapsulate audit trail retrieval patterns.
    - Ensure append-only retrieval consistency (ordered by timestamp).
    - Return ORM objects for service-layer inspection.
    
    Non-Responsibilities:
    - Tenant isolation (enforced upstream via application_id validation).
    - Business logic (status transition validation).
    - Transaction management (commit/rollback).
    - Soft-delete filtering (model does not support it).
    """

    def __init__(self):
        super().__init__(ApplicationStatusLog)

    # ---------------------------------------------------------------------
    # Custom Query Methods
    # ---------------------------------------------------------------------

    def get_history_by_application(
        self,
        db: Session,
        application_id: UUID
    ) -> List[ApplicationStatusLog]:
        """
        Retrieve the complete status history for a specific application.
        
        Returns logs ordered chronologically (ascending by changed_at) 
        to allow full timeline reconstruction.
        
        Args:
            db: Database session.
            application_id: The admission application UUID.
            
        Returns:
            List of ApplicationStatusLog ORM objects ordered by time.
        """
        stmt = select(self.model).where(
            self.model.application_id == application_id
        )

        # Order ascending for timeline reconstruction
        stmt = stmt.order_by(self.model.changed_at.asc())

        # Note: No soft-delete filter applied (model does not support it)
        # Note: No tenant filter applied (enforced upstream via application_id)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_latest_log_by_application(
        self,
        db: Session,
        application_id: UUID
    ) -> Optional[ApplicationStatusLog]:
        """
        Retrieve the most recent status change for a specific application.
        
        Useful for quickly determining the current state without 
        loading the entire history.
        
        Args:
            db: Database session.
            application_id: The admission application UUID.
            
        Returns:
            The most recent ApplicationStatusLog ORM object, or None.
        """
        stmt = select(self.model).where(
            self.model.application_id == application_id
        )

        # Order descending to get the latest record
        stmt = stmt.order_by(self.model.changed_at.desc()).limit(1)

        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # ---------------------------------------------------------------------
    # Inherited Methods Note
    # ---------------------------------------------------------------------
    # create(db, obj): Available via BaseRepository. Used to append new logs.
    # get(db, id): Available via BaseRepository. Used to fetch specific log entry.
    # delete(db, obj): Available via BaseRepository. 
    #   NOTE: As this is an audit table, deletion should be avoided at the 
    #   service layer. This repository does not enforce immutability 
    #   technically, but semantically represents an append-only store.