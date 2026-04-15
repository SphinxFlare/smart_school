# academic/repositories/rank_repository.py


from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select

from academic.models.assessment import StudentExamRank
from repositories.base import BaseRepository

# =============================================================================
# STUDENT EXAM RANK REPOSITORY
# =============================================================================

class StudentExamRankRepository(BaseRepository[StudentExamRank]):
    """
    Repository for StudentExamRank persistence operations.
    
    Extends BaseRepository as this model does not contain school_id directly.
    Tenant isolation is enforced upstream by validating exam_id ownership.
    
    Responsibilities:
    - Encapsulate rank lookup and listing patterns.
    - Support filtering by exam and rank_type.
    - Provide existence checks aligned with unique constraint.
    
    Non-Responsibilities:
    - Tenant isolation (enforced upstream via exam validation).
    - Business logic (rank calculation, position assignment).
    - Cross-domain joins to verify school ownership.
    """

    def __init__(self):
        super().__init__(StudentExamRank)

    def get_rank(
        self,
        db: Session,
        exam_id: UUID,
        student_id: UUID,
        rank_type
    ) -> Optional[StudentExamRank]:
        """
        Retrieve a rank entry matching the unique constraint.
        
        Used to prevent duplicate ranks for the same exam/student/type.
        
        Args:
            db: Database session.
            exam_id: Exam UUID.
            student_id: Student UUID.
            rank_type: RankType enum value.
            
        Returns:
            StudentExamRank object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.exam_id == exam_id,
            self.model.student_id == student_id,
            self.model.rank_type == rank_type
        )

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def list_by_exam_and_type(
        self,
        db: Session,
        exam_id: UUID,
        rank_type,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentExamRank]:
        """
        List all ranks for an exam filtered by rank type.
        
        Ordered by rank_position ascending for leaderboard display.
        
        Args:
            db: Database session.
            exam_id: Exam UUID.
            rank_type: RankType enum value.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of StudentExamRank ORM objects.
        """
        stmt = select(self.model).where(
            self.model.exam_id == exam_id,
            self.model.rank_type == rank_type
        )

        stmt = stmt.order_by(self.model.rank_position.asc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_exam(
        self,
        db: Session,
        exam_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentExamRank]:
        """
        List all ranks for an exam across all rank types.
        
        Ordered by rank_type then rank_position for grouped display.
        
        Args:
            db: Database session.
            exam_id: Exam UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of StudentExamRank ORM objects.
        """
        stmt = select(self.model).where(self.model.exam_id == exam_id)

        stmt = stmt.order_by(
            self.model.rank_type.asc(),
            self.model.rank_position.asc()
        )
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_student(
        self,
        db: Session,
        student_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentExamRank]:
        """
        List all ranks for a specific student across exams.
        
        Ordered by exam_id for historical view.
        
        Args:
            db: Database session.
            student_id: Student UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of StudentExamRank ORM objects.
        """
        stmt = select(self.model).where(self.model.student_id == student_id)

        stmt = stmt.order_by(self.model.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def exists_for_exam_and_type(
        self,
        db: Session,
        exam_id: UUID,
        rank_type
    ) -> bool:
        """
        Check if any ranks exist for an exam and rank type.
        
        Useful for determining if ranking has been computed.
        
        Args:
            db: Database session.
            exam_id: Exam UUID.
            rank_type: RankType enum value.
            
        Returns:
            Boolean indicating existence of ranks.
        """
        stmt = select(self.model.id).where(
            self.model.exam_id == exam_id,
            self.model.rank_type == rank_type
        ).limit(1)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None
