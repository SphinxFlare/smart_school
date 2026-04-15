# repositories/infrastructure/class_repository.py



from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select

from academic.models.infrastructure import Class

from repositories.base import SchoolScopedRepository


# =============================================================================
# CLASS REPOSITORY
# =============================================================================

class ClassRepository(SchoolScopedRepository[Class]):
    """
    Repository for Class persistence operations.
    
    Extends SchoolScopedRepository to enforce tenant isolation (school_id)
    and soft-delete filtering.
    
    Responsibilities:
    - Lookup by school and academic year.
    - Ordered listing by level for display.
    - Support class hierarchy queries.
    """

    def __init__(self):
        super().__init__(Class)

    def list_by_school_and_year(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Class]:
        """
        List all classes for a school within an academic year.
        
        Ordered by level ascending for proper grade ordering.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            academic_year_id: Academic year UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of Class ORM objects.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.academic_year_id == academic_year_id
        )

        stmt = stmt.order_by(self.model.level.asc())
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_by_name_and_school(
        self,
        db: Session,
        school_id: UUID,
        name: str,
        academic_year_id: UUID
    ) -> Optional[Class]:
        """
        Retrieve a class by name within a school and academic year.
        
        Useful for validation during class creation.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            name: Class name (e.g., "Grade 1").
            academic_year_id: Academic year UUID.
            
        Returns:
            Class object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.name == name,
            self.model.academic_year_id == academic_year_id
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
    ) -> List[Class]:
        """
        List all classes for a school across all academic years.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of Class ORM objects.
        """
        stmt = select(self.model).where(self.model.school_id == school_id)
        stmt = stmt.order_by(self.model.academic_year_id.desc(), self.model.level.asc())
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())
