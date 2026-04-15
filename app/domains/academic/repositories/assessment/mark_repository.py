# academic/repositories/mark_repository.py


from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from academic.models.assessment import StudentExamMark
from repositories.base import BaseRepository


# =============================================================================
# STUDENT EXAM MARK REPOSITORY
# =============================================================================

class StudentExamMarkRepository(BaseRepository[StudentExamMark]):
    """
    Repository for StudentExamMark persistence operations.
    
    Extends BaseRepository as this model does not contain school_id directly.
    Tenant isolation is enforced upstream by validating exam_schedule_id ownership.
    
    Responsibilities:
    - Encapsulate mark lookup and listing patterns.
    - Support aggregate computations (sum, average) for result calculation.
    - Provide row-locking for safe mark updates.
    
    Non-Responsibilities:
    - Tenant isolation (enforced upstream via schedule validation).
    - Business logic (percentage calculation, grade assignment).
    - Cross-domain joins to verify school ownership.
    """

    def __init__(self):
        super().__init__(StudentExamMark)

    def get_mark(
        self,
        db: Session,
        exam_schedule_id: UUID,
        student_id: UUID
    ) -> Optional[StudentExamMark]:
        """
        Retrieve a mark entry matching the unique constraint.
        
        Used to prevent duplicate marks for the same schedule/student.
        
        Args:
            db: Database session.
            exam_schedule_id: Exam schedule UUID.
            student_id: Student UUID.
            
        Returns:
            StudentExamMark object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.exam_schedule_id == exam_schedule_id,
            self.model.student_id == student_id
        )

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def list_by_schedule(
        self,
        db: Session,
        exam_schedule_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentExamMark]:
        """
        List all marks for a specific exam schedule.
        
        Useful for generating mark sheets for a subject/class.
        
        Args:
            db: Database session.
            exam_schedule_id: Exam schedule UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of StudentExamMark ORM objects.
        """
        stmt = select(self.model).where(
            self.model.exam_schedule_id == exam_schedule_id
        )

        stmt = stmt.order_by(self.model.student_id.asc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_student(
        self,
        db: Session,
        student_id: UUID,
        exam_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentExamMark]:
        """
        List all marks for a specific student across schedules.
        
        Optional exam_id filter for exam-specific mark lists.
        
        Args:
            db: Database session.
            student_id: Student UUID.
            exam_id: Optional exam UUID filter.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of StudentExamMark ORM objects.
        """
        # Join with exam_schedule to filter by exam_id if provided
        from academic.models.assessment import ExamSchedule
        
        if exam_id is not None:
            stmt = select(self.model).join(
                ExamSchedule,
                self.model.exam_schedule_id == ExamSchedule.id
            ).where(
                self.model.student_id == student_id,
                ExamSchedule.exam_id == exam_id
            )
        else:
            stmt = select(self.model).where(
                self.model.student_id == student_id
            )

        stmt = stmt.order_by(self.model.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_total_marks_by_schedule(
        self,
        db: Session,
        exam_schedule_id: UUID
    ) -> dict:
        """
        Compute aggregate mark statistics for a schedule.
        
        Returns sum of marks_obtained, sum of max_marks, and count.
        
        Args:
            db: Database session.
            exam_schedule_id: Exam schedule UUID.
            
        Returns:
            Dictionary with 'total_obtained', 'total_max', 'count' keys.
        """
        
        stmt = select(
            func.sum(self.model.marks_obtained).label('total_obtained'),
            func.sum(self.model.max_marks).label('total_max'),
            func.count(self.model.id).label('count')
        ).where(self.model.exam_schedule_id == exam_schedule_id)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        row = result.first()
        if not row:
            return {'total_obtained': 0.0, 'total_max': 0.0, 'count': 0}
        
        return {
            'total_obtained': float(row[0]) if row[0] else 0.0,
            'total_max': float(row[1]) if row[1] else 0.0,
            'count': row[2] if row[2] else 0
        }

    def get_mark_locked(
        self,
        db: Session,
        exam_schedule_id: UUID,
        student_id: UUID
    ) -> Optional[StudentExamMark]:
        """
        Retrieve a mark entry with a row-level lock for safe updates.
        
        Prevents race conditions when multiple users update marks concurrently.
        
        Args:
            db: Database session.
            exam_schedule_id: Exam schedule UUID.
            student_id: Student UUID.
            
        Returns:
            Locked StudentExamMark object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.exam_schedule_id == exam_schedule_id,
            self.model.student_id == student_id
        )

        stmt = stmt.with_for_update()

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return result.scalar_one_or_none()