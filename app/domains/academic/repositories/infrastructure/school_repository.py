# repositories/infrastructure/school_repository.py


from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select

from academic.models.infrastructure import School
from repositories.base import SchoolScopedRepository


# =============================================================================
# SCHOOL REPOSITORY
# =============================================================================

class SchoolRepository(SchoolScopedRepository[School]):
    """
    Repository for School persistence operations.
    
    Note: School is the tenant root entity. school_id filtering is 
    inherently satisfied by the entity's own id.
    
    Responsibilities:
    - Lookup by unique code (tenant routing).
    - List active schools.
    - Apply soft-delete filtering consistently.
    """

    def __init__(self):
        super().__init__(School)

    def get_by_code(self, db: Session, code: str) -> Optional[School]:
        """
        Retrieve a school by its unique code.
        
        Used for tenant routing during request initialization.
        
        Args:
            db: Database session.
            code: Unique school code string.
            
        Returns:
            School object if found, else None.
        """
        stmt = select(self.model).where(self.model.code == code)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def list_active(self, db: Session, skip: int = 0, limit: int = 100) -> List[School]:
        """
        List all active (non-deleted) schools.
        
        Args:
            db: Database session.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of School ORM objects.
        """
        stmt = select(self.model).where(self.model.is_active.is_(True))
        stmt = self._apply_soft_delete_filter(stmt)
        stmt = stmt.order_by(self.model.name.asc())
        stmt = stmt.offset(skip).limit(limit)

        result = db.execute(stmt)
        return list(result.scalars().all())