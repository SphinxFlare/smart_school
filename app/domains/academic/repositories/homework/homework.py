# academic/repositories/homework/homework.py

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from academic.models.assessment import Homework
from repositories.base import BaseRepository


class HomeworkRepository(BaseRepository[Homework]):
    """
    Repository for Homework persistence operations.
    
    Extends BaseRepository as this model does not contain school_id directly.
    Tenant isolation is enforced upstream by validating teacher_assignment_id 
    ownership (which links to class, section, subject, and academic_year).
    
    Responsibilities:
    - Encapsulate homework lookup and listing patterns.
    - Support filtering by teacher assignment, date ranges, and due date status.
    - Apply soft-delete filtering consistently (model has is_deleted).
    - Provide row-locking for safe concurrent modifications.
    - Ensure deterministic ordering for UI stability.
    - Support pagination with explicit offset/limit defaults.
    
    Non-Responsibilities:
    - Tenant isolation (enforced upstream via teacher_assignment validation).
    - Business logic (late detection, submission deadlines, access control).
    - Cross-domain joins to verify school ownership.
    - Transaction management (commit/rollback).
    - Computing submission statistics or grading state.
    
    Index Requirements (must exist at DB level):
    - ix_homework_teacher_assignment (teacher_assignment_id)
    - ix_homework_assigned_date (assigned_date)
    - ix_homework_due_date (due_date)
    """

    def __init__(self):
        super().__init__(Homework)

    def get_by_id(
        self,
        db: Session,
        homework_id: UUID
    ) -> Optional[Homework]:
        """
        Retrieve a homework by its ID with soft-delete awareness.
        
        Note: Tenant isolation must be validated upstream before calling.
        
        Args:
            db: Database session.
            homework_id: Homework UUID.
            
        Returns:
            Homework object if found and not deleted, else None.
        """
        stmt = select(self.model).where(self.model.id == homework_id)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_locked_for_update(
        self,
        db: Session,
        homework_id: UUID
    ) -> Optional[Homework]:
        """
        Retrieve a homework with a row-level lock for safe updates.
        
        Prevents race conditions when modifying homework details
        (e.g., due date, max_marks, attachments) while submissions 
        are being made or graded.
        
        Args:
            db: Database session.
            homework_id: Homework UUID.
            
        Returns:
            Locked Homework object if found and not deleted, else None.
        """
        stmt = select(self.model).where(self.model.id == homework_id)
        stmt = stmt.with_for_update()
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def list_by_teacher_assignment(
        self,
        db: Session,
        teacher_assignment_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Homework]:
        """
        List all homework assignments for a specific teacher assignment.
        
        Ordered by assigned_date descending for teacher dashboard view
        (most recently assigned first).
        
        Args:
            db: Database session.
            teacher_assignment_id: Teacher assignment UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of Homework ORM objects.
        """
        stmt = select(self.model).where(
            self.model.teacher_assignment_id == teacher_assignment_id
        )

        stmt = stmt.order_by(self.model.assigned_date.desc())
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_due_date_range(
        self,
        db: Session,
        teacher_assignment_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[Homework]:
        """
        List homework assignments with due dates within a specific range.
        
        Uses range comparisons to preserve index usage on due_date.
        Ordered by due_date ascending for student view (earliest deadlines first).
        
        Args:
            db: Database session.
            teacher_assignment_id: Teacher assignment UUID.
            start_date: Range start datetime (inclusive).
            end_date: Range end datetime (inclusive).
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of Homework ORM objects.
        """
        stmt = select(self.model).where(
            self.model.teacher_assignment_id == teacher_assignment_id,
            self.model.due_date >= start_date,
            self.model.due_date <= end_date
        )

        stmt = stmt.order_by(self.model.due_date.asc())
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_assigned_date_range(
        self,
        db: Session,
        teacher_assignment_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[Homework]:
        """
        List homework assignments created within a specific date range.
        
        Uses range comparisons to preserve index usage on assigned_date.
        Ordered by assigned_date descending for chronological view.
        
        Args:
            db: Database session.
            teacher_assignment_id: Teacher assignment UUID.
            start_date: Range start datetime (inclusive).
            end_date: Range end datetime (inclusive).
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of Homework ORM objects.
        """
        stmt = select(self.model).where(
            self.model.teacher_assignment_id == teacher_assignment_id,
            self.model.assigned_date >= start_date,
            self.model.assigned_date <= end_date
        )

        stmt = stmt.order_by(self.model.assigned_date.desc())
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_overdue(
        self,
        db: Session,
        teacher_assignment_id: UUID,
        reference_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[Homework]:
        """
        List homework assignments that are overdue relative to a reference date.
        
        Purely date-based filtering (due_date < reference_date).
        No status logic, late-detection policy, or submission state considered.
        
        Args:
            db: Database session.
            teacher_assignment_id: Teacher assignment UUID.
            reference_date: Date to compare against (typically now).
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of Homework ORM objects with due_date before reference.
        """
        stmt = select(self.model).where(
            self.model.teacher_assignment_id == teacher_assignment_id,
            self.model.due_date < reference_date
        )

        stmt = stmt.order_by(self.model.due_date.asc())
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_upcoming(
        self,
        db: Session,
        teacher_assignment_id: UUID,
        reference_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[Homework]:
        """
        List homework assignments that are upcoming or current relative to a reference date.
        
        Purely date-based filtering (due_date >= reference_date).
        No status logic or completion state considered.
        
        Args:
            db: Database session.
            teacher_assignment_id: Teacher assignment UUID.
            reference_date: Date to compare against (typically now).
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of Homework ORM objects with due_date at or after reference.
        """
        stmt = select(self.model).where(
            self.model.teacher_assignment_id == teacher_assignment_id,
            self.model.due_date >= reference_date
        )

        stmt = stmt.order_by(self.model.due_date.asc())
        stmt = stmt.offset(skip).limit(limit)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def count_by_teacher_assignment(
        self,
        db: Session,
        teacher_assignment_id: UUID
    ) -> int:
        """
        Count total active homework assignments for a teacher assignment.
        
        Args:
            db: Database session.
            teacher_assignment_id: Teacher assignment UUID.
            
        Returns:
            Count of active (non-deleted) homework assignments.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.teacher_assignment_id == teacher_assignment_id
        )

        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_overdue(
        self,
        db: Session,
        teacher_assignment_id: UUID,
        reference_date: datetime
    ) -> int:
        """
        Count overdue homework assignments for a teacher assignment.
        
        Purely date-based counting (due_date < reference_date).
        
        Args:
            db: Database session.
            teacher_assignment_id: Teacher assignment UUID.
            reference_date: Date to compare against (typically now).
            
        Returns:
            Count of overdue homework assignments.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.teacher_assignment_id == teacher_assignment_id,
            self.model.due_date < reference_date
        )

        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_upcoming(
        self,
        db: Session,
        teacher_assignment_id: UUID,
        reference_date: datetime
    ) -> int:
        """
        Count upcoming homework assignments for a teacher assignment.
        
        Purely date-based counting (due_date >= reference_date).
        
        Args:
            db: Database session.
            teacher_assignment_id: Teacher assignment UUID.
            reference_date: Date to compare against (typically now).
            
        Returns:
            Count of upcoming homework assignments.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.teacher_assignment_id == teacher_assignment_id,
            self.model.due_date >= reference_date
        )

        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0