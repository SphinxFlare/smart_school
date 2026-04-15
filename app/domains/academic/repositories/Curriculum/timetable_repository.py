# repositories/curriculum/timetable_repository.py


from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select

from academic.models.curriculum import ClassTimetable
from repositories.base import BaseRepository


# =============================================================================
# CLASS TIMETABLE REPOSITORY
# =============================================================================

class ClassTimetableRepository(BaseRepository[ClassTimetable]):
    """
    Repository for ClassTimetable persistence operations.
    
    Extends BaseRepository as this model does not contain school_id directly.
    Tenant isolation is enforced upstream by validating class_id/academic_year_id.
    
    Responsibilities:
    - Encapsulate timetable slot retrieval and listing.
    - Support ordered listing (day, period) for UI rendering.
    - Provide row-locking for concurrent slot modifications.
    - Apply soft-delete filtering consistently.
    
    Non-Responsibilities:
    - Tenant isolation (enforced upstream).
    - Business logic (conflict detection, teacher availability).
    - Cross-domain joins.
    """

    def __init__(self):
        super().__init__(ClassTimetable)

    def list_by_class_section(
        self,
        db: Session,
        class_id: UUID,
        section_id: UUID,
        academic_year_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ClassTimetable]:
        """
        Retrieve the full timetable for a specific class and section.
        
        Ordered by day_of_week and period_number for grid rendering.
        
        Args:
            db: Database session.
            class_id: The class UUID.
            section_id: The section UUID.
            academic_year_id: The academic year UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of ClassTimetable ORM objects.
        """
        stmt = select(self.model).where(
            self.model.class_id == class_id,
            self.model.section_id == section_id,
            self.model.academic_year_id == academic_year_id
        )

        stmt = stmt.order_by(
            self.model.day_of_week.asc(),
            self.model.period_number.asc()
        )
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_period_slot(
        self,
        db: Session,
        class_id: UUID,
        section_id: UUID,
        day_of_week: int,
        period_number: int,
        academic_year_id: UUID
    ) -> Optional[ClassTimetable]:
        """
        Retrieve a specific timetable slot.
        
        Matches the unique constraint (class, section, day, period, year).
        
        Args:
            db: Database session.
            class_id: The class UUID.
            section_id: The section UUID.
            day_of_week: Integer (0=Monday, etc.).
            period_number: Integer period index.
            academic_year_id: The academic year UUID.
            
        Returns:
            ClassTimetable object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.class_id == class_id,
            self.model.section_id == section_id,
            self.model.day_of_week == day_of_week,
            self.model.period_number == period_number,
            self.model.academic_year_id == academic_year_id
        )

        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_period_slot_locked(
        self,
        db: Session,
        class_id: UUID,
        section_id: UUID,
        day_of_week: int,
        period_number: int,
        academic_year_id: UUID
    ) -> Optional[ClassTimetable]:
        """
        Retrieve a specific timetable slot with a row-level lock.
        
        Used when updating or assigning a slot to prevent race conditions
        where two admins modify the same period simultaneously.
        
        Args:
            db: Database session.
            class_id: The class UUID.
            section_id: The section UUID.
            day_of_week: Integer (0=Monday, etc.).
            period_number: Integer period index.
            academic_year_id: The academic year UUID.
            
        Returns:
            Locked ClassTimetable object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.class_id == class_id,
            self.model.section_id == section_id,
            self.model.day_of_week == day_of_week,
            self.model.period_number == period_number,
            self.model.academic_year_id == academic_year_id
        )

        stmt = stmt.with_for_update()
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def list_by_teacher_assignment(
        self,
        db: Session,
        teacher_assignment_id: UUID,
        academic_year_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ClassTimetable]:
        """
        Retrieve all timetable slots assigned to a specific teacher assignment.
        
        Useful for generating a teacher's personal schedule.
        
        Args:
            db: Database session.
            teacher_assignment_id: The teacher assignment UUID.
            academic_year_id: The academic year UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of ClassTimetable ORM objects.
        """
        stmt = select(self.model).where(
            self.model.teacher_assignment_id == teacher_assignment_id,
            self.model.academic_year_id == academic_year_id
        )

        stmt = stmt.order_by(
            self.model.day_of_week.asc(),
            self.model.period_number.asc()
        )
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())