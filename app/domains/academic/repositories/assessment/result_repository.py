# academic/repositories/result_repository.py


from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select

from academic.models.assessment import StudentExamResult
from repositories.base import BaseRepository


# =============================================================================
# STUDENT EXAM RESULT REPOSITORY
# =============================================================================

class StudentExamResultRepository(BaseRepository[StudentExamResult]):
    """
    Repository for StudentExamResult persistence operations.
    
    Extends BaseRepository as this model does not contain school_id directly.
    Tenant isolation is enforced upstream by validating exam_id ownership.
    
    Responsibilities:
    - Encapsulate result lookup and listing patterns.
    - Support filtering by publication status.
    - Provide row-locking for safe publication workflows.
    
    Non-Responsibilities:
    - Tenant isolation (enforced upstream via exam validation).
    - Business logic (result computation, aggregation).
    - Cross-domain joins to verify school ownership.
    """

    def __init__(self):
        super().__init__(StudentExamResult)

    def get_result(
        self,
        db: Session,
        exam_id: UUID,
        student_id: UUID
    ) -> Optional[StudentExamResult]:
        """
        Retrieve a result entry matching the unique constraint.
        
        Used to prevent duplicate results for the same exam/student.
        
        Args:
            db: Database session.
            exam_id: Exam UUID.
            student_id: Student UUID.
            
        Returns:
            StudentExamResult object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.exam_id == exam_id,
            self.model.student_id == student_id
        )

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def list_by_exam(
        self,
        db: Session,
        exam_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentExamResult]:
        """
        List all results for a specific exam.
        
        Ordered by percentage descending for ranking display.
        
        Args:
            db: Database session.
            exam_id: Exam UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of StudentExamResult ORM objects.
        """
        stmt = select(self.model).where(self.model.exam_id == exam_id)

        stmt = stmt.order_by(self.model.percentage.desc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_student(
        self,
        db: Session,
        student_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentExamResult]:
        """
        List all results for a specific student across exams.
        
        Ordered by created_at descending for historical view.
        
        Args:
            db: Database session.
            student_id: Student UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of StudentExamResult ORM objects.
        """
        stmt = select(self.model).where(self.model.student_id == student_id)

        stmt = stmt.order_by(self.model.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_published_by_exam(
        self,
        db: Session,
        exam_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentExamResult]:
        """
        List only published results for an exam.
        
        Useful for student-facing result views.
        
        Args:
            db: Database session.
            exam_id: Exam UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of published StudentExamResult ORM objects.
        """
        stmt = select(self.model).where(
            self.model.exam_id == exam_id,
            self.model.is_published.is_(True)
        )

        stmt = stmt.order_by(self.model.percentage.desc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_result_locked(
        self,
        db: Session,
        exam_id: UUID,
        student_id: UUID
    ) -> Optional[StudentExamResult]:
        """
        Retrieve a result entry with a row-level lock for safe publication.
        
        Prevents race conditions when publishing results concurrently.
        
        Args:
            db: Database session.
            exam_id: Exam UUID.
            student_id: Student UUID.
            
        Returns:
            Locked StudentExamResult object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.exam_id == exam_id,
            self.model.student_id == student_id
        )

        stmt = stmt.with_for_update()

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return result.scalar_one_or_none()