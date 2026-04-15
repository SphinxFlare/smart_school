# welfare/repositories/wellness/wellness_check_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from repositories.base import BaseRepository
from welfare.models.wellness import WellnessCheck


class WellnessCheckRepository(BaseRepository[WellnessCheck]):
    """
    Repository for WellnessCheck model operations.
    Extends BaseRepository - model does NOT contain school_id.
    Tenant isolation enforced through student_id/counselor_id scoping at service layer.
    Soft-delete aware (WellnessCheck model has is_deleted).
    Zero business logic, zero validation, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(WellnessCheck)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        check_id: UUID
    ) -> Optional[WellnessCheck]:
        """
        Retrieve wellness check by ID.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(self.model.id == check_id)
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
    ) -> List[WellnessCheck]:
        """
        List wellness checks for a student.
        Deterministic ordering: check_date DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(self.model.student_id == student_id)
            .order_by(
                self.model.check_date.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_counselor(
        self,
        db: Session,
        counselor_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[WellnessCheck]:
        """
        List wellness checks by a counselor.
        Deterministic ordering: check_date DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(self.model.counselor_id == counselor_id)
            .order_by(
                self.model.check_date.desc(),
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
    ) -> List[WellnessCheck]:
        """
        List wellness checks within date range for a student.
        Index-friendly filtering on check_date.
        Deterministic ordering: check_date DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.student_id == student_id,
                self.model.check_date >= start_date,
                self.model.check_date <= end_date
            )
            .order_by(
                self.model.check_date.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_requiring_follow_up(
        self,
        db: Session,
        counselor_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[WellnessCheck]:
        """
        List wellness checks requiring follow-up.
        Deterministic ordering: follow_up_date ASC, id ASC.
        Soft-delete filtered.
        """
        stmt = select(self.model).where(
            self.model.follow_up_required.is_(True)
        )
        
        if counselor_id:
            stmt = stmt.where(self.model.counselor_id == counselor_id)
        
        stmt = (
            stmt.order_by(
                self.model.follow_up_date.asc().nulls_last(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_upcoming_follow_ups(
        self,
        db: Session,
        reference_date: datetime,
        counselor_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[WellnessCheck]:
        """
        List wellness checks with upcoming follow-ups.
        follow_up_date >= reference_date and follow_up_required = True.
        Deterministic ordering: follow_up_date ASC, id ASC.
        Soft-delete filtered.
        """
        stmt = select(self.model).where(
            self.model.follow_up_required.is_(True),
            self.model.follow_up_date >= reference_date,
            self.model.follow_up_date.is_not(None)
        )
        
        if counselor_id:
            stmt = stmt.where(self.model.counselor_id == counselor_id)
        
        stmt = (
            stmt.order_by(
                self.model.follow_up_date.asc(),
                self.model.id.asc()
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
    ) -> List[WellnessCheck]:
        """
        List soft-deleted wellness checks.
        Does NOT apply soft-delete filter (explicitly includes deleted).
        Deterministic ordering: check_date DESC, id DESC.
        """
        stmt = select(self.model).where(
            self.model.is_deleted.is_(True)
        )
        
        if student_id:
            stmt = stmt.where(self.model.student_id == student_id)
        
        stmt = (
            stmt.order_by(
                self.model.check_date.desc(),
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
        check_id: UUID
    ) -> Optional[WellnessCheck]:
        """
        Lock wellness check for update.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(self.model.id == check_id)
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_by_student_and_date_for_update(
        self,
        db: Session,
        student_id: UUID,
        check_date: datetime
    ) -> List[WellnessCheck]:
        """
        Lock all wellness checks for a student on a specific date.
        Used for batch operations.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.student_id == student_id,
                self.model.check_date == check_date
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def lock_follow_up_for_update(
        self,
        db: Session,
        check_id: UUID
    ) -> Optional[WellnessCheck]:
        """
        Lock wellness check for follow-up update operations.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == check_id,
                self.model.follow_up_required.is_(True)
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Existence Checks
    # -----------------------------------------

    def exists_by_id(
        self,
        db: Session,
        check_id: UUID
    ) -> bool:
        """
        Efficient existence check for wellness check by ID.
        Soft-delete filtered.
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(self.model.id == check_id)
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
        Count wellness checks for a student.
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

    def count_by_counselor(
        self,
        db: Session,
        counselor_id: UUID
    ) -> int:
        """
        Count wellness checks by a counselor.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.counselor_id == counselor_id)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_requiring_follow_up(
        self,
        db: Session,
        counselor_id: Optional[UUID] = None
    ) -> int:
        """
        Count wellness checks requiring follow-up.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.follow_up_required.is_(True)
        )
        
        if counselor_id:
            stmt = stmt.where(self.model.counselor_id == counselor_id)
        
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_upcoming_follow_ups(
        self,
        db: Session,
        reference_date: datetime,
        counselor_id: Optional[UUID] = None
    ) -> int:
        """
        Count wellness checks with upcoming follow-ups.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.follow_up_required.is_(True),
            self.model.follow_up_date >= reference_date,
            self.model.follow_up_date.is_not(None)
        )
        
        if counselor_id:
            stmt = stmt.where(self.model.counselor_id == counselor_id)
        
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_deleted(
        self,
        db: Session,
        student_id: Optional[UUID] = None
    ) -> int:
        """
        Count soft-deleted wellness checks.
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

    def get_average_wellness_scores(
        self,
        db: Session,
        student_id: UUID
    ) -> Dict[str, Optional[float]]:
        """
        Get average wellness scores for a student.
        Null-safe aggregation for each dimension.
        Soft-delete filtered.
        Returns dict with academic, emotional, social, physical averages.
        """
        stmt = (
            select(
                func.avg(self.model.academic_wellness),
                func.avg(self.model.emotional_wellness),
                func.avg(self.model.social_wellness),
                func.avg(self.model.physical_wellness)
            )
            .where(self.model.student_id == student_id)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        row = result.first()
        
        return {
            'academic': float(row[0]) if row[0] is not None else None,
            'emotional': float(row[1]) if row[1] is not None else None,
            'social': float(row[2]) if row[2] is not None else None,
            'physical': float(row[3]) if row[3] is not None else None
        }

    # -----------------------------------------
    # Soft Delete Operations
    # -----------------------------------------

    def soft_delete(
        self,
        db: Session,
        check_id: UUID
    ) -> bool:
        """
        Soft delete wellness check record.
        Returns True if successful.
        """
        stmt = (
            select(self.model)
            .where(self.model.id == check_id)
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        check = result.scalar_one_or_none()

        if check:
            check.is_deleted = True
            db.flush()
            return True
        return False


    def restore(
        self,
        db: Session,
        check_id: UUID
    ) -> bool:
        """
        Restore soft-deleted wellness check record.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == check_id,
                self.model.is_deleted.is_(True)
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        check = result.scalar_one_or_none()

        if check:
            check.is_deleted = False
            db.flush()
            return True
        return False

    # -----------------------------------------
    # Bulk Operations (Atomic, Empty Guards)
    # -----------------------------------------

    def bulk_update_follow_up(
        self,
        db: Session,
        check_ids: List[UUID],
        follow_up_required: bool,
        follow_up_date: Optional[datetime] = None
    ) -> int:
        """
        Bulk update follow-up status for multiple wellness checks.
        Atomic update statement.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not check_ids:
            return 0

        values = {'follow_up_required': follow_up_required}
        if follow_up_date is not None:
            values['follow_up_date'] = follow_up_date

        stmt = (
            update(self.model)
            .where(
                self.model.id.in_(check_ids),
                self.model.is_deleted.is_(False)
            )
            .values(**values)
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
        Bulk update wellness checks for a student.
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

    def bulk_update_by_counselor(
        self,
        db: Session,
        counselor_id: UUID,
        updates: Dict[str, Any]
    ) -> int:
        """
        Bulk update wellness checks by a counselor.
        Atomic update statement scoped by counselor_id.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not updates:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.counselor_id == counselor_id,
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
        Bulk soft delete all wellness checks for a student.
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
        Bulk restore all soft-deleted wellness checks for a student.
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