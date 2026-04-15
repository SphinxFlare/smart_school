# academic/repositories/exam_repository.py


from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select

from academic.models.assessment import Exam
from repositories.base import SchoolScopedRepository
from types.types import ExamType


# =============================================================================
# EXAM REPOSITORY
# =============================================================================

class ExamRepository(SchoolScopedRepository[Exam]):
    """
    Repository for Exam persistence operations.
    
    Extends SchoolScopedRepository to enforce tenant isolation (school_id)
    and soft-delete filtering.
    
    Responsibilities:
    - Encapsulate exam lookup and listing patterns.
    - Support filtering by academic year, exam type, and date ranges.
    - Provide row-locking for safe publishing workflows.
    
    Non-Responsibilities:
    - Business logic (date overlap validation, publishing rules).
    - Transaction management.
    """

    def __init__(self):
        super().__init__(Exam)

    def list_by_school_and_year(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Exam]:
        """
        List all exams for a school within an academic year.
        
        Ordered by start_date ascending for chronological display.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            academic_year_id: Academic year UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of Exam ORM objects.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.academic_year_id == academic_year_id
        )

        stmt = stmt.order_by(self.model.start_date.asc())
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_exam_type(
        self,
        db: Session,
        school_id: UUID,
        exam_type: ExamType,
        academic_year_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Exam]:
        """
        List exams filtered by exam type (e.g., MIDTERM, FINAL).
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            exam_type: ExamType enum value.
            academic_year_id: Optional academic year filter.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of Exam ORM objects.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.type == exam_type
        )

        if academic_year_id is not None:
            stmt = stmt.where(self.model.academic_year_id == academic_year_id)

        stmt = stmt.order_by(self.model.start_date.desc())
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_within_date_range(
        self,
        db: Session,
        school_id: UUID,
        start_date: datetime,
        end_date: datetime,
        academic_year_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Exam]:
        """
        List exams occurring within a specific date range.
        
        Useful for calendar views and scheduling conflict checks.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            start_date: Range start datetime.
            end_date: Range end datetime.
            academic_year_id: Optional academic year filter.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of Exam ORM objects.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.start_date <= end_date,
            self.model.end_date >= start_date
        )

        if academic_year_id is not None:
            stmt = stmt.where(self.model.academic_year_id == academic_year_id)

        stmt = stmt.order_by(self.model.start_date.asc())
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_locked_for_publishing(
        self,
        db: Session,
        school_id: UUID,
        exam_id: UUID
    ) -> Optional[Exam]:
        """
        Retrieve an exam with a row-level lock for publishing workflows.
        
        Prevents race conditions when multiple admins attempt to publish
        or modify exam results concurrently.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            exam_id: Exam UUID.
            
        Returns:
            Locked Exam object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.id == exam_id,
            self.model.school_id == school_id
        )

        stmt = stmt.with_for_update()
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_school_and_id(
        self,
        db: Session,
        school_id: UUID,
        exam_id: UUID
    ) -> Optional[Exam]:
        """
        Retrieve an exam by ID within a specific school.
        
        Enforces tenant isolation at the lookup level.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            exam_id: Exam UUID.
            
        Returns:
            Exam object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.id == exam_id,
            self.model.school_id == school_id
        )

        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()