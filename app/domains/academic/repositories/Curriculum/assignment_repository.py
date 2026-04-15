# repositories/curriculum/assignment_repository.py


from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select

from academic.models.curriculum import TeacherAssignment

from repositories.base import BaseRepository


# =============================================================================
# TEACHER ASSIGNMENT REPOSITORY
# =============================================================================

class TeacherAssignmentRepository(BaseRepository[TeacherAssignment]):
    """
    Repository for TeacherAssignment persistence operations.
    
    Extends BaseRepository as this model does not contain school_id directly.
    Tenant isolation is enforced upstream by validating class_id/academic_year_id.
    
    Responsibilities:
    - Encapsulate assignment lookup patterns (by staff, by class, by year).
    - Support existence checks for unique constraint validation.
    - Apply soft-delete filtering consistently.
    
    Non-Responsibilities:
    - Tenant isolation (enforced upstream via class/year validation).
    - Business logic (workload limits, conflict detection).
    - Cross-domain joins to verify school ownership.
    """

    def __init__(self):
        super().__init__(TeacherAssignment)

    def list_by_staff(
        self,
        db: Session,
        staff_member_id: UUID,
        academic_year_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[TeacherAssignment]:
        """
        Retrieve all assignments for a specific staff member in an academic year.
        
        Args:
            db: Database session.
            staff_member_id: The staff member's UUID.
            academic_year_id: The academic year UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of TeacherAssignment ORM objects.
        """
        stmt = select(self.model).where(
            self.model.staff_member_id == staff_member_id,
            self.model.academic_year_id == academic_year_id
        )

        stmt = stmt.order_by(self.model.subject_id.asc())
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_class_section(
        self,
        db: Session,
        class_id: UUID,
        section_id: UUID,
        academic_year_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[TeacherAssignment]:
        """
        Retrieve all teacher assignments for a specific class and section.
        
        Useful for displaying the teacher list for a class.
        
        Args:
            db: Database session.
            class_id: The class UUID.
            section_id: The section UUID.
            academic_year_id: The academic year UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of TeacherAssignment ORM objects.
        """
        stmt = select(self.model).where(
            self.model.class_id == class_id,
            self.model.section_id == section_id,
            self.model.academic_year_id == academic_year_id
        )

        stmt = stmt.order_by(self.model.subject_id.asc())
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_assignment(
        self,
        db: Session,
        staff_member_id: UUID,
        class_id: UUID,
        section_id: UUID,
        subject_id: UUID,
        academic_year_id: UUID
    ) -> Optional[TeacherAssignment]:
        """
        Retrieve a specific assignment matching the unique constraint.
        
        Used to prevent duplicate assignments for the same combination.
        
        Args:
            db: Database session.
            staff_member_id: The staff member's UUID.
            class_id: The class UUID.
            section_id: The section UUID.
            subject_id: The subject UUID.
            academic_year_id: The academic year UUID.
            
        Returns:
            TeacherAssignment object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.staff_member_id == staff_member_id,
            self.model.class_id == class_id,
            self.model.section_id == section_id,
            self.model.subject_id == subject_id,
            self.model.academic_year_id == academic_year_id
        )

        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def list_by_academic_year(
        self,
        db: Session,
        academic_year_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[TeacherAssignment]:
        """
        Retrieve all assignments for an academic year.
        
        Args:
            db: Database session.
            academic_year_id: The academic year UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of TeacherAssignment ORM objects.
        """
        stmt = select(self.model).where(
            self.model.academic_year_id == academic_year_id
        )

        stmt = stmt.order_by(self.model.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())

