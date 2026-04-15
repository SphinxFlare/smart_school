# repositories/infrastructure/section_repository.py


from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select

from academic.models.infrastructure import Section

from repositories.base import BaseRepository


# =============================================================================
# SECTION REPOSITORY
# =============================================================================

class SectionRepository(BaseRepository[Section]):
    """
    Repository for Section persistence operations.
    
    Extends BaseRepository as Section does not contain school_id directly.
    Tenant isolation must be enforced upstream through class_id validation.
    
    Responsibilities:
    - Lookup sections by class.
    - Apply soft-delete filtering consistently.
    - Support section listing for class management.
    
    Note: Service layer must validate that class_id belongs to the 
    requesting school before calling these methods.
    """

    def __init__(self):
        super().__init__(Section)

    def list_by_class(
        self,
        db: Session,
        class_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Section]:
        """
        List all sections for a specific class.
        
        Args:
            db: Database session.
            class_id: Class UUID (tenant isolation enforced upstream).
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of Section ORM objects.
        """
        stmt = select(self.model).where(self.model.class_id == class_id)
        stmt = stmt.order_by(self.model.name.asc())
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_by_name_and_class(
        self,
        db: Session,
        class_id: UUID,
        name: str
    ) -> Optional[Section]:
        """
        Retrieve a section by name within a class.
        
        Useful for validation during section creation.
        
        Args:
            db: Database session.
            class_id: Class UUID (tenant isolation enforced upstream).
            name: Section name (e.g., "A", "B").
            
        Returns:
            Section object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.class_id == class_id,
            self.model.name == name
        )

        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def list_by_class_with_capacity(
        self,
        db: Session,
        class_id: UUID
    ) -> List[Section]:
        """
        List sections for a class with capacity information.
        
        Useful for enrollment capacity checks.
        
        Args:
            db: Database session.
            class_id: Class UUID (tenant isolation enforced upstream).
            
        Returns:
            List of Section ORM objects.
        """
        stmt = select(self.model).where(
            self.model.class_id == class_id,
            self.model.capacity.isnot(None)
        )

        stmt = stmt.order_by(self.model.name.asc())
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())