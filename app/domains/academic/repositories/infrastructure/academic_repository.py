# repositories/infrastructure/academic_repository.py


from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select

from academic.models.infrastructure import AcademicYear
from repositories.base import SchoolScopedRepository


# =============================================================================
# ACADEMIC YEAR REPOSITORY
# =============================================================================

class AcademicYearRepository(SchoolScopedRepository[AcademicYear]):
    """
    Repository for AcademicYear persistence operations.
    
    Extends SchoolScopedRepository to enforce tenant isolation (school_id)
    and soft-delete filtering.
    
    Responsibilities:
    - Lookup by school and year identifiers.
    - Retrieve current academic year for a school.
    - List years within date ranges.
    """

    def __init__(self):
        super().__init__(AcademicYear)

    def get_current_by_school(
        self,
        db: Session,
        school_id: UUID
    ) -> Optional[AcademicYear]:
        """
        Retrieve the current academic year for a school.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            
        Returns:
            AcademicYear object marked as current, else None.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.is_current.is_(True)
        )

        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def list_by_school(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[AcademicYear]:
        """
        List all academic years for a school.
        
        Ordered by start_date descending (most recent first).
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of AcademicYear ORM objects.
        """
        stmt = select(self.model).where(self.model.school_id == school_id)
        stmt = stmt.order_by(self.model.start_date.desc())
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_by_name_and_school(
        self,
        db: Session,
        school_id: UUID,
        name: str
    ) -> Optional[AcademicYear]:
        """
        Retrieve an academic year by name within a school.
        
        Useful for validation during year creation.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            name: Academic year name (e.g., "2025-2026").
            
        Returns:
            AcademicYear object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.name == name
        )

        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()