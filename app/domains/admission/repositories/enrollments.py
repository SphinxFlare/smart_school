# admission/repositories/enrollments.py

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select

from admission.models.enrollments import StudentEnrollment
from repositories.base import SchoolScopedRepository


class StudentEnrollmentRepository(SchoolScopedRepository[StudentEnrollment]):
    """
    Repository for StudentEnrollment persistence operations.
    
    Extends SchoolScopedRepository to enforce tenant isolation (school_id)
    and prepare for potential soft-delete filtering in the future.
    
    Responsibilities:
    - Encapsulate enrollment query patterns (lookups, lists, locking).
    - Ensure all queries respect multi-tenancy (school_id).
    - Support integrity checks for unique constraints (via lookups).
    - Return ORM objects for service-layer manipulation.
    
    Non-Responsibilities:
    - Business logic (promotion rules, enrollment validation).
    - Transaction management (commit/rollback).
    - Generating enrollment numbers (logic belongs in service, 
      though this repo provides locking support for it).
    """

    def __init__(self):
        super().__init__(StudentEnrollment)

    # ---------------------------------------------------------------------
    # Custom Query Methods
    # ---------------------------------------------------------------------

    def get_by_student_and_academic_year(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        academic_year_id: UUID
    ) -> Optional[StudentEnrollment]:
        """
        Retrieve an enrollment for a specific student in a specific academic year.
        
        Used to enforce the unique constraint (student_id, academic_year_id)
        at the service layer before creation.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            student_id: The student's UUID.
            academic_year_id: The academic year UUID.
            
        Returns:
            StudentEnrollment object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.student_id == student_id,
            self.model.academic_year_id == academic_year_id
        )

        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def list_by_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentEnrollment]:
        """
        Retrieve all enrollments for a specific student within the school.
        
        Ordered by enrollment_date descending to show most recent first.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            student_id: The student's UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of StudentEnrollment ORM objects.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.student_id == student_id
        )

        stmt = stmt.order_by(self.model.enrollment_date.desc())
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_academic_year(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentEnrollment]:
        """
        Retrieve all enrollments for a specific academic year within the school.
        
        Useful for generating class rolls or year-specific reports.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            academic_year_id: The academic year UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of StudentEnrollment ORM objects.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.academic_year_id == academic_year_id
        )

        stmt = stmt.order_by(self.model.enrollment_number.asc())
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_by_enrollment_number(
        self,
        db: Session,
        school_id: UUID,
        enrollment_number: str
    ) -> Optional[StudentEnrollment]:
        """
        Retrieve an enrollment by its unique enrollment number within the school.
        
        Supports admin lookup functionality.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            enrollment_number: The unique enrollment number string.
            
        Returns:
            StudentEnrollment object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.enrollment_number == enrollment_number
        )

        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_latest_enrollment_locked(
        self,
        db: Session,
        school_id: UUID
    ) -> Optional[StudentEnrollment]:
        """
        Retrieve the most recent enrollment record for a school with a row lock.
        
        Used during sequential enrollment number generation to prevent race 
        conditions when multiple admins create enrollments simultaneously.
        Locks the latest row so the service can safely read the last number 
        and compute the next one within the same transaction.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            
        Returns:
            Locked StudentEnrollment object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id
        )

        # Order by ID desc to get the latest created record
        stmt = stmt.order_by(self.model.enrollment_date.desc(),
                             self.model.id.desc()
                             ).limit(1)
        
        # Apply row lock
        stmt = stmt.with_for_update()
        
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return result.scalar_one_or_none()