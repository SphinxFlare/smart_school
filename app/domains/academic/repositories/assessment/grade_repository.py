# academic/repositories/grade_repository.py


from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select

from academic.models.assessment import GradeScale

from repositories.base import SchoolScopedRepository


# =============================================================================
# GRADE SCALE REPOSITORY
# =============================================================================

class GradeScaleRepository(SchoolScopedRepository[GradeScale]):
    """
    Repository for GradeScale persistence operations.
    
    Extends SchoolScopedRepository to enforce tenant isolation (school_id).
    Note: This model does not have soft-delete fields.
    
    Responsibilities:
    - Encapsulate grade scale lookup patterns.
    - Support range-based grade lookup by percentage.
    - Provide ordered listing for grade policy display.
    
    Non-Responsibilities:
    - Business logic (grading policy decisions).
    - Transaction management.
    """

    def __init__(self):
        super().__init__(GradeScale)

    def list_by_school(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[GradeScale]:
        """
        List all grade scales for a school.
        
        Ordered by min_percentage ascending for policy display.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of GradeScale ORM objects.
        """
        stmt = select(self.model).where(self.model.school_id == school_id)

        stmt = stmt.order_by(self.model.min_percentage.asc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_by_grade_letter(
        self,
        db: Session,
        school_id: UUID,
        grade_letter
    ) -> Optional[GradeScale]:
        """
        Retrieve a grade scale by grade letter within a school.
        
        Enforces the unique constraint (school_id, grade_letter).
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            grade_letter: GradeLetter enum value.
            
        Returns:
            GradeScale object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.grade_letter == grade_letter
        )

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_percentage(
        self,
        db: Session,
        school_id: UUID,
        percentage: float
    ) -> Optional[GradeScale]:
        """
        Retrieve the grade scale matching a given percentage.
        
        Uses range-based lookup (min_percentage <= value <= max_percentage).
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            percentage: Percentage value to match.
            
        Returns:
            GradeScale object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.min_percentage <= percentage,
            self.model.max_percentage >= percentage
        )

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return result.scalar_one_or_none()