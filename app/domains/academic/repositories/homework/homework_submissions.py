# academic/repositories/homework_submissions.py

from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from academic.models.assessment import HomeworkSubmission
from repositories.base import BaseRepository
from types.results import SubmissionStatus



class HomeworkSubmissionRepository(BaseRepository[HomeworkSubmission]):
    """
    Repository for HomeworkSubmission persistence operations.
    
    Extends BaseRepository as this model does not contain school_id directly.
    Tenant isolation is enforced upstream by validating homework ownership
    (which links to teacher_assignment and ultimately to school).
    
    Responsibilities:
    - Encapsulate submission lookup and listing patterns.
    - Treat (homework_id, student_id) as unique (enforced by UniqueConstraint).
    - Support filtering by homework, student, and submission status.
    - Provide aggregate helpers for dashboard metrics.
    - Provide row-locking for safe grading operations.
    - Ensure deterministic ordering for grading workflows.
    - Support pagination with explicit offset/limit defaults.
    - Handle null aggregation results safely.
    
    Non-Responsibilities:
    - Tenant isolation (enforced upstream via homework validation).
    - Business logic (late detection, grade computation, edit policies).
    - Cross-domain joins to verify school ownership.
    - Soft-delete filtering (model does not support it).
    - Transaction management (commit/rollback).
    - Auto-updating homework state based on submission counts.
    - Mutating attachment JSON fields.
    
    Index Requirements (must exist at DB level):
    - ix_submission_homework (homework_id)
    - ix_submission_student (student_id)
    - ix_submission_status (status)
    - ix_submission_submitted_at (submitted_at)
    - uq_submission_homework_student (homework_id, student_id) - UniqueConstraint
    """

    def __init__(self):
        super().__init__(HomeworkSubmission)

    def get_by_homework_and_student(
        self,
        db: Session,
        homework_id: UUID,
        student_id: UUID
    ) -> Optional[HomeworkSubmission]:
        """
        Retrieve a submission matching the unique constraint (homework_id, student_id).
        
        A student should have exactly one submission per homework.
        This is enforced at the database level via UniqueConstraint.
        
        Args:
            db: Database session.
            homework_id: Homework UUID.
            student_id: Student UUID.
            
        Returns:
            HomeworkSubmission object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.homework_id == homework_id,
            self.model.student_id == student_id
        )

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def exists_by_homework_and_student(
        self,
        db: Session,
        homework_id: UUID,
        student_id: UUID
    ) -> bool:
        """
        Lightweight existence check for a submission.
        
        Uses ID-only select for efficiency (no full row fetch).
        
        Args:
            db: Database session.
            homework_id: Homework UUID.
            student_id: Student UUID.
            
        Returns:
            True if submission exists, False otherwise.
        """
        stmt = select(self.model.id).where(
            self.model.homework_id == homework_id,
            self.model.student_id == student_id
        ).limit(1)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def get_locked_for_update(
        self,
        db: Session,
        homework_id: UUID,
        student_id: UUID
    ) -> Optional[HomeworkSubmission]:
        """
        Retrieve a submission with a row-level lock for safe grading.
        
        Prevents race conditions when multiple users grade the same
        submission concurrently (e.g., updating marks, remarks, status).
        
        Args:
            db: Database session.
            homework_id: Homework UUID.
            student_id: Student UUID.
            
        Returns:
            Locked HomeworkSubmission object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.homework_id == homework_id,
            self.model.student_id == student_id
        )

        stmt = stmt.with_for_update()

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def list_by_homework(
        self,
        db: Session,
        homework_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[HomeworkSubmission]:
        """
        List all submissions for a specific homework.
        
        Ordered by submitted_at ascending for grading workflow
        (first submitted first in queue).
        
        Args:
            db: Database session.
            homework_id: Homework UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of HomeworkSubmission ORM objects.
        """
        stmt = select(self.model).where(
            self.model.homework_id == homework_id
        )

        stmt = stmt.order_by(self.model.submitted_at.asc())
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
    ) -> List[HomeworkSubmission]:
        """
        List all submissions for a specific student.
        
        Ordered by submitted_at descending for student history view
        (most recent submissions first).
        
        Args:
            db: Database session.
            student_id: Student UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of HomeworkSubmission ORM objects.
        """
        stmt = select(self.model).where(
            self.model.student_id == student_id
        )

        stmt = stmt.order_by(self.model.submitted_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_status(
        self,
        db: Session,
        homework_id: UUID,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[HomeworkSubmission]:
        """
        List submissions for a homework filtered by status.
        
        Uses centralized SubmissionStatus constants for type safety.
        Useful for grading queues (e.g., show only SUBMITTED pending grading).
        
        Args:
            db: Database session.
            homework_id: Homework UUID.
            status: Submission status (use SubmissionStatus constants).
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of HomeworkSubmission ORM objects.
        """
        stmt = select(self.model).where(
            self.model.homework_id == homework_id,
            self.model.status == status
        )

        stmt = stmt.order_by(self.model.submitted_at.asc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_homework_and_date_range(
        self,
        db: Session,
        homework_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[HomeworkSubmission]:
        """
        List submissions for a homework within a submission date range.
        
        Uses range comparisons to preserve index usage on submitted_at.
        
        Args:
            db: Database session.
            homework_id: Homework UUID.
            start_date: Range start datetime (inclusive).
            end_date: Range end datetime (inclusive).
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of HomeworkSubmission ORM objects.
        """
        stmt = select(self.model).where(
            self.model.homework_id == homework_id,
            self.model.submitted_at >= start_date,
            self.model.submitted_at <= end_date
        )

        stmt = stmt.order_by(self.model.submitted_at.asc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_student_and_date_range(
        self,
        db: Session,
        student_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[HomeworkSubmission]:
        """
        List submissions for a student within a submission date range.
        
        Uses range comparisons to preserve index usage on submitted_at.
        
        Args:
            db: Database session.
            student_id: Student UUID.
            start_date: Range start datetime (inclusive).
            end_date: Range end datetime (inclusive).
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of HomeworkSubmission ORM objects.
        """
        stmt = select(self.model).where(
            self.model.student_id == student_id,
            self.model.submitted_at >= start_date,
            self.model.submitted_at <= end_date
        )

        stmt = stmt.order_by(self.model.submitted_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def count_by_status(
        self,
        db: Session,
        homework_id: UUID
    ) -> Dict[str, int]:
        """
        Count submissions grouped by status for a homework.
        
        Returns raw counts only; service layer interprets for business logic.
        
        Args:
            db: Database session.
            homework_id: Homework UUID.
            
        Returns:
            Dictionary mapping status string to count.
        """
        stmt = select(
            self.model.status,
            func.count(self.model.id).label('count')
        ).where(
            self.model.homework_id == homework_id
        ).group_by(self.model.status)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        
        return {row[0]: row[1] for row in result.all()}

    def count_total(
        self,
        db: Session,
        homework_id: UUID
    ) -> int:
        """
        Count total submissions for a homework.
        
        Quick metric for homework completion tracking.
        
        Args:
            db: Database session.
            homework_id: Homework UUID.
            
        Returns:
            Total count of submissions.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.homework_id == homework_id
        )

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_pending(
        self,
        db: Session,
        homework_id: UUID
    ) -> int:
        """
        Count pending (ungraded) submissions for a homework.
        
        Includes SUBMITTED and PENDING statuses.
        Useful for teacher grading queue indicators.
        
        Args:
            db: Database session.
            homework_id: Homework UUID.
            
        Returns:
            Count of submissions pending grading.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.homework_id == homework_id,
            self.model.status.in_([SubmissionStatus.SUBMITTED, SubmissionStatus.PENDING])
        )

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_graded(
        self,
        db: Session,
        homework_id: UUID
    ) -> int:
        """
        Count graded submissions for a homework.
        
        Useful for tracking grading progress.
        
        Args:
            db: Database session.
            homework_id: Homework UUID.
            
        Returns:
            Count of submissions with GRADED status.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.homework_id == homework_id,
            self.model.status == SubmissionStatus.GRADED
        )

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_status_value(
        self,
        db: Session,
        homework_id: UUID,
        status: str
    ) -> int:
        """
        Count submissions for a specific status value.
        
        Args:
            db: Database session.
            homework_id: Homework UUID.
            status: Status string to count.
            
        Returns:
            Count of submissions with the specified status.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.homework_id == homework_id,
            self.model.status == status
        )

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return result.scalar() or 0

    def get_average_marks(
        self,
        db: Session,
        homework_id: UUID
    ) -> Optional[float]:
        """
        Calculate average marks awarded for a homework.
        
        Only includes submissions that have been graded (marks_awarded is not null).
        Returns precise numeric type from DB; service layer handles conversion.
        
        Args:
            db: Database session.
            homework_id: Homework UUID.
            
        Returns:
            Average marks as float, or None if no graded submissions exist.
        """
        stmt = select(
            func.avg(self.model.marks_awarded).label('avg_marks')
        ).where(
            self.model.homework_id == homework_id,
            self.model.marks_awarded.isnot(None)
        )

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        row = result.first()
        
        # Handle null result safely
        if row is None or row[0] is None:
            return None
        
        return float(row[0])

    def get_sum_marks(
        self,
        db: Session,
        homework_id: UUID
    ) -> float:
        """
        Calculate sum of marks awarded for a homework.
        
        Only includes submissions that have been graded (marks_awarded is not null).
        
        Args:
            db: Database session.
            homework_id: Homework UUID.
            
        Returns:
            Sum of marks as float (0.0 if no graded submissions).
        """
        stmt = select(
            func.sum(self.model.marks_awarded).label('sum_marks')
        ).where(
            self.model.homework_id == homework_id,
            self.model.marks_awarded.isnot(None)
        )

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        row = result.first()
        
        # Handle null result safely
        return float(row[0]) if row is not None and row[0] is not None else 0.0

    def get_max_marks(
        self,
        db: Session,
        homework_id: UUID
    ) -> Optional[float]:
        """
        Get maximum marks awarded for a homework.
        
        Only includes submissions that have been graded (marks_awarded is not null).
        
        Args:
            db: Database session.
            homework_id: Homework UUID.
            
        Returns:
            Maximum marks as float, or None if no graded submissions.
        """
        stmt = select(
            func.max(self.model.marks_awarded).label('max_marks')
        ).where(
            self.model.homework_id == homework_id,
            self.model.marks_awarded.isnot(None)
        )

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        row = result.first()
        
        # Handle null result safely
        return float(row[0]) if row is not None and row[0] is not None else None

    def get_min_marks(
        self,
        db: Session,
        homework_id: UUID
    ) -> Optional[float]:
        """
        Get minimum marks awarded for a homework.
        
        Only includes submissions that have been graded (marks_awarded is not null).
        
        Args:
            db: Database session.
            homework_id: Homework UUID.
            
        Returns:
            Minimum marks as float, or None if no graded submissions.
        """
        stmt = select(
            func.min(self.model.marks_awarded).label('min_marks')
        ).where(
            self.model.homework_id == homework_id,
            self.model.marks_awarded.isnot(None)
        )

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        row = result.first()
        
        # Handle null result safely
        return float(row[0]) if row is not None and row[0] is not None else None