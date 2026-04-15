# repositories/curriculum/subject_repository.py


from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select

from academic.models.curriculum import Subject
from repositories.base import SchoolScopedRepository


# =============================================================================
# SUBJECT REPOSITORY
# =============================================================================

class SubjectRepository(SchoolScopedRepository[Subject]):
    """
    Repository for Subject persistence operations.
    
    Extends SchoolScopedRepository to enforce tenant isolation (school_id)
    and soft-delete filtering.
    
    Responsibilities:
    - Encapsulate subject lookup and listing patterns.
    - Ensure uniqueness checks (school_id, code) are supported.
    - Support active/inactive filtering.
    
    Non-Responsibilities:
    - Business logic (subject eligibility, curriculum mapping).
    - Transaction management.
    """

    def __init__(self):
        super().__init__(Subject)

    def get_by_code(
        self,
        db: Session,
        school_id: UUID,
        code: str
    ) -> Optional[Subject]:
        """
        Retrieve a subject by its unique code within a school.
        
        Enforces the unique constraint (school_id, code) at the lookup level.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            code: Unique subject code string.
            
        Returns:
            Subject object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.code == code
        )

        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def list_by_school(
        self,
        db: Session,
        school_id: UUID,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Subject]:
        """
        List subjects for a school with optional active status filtering.
        
        Ordered by name for predictable UI display.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            is_active: Filter by active status (None returns all).
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of Subject ORM objects.
        """
        stmt = select(self.model).where(self.model.school_id == school_id)

        if is_active is not None:
            stmt = stmt.where(self.model.is_active == is_active)

        stmt = stmt.order_by(self.model.name.asc())
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_active_by_school(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Subject]:
        """
        Convenience method to list only active subjects for a school.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of active Subject ORM objects.
        """
        return self.list_by_school(
            db, school_id, is_active=True, skip=skip, limit=limit
        )

