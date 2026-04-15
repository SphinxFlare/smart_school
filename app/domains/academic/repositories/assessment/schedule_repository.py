# academic/repositories/schedule_repository.py


from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select

from academic.models.assessment import ExamSchedule

from repositories.base import BaseRepository


# =============================================================================
# EXAM SCHEDULE REPOSITORY
# =============================================================================

class ExamScheduleRepository(BaseRepository[ExamSchedule]):
    """
    Repository for ExamSchedule persistence operations.
    
    Extends BaseRepository as this model does not contain school_id directly.
    Tenant isolation is enforced upstream by validating exam_id ownership.
    
    Responsibilities:
    - Encapsulate schedule lookup and listing patterns.
    - Support filtering by exam, class, section, and publication status.
    - Provide row-locking for concurrent scheduling edits.
    
    Non-Responsibilities:
    - Tenant isolation (enforced upstream via exam_id validation).
    - Business logic (conflict detection, invigilator availability).
    - Cross-domain joins to verify school ownership.
    """

    def __init__(self):
        super().__init__(ExamSchedule)

    def list_by_exam(
        self,
        db: Session,
        exam_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ExamSchedule]:
        """
        List all schedules for a specific exam.
        
        Ordered by date and start_time for chronological display.
        
        Args:
            db: Database session.
            exam_id: Exam UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of ExamSchedule ORM objects.
        """
        stmt = select(self.model).where(self.model.exam_id == exam_id)

        stmt = stmt.order_by(
            self.model.date.asc(),
            self.model.start_time.asc()
        )
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_class_section(
        self,
        db: Session,
        exam_id: UUID,
        class_id: UUID,
        section_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ExamSchedule]:
        """
        List schedules for a specific class and section within an exam.
        
        Useful for generating class-specific exam timetables.
        
        Args:
            db: Database session.
            exam_id: Exam UUID.
            class_id: Class UUID.
            section_id: Section UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of ExamSchedule ORM objects.
        """
        stmt = select(self.model).where(
            self.model.exam_id == exam_id,
            self.model.class_id == class_id,
            self.model.section_id == section_id
        )

        stmt = stmt.order_by(
            self.model.date.asc(),
            self.model.start_time.asc()
        )
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_schedule(
        self,
        db: Session,
        exam_id: UUID,
        class_id: UUID,
        section_id: UUID,
        subject_id: UUID
    ) -> Optional[ExamSchedule]:
        """
        Retrieve a specific schedule matching the unique constraint.
        
        Used to prevent duplicate schedules for the same combination.
        
        Args:
            db: Database session.
            exam_id: Exam UUID.
            class_id: Class UUID.
            section_id: Section UUID.
            subject_id: Subject UUID.
            
        Returns:
            ExamSchedule object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.exam_id == exam_id,
            self.model.class_id == class_id,
            self.model.section_id == section_id,
            self.model.subject_id == subject_id
        )

        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def list_published_by_exam(
        self,
        db: Session,
        exam_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ExamSchedule]:
        """
        List only published schedules for an exam.
        
        Useful for student-facing timetable views.
        
        Args:
            db: Database session.
            exam_id: Exam UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of published ExamSchedule ORM objects.
        """
        stmt = select(self.model).where(
            self.model.exam_id == exam_id,
            self.model.is_published.is_(True)
        )

        stmt = stmt.order_by(
            self.model.date.asc(),
            self.model.start_time.asc()
        )
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_schedule_locked(
        self,
        db: Session,
        exam_id: UUID,
        class_id: UUID,
        section_id: UUID,
        subject_id: UUID
    ) -> Optional[ExamSchedule]:
        """
        Retrieve a specific schedule with a row-level lock.
        
        Used when updating schedule details to prevent race conditions.
        
        Args:
            db: Database session.
            exam_id: Exam UUID.
            class_id: Class UUID.
            section_id: Section UUID.
            subject_id: Subject UUID.
            
        Returns:
            Locked ExamSchedule object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.exam_id == exam_id,
            self.model.class_id == class_id,
            self.model.section_id == section_id,
            self.model.subject_id == subject_id
        )

        stmt = stmt.with_for_update()
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return result.scalar_one_or_none()