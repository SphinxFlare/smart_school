# admission/repositories/application.py

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select

from admission.models.applications import AdmissionApplication
from types.admissions import ApplicationStatus
from repositories.base import SchoolScopedRepository


class AdmissionApplicationRepository(SchoolScopedRepository[AdmissionApplication]):
    """
    Repository for AdmissionApplication persistence operations.
    
    Extends SchoolScopedRepository to enforce tenant isolation (school_id)
    and soft-delete filtering automatically.
    
    Responsibilities:
    - Encapsulate complex query patterns (filtering, locking, lookups).
    - Ensure all queries respect multi-tenancy and soft-delete rules.
    - Return ORM objects for service-layer manipulation.
    
    Non-Responsibilities:
    - Business logic (status transitions, approvals, student creation).
    - Transaction management (commit/rollback).
    """

    def __init__(self):
        super().__init__(AdmissionApplication)

    # ---------------------------------------------------------------------
    # Custom Query Methods
    # ---------------------------------------------------------------------

    def list_filtered(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: Optional[UUID] = None,
        status: Optional[ApplicationStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AdmissionApplication]:
        """
        List applications with optional filtering by academic year and status.
        
        Designed to leverage the composite index ix_app_school_year_status
        (school_id, academic_year_id, status) when filters are provided.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            academic_year_id: Filter by specific academic year.
            status: Filter by specific application status (Enum).
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of AdmissionApplication ORM objects.
        """
        stmt = select(self.model).where(self.model.school_id == school_id)

        if academic_year_id:
            stmt = stmt.where(self.model.academic_year_id == academic_year_id)

        if status:
            # Ensure enum type comparison
            stmt = stmt.where(self.model.status == status)

        stmt = self._apply_soft_delete_filter(stmt)
        stmt = stmt.order_by(self.model.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_by_student_and_academic_year(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        academic_year_id: UUID
    ) -> Optional[AdmissionApplication]:
        """
        Check if a student already has an application for a specific academic year.
        
        Used to prevent duplicate applications during submission or enrollment.
        Accounts for the lifecycle where student_id is null before approval,
        but here we are querying *for* an existing linked student_id.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            student_id: The student's UUID.
            academic_year_id: The academic year UUID.
            
        Returns:
            AdmissionApplication object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.student_id == student_id,
            self.model.academic_year_id == academic_year_id
        )

        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_locked_for_approval(
        self,
        db: Session,
        school_id: UUID,
        application_id: UUID
    ) -> Optional[AdmissionApplication]:
        """
        Retrieve an application with a row-level lock for approval workflows.
        
        Prevents race conditions when multiple admins attempt to approve
        or process the same application concurrently.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            application_id: The application UUID.
            
        Returns:
            Locked AdmissionApplication ORM object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.id == application_id,
            self.model.school_id == school_id
        )

        stmt = self._apply_soft_delete_filter(stmt)
        
        # Apply row lock
        stmt = stmt.with_for_update(nowait=True)

        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def count_by_status(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: Optional[UUID] = None
    ) -> dict[ApplicationStatus, int]:
        """
        Count applications grouped by status for dashboard metrics.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            academic_year_id: Optional filter for specific year.
            
        Returns:
            Dictionary mapping ApplicationStatus to count.
        """
        from sqlalchemy import func
        
        stmt = select(
            self.model.status, 
            func.count(self.model.id).label("count")
        ).where(
            self.model.school_id == school_id
        )

        if academic_year_id:
            stmt = stmt.where(self.model.academic_year_id == academic_year_id)

        stmt = self._apply_soft_delete_filter(stmt)
        stmt = stmt.group_by(self.model.status)

        result = db.execute(stmt)
        
        # Convert to dict {Status: count}
        return {row[0]: row[1] for row in result.all()}