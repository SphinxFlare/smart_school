# welfare/repositories/wellness/student_observation_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from repositories.base import BaseRepository
from welfare.models.wellness import StudentObservation


class StudentObservationRepository(BaseRepository[StudentObservation]):
    """
    Repository for StudentObservation model operations.
    Extends BaseRepository - model does NOT contain school_id.
    Tenant isolation enforced through student_id/teacher_id scoping at service layer.
    Soft-delete aware (StudentObservation model has is_deleted).
    Zero business logic, zero validation, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(StudentObservation)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        observation_id: UUID
    ) -> Optional[StudentObservation]:
        """
        Retrieve observation by ID.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(self.model.id == observation_id)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Listing Methods
    # -----------------------------------------

    def list_by_student(
        self,
        db: Session,
        student_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentObservation]:
        """
        List observations for a student.
        Deterministic ordering: observation_date DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(self.model.student_id == student_id)
            .order_by(
                self.model.observation_date.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_teacher(
        self,
        db: Session,
        teacher_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentObservation]:
        """
        List observations by a teacher.
        Deterministic ordering: observation_date DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(self.model.teacher_id == teacher_id)
            .order_by(
                self.model.observation_date.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_class(
        self,
        db: Session,
        class_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentObservation]:
        """
        List observations for a class.
        Deterministic ordering: observation_date DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(self.model.class_id == class_id)
            .order_by(
                self.model.observation_date.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_category(
        self,
        db: Session,
        student_id: UUID,
        category: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentObservation]:
        """
        List observations by category for a student.
        Uses index on category.
        Deterministic ordering: observation_date DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.student_id == student_id,
                self.model.category == category
            )
            .order_by(
                self.model.observation_date.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_date_range(
        self,
        db: Session,
        student_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentObservation]:
        """
        List observations within date range for a student.
        Index-friendly filtering on observation_date.
        Deterministic ordering: observation_date DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.student_id == student_id,
                self.model.observation_date >= start_date,
                self.model.observation_date <= end_date
            )
            .order_by(
                self.model.observation_date.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_shared_with_parents(
        self,
        db: Session,
        student_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentObservation]:
        """
        List observations shared with parents for a student.
        Deterministic ordering: observation_date DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.student_id == student_id,
                self.model.shared_with_parents.is_(True)
            )
            .order_by(
                self.model.observation_date.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_deleted(
        self,
        db: Session,
        student_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentObservation]:
        """
        List soft-deleted observations.
        Does NOT apply soft-delete filter (explicitly includes deleted).
        Deterministic ordering: observation_date DESC, id DESC.
        """
        stmt = select(self.model).where(
            self.model.is_deleted.is_(True)
        )
        
        if student_id:
            stmt = stmt.where(self.model.student_id == student_id)
        
        stmt = (
            stmt.order_by(
                self.model.observation_date.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Row Locking
    # -----------------------------------------

    def lock_for_update(
        self,
        db: Session,
        observation_id: UUID
    ) -> Optional[StudentObservation]:
        """
        Lock observation for update.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(self.model.id == observation_id)
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()


    def lock_by_student_and_date_for_update(
        self,
        db: Session,
        student_id: UUID,
        observation_date: datetime
    ) -> List[StudentObservation]:
        """
        Lock all observations for a student on a specific date.
        Used for batch operations.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.student_id == student_id,
                self.model.observation_date == observation_date
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Existence Checks
    # -----------------------------------------

    def exists_by_id(
        self,
        db: Session,
        observation_id: UUID
    ) -> bool:
        """
        Efficient existence check for observation by ID.
        Soft-delete filtered.
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(self.model.id == observation_id)
            .limit(1)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    # -----------------------------------------
    # Aggregations (Null-Safe)
    # -----------------------------------------

    def count_by_student(
        self,
        db: Session,
        student_id: UUID
    ) -> int:
        """
        Count observations for a student.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.student_id == student_id)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_teacher(
        self,
        db: Session,
        teacher_id: UUID
    ) -> int:
        """
        Count observations by a teacher.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.teacher_id == teacher_id)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_category(
        self,
        db: Session,
        student_id: UUID,
        category: str
    ) -> int:
        """
        Count observations by category for a student.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.student_id == student_id,
                self.model.category == category
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_shared_with_parents(
        self,
        db: Session,
        student_id: UUID
    ) -> int:
        """
        Count observations shared with parents for a student.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.student_id == student_id,
                self.model.shared_with_parents.is_(True)
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_deleted(
        self,
        db: Session,
        student_id: Optional[UUID] = None
    ) -> int:
        """
        Count soft-deleted observations.
        Null-safe aggregation.
        Does NOT apply soft-delete filter.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.is_deleted.is_(True)
        )
        
        if student_id:
            stmt = stmt.where(self.model.student_id == student_id)
        
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # Soft Delete Operations
    # -----------------------------------------

    def soft_delete(
        self,
        db: Session,
        observation_id: UUID
    ) -> bool:
        """
        Soft delete observation record.
        Returns True if successful.
        """
        stmt = (
            select(self.model)
            .where(self.model.id == observation_id)
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        observation = result.scalar_one_or_none()

        if observation:
            observation.is_deleted = True
            db.flush()
            return True
        return False
    

    def restore(
        self,
        db: Session,
        observation_id: UUID
    ) -> bool:
        """
        Restore soft-deleted observation record.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == observation_id,
                self.model.is_deleted.is_(True)
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        observation = result.scalar_one_or_none()

        if observation:
            observation.is_deleted = False
            db.flush()
            return True
        return False

    # -----------------------------------------
    # Bulk Operations (Atomic, Empty Guards)
    # -----------------------------------------

    def bulk_update_shared_status(
        self,
        db: Session,
        observation_ids: List[UUID],
        shared_with_parents: bool
    ) -> int:
        """
        Bulk update shared_with_parents for multiple observations.
        Atomic update statement.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not observation_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.id.in_(observation_ids),
                self.model.is_deleted.is_(False)
            )
            .values(shared_with_parents=shared_with_parents)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_by_student(
        self,
        db: Session,
        student_id: UUID,
        updates: Dict[str, Any]
    ) -> int:
        """
        Bulk update observations for a student.
        Atomic update statement scoped by student_id.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not updates:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.student_id == student_id,
                self.model.is_deleted.is_(False)
            )
            .values(**updates)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_soft_delete_by_student(
        self,
        db: Session,
        student_id: UUID
    ) -> int:
        """
        Bulk soft delete all observations for a student.
        Atomic update statement scoped by student_id.
        Returns count of updated rows.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.student_id == student_id,
                self.model.is_deleted.is_(False)
            )
            .values(is_deleted=True)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_restore_by_student(
        self,
        db: Session,
        student_id: UUID
    ) -> int:
        """
        Bulk restore all soft-deleted observations for a student.
        Atomic update statement scoped by student_id.
        Returns count of updated rows.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.student_id == student_id,
                self.model.is_deleted.is_(True)
            )
            .values(is_deleted=False)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0