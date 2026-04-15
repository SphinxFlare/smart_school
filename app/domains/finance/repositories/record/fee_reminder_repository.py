# finance/repositories/record/fee_reminder_repository.py


from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update
from sqlalchemy.dialects.postgresql import JSONB

from repositories.base import SchoolScopedRepository
from finance.models.record import FeeReminder


class FeeReminderRepository(SchoolScopedRepository[FeeReminder]):
    """
    Repository for FeeReminder model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    NO soft-delete logic (model lacks is_deleted).
    Focus on reminder scheduling persistence only.
    Zero scheduling engine logic, zero notification dispatch logic.
    """

    def __init__(self):
        super().__init__(FeeReminder)

    # -----------------------------------------
    # Listing by Association
    # -----------------------------------------

    def list_by_student_fee(
        self,
        db: Session,
        school_id: UUID,
        student_fee_id: UUID,
        order_by_upcoming: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeeReminder]:
        """
        List reminders by student fee record within school tenant.
        Deterministic ordering:
        - order_by_upcoming=True: reminder_date ASC, id ASC
        - order_by_upcoming=False: created_at DESC, id DESC
        NO soft-delete filter (model lacks is_deleted).
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.student_fee_id == student_fee_id
        )

        if order_by_upcoming:
            stmt = stmt.order_by(
                self.model.reminder_date.asc(),
                self.model.id.asc()
            )
        else:
            stmt = stmt.order_by(
                self.model.created_at.desc(),
                self.model.id.desc()
            )

        stmt = stmt.offset(skip).limit(limit)
        # NO soft-delete filter (model lacks is_deleted)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        order_by_upcoming: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeeReminder]:
        """
        List reminders by student within school tenant.
        Deterministic ordering.
        NO soft-delete filter.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.student_id == student_id
        )

        if order_by_upcoming:
            stmt = stmt.order_by(
                self.model.reminder_date.asc(),
                self.model.id.asc()
            )
        else:
            stmt = stmt.order_by(
                self.model.created_at.desc(),
                self.model.id.desc()
            )

        stmt = stmt.offset(skip).limit(limit)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Filtering
    # -----------------------------------------

    def filter_by_date_range(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeeReminder]:
        """
        Filter reminders by reminder_date range within school tenant.
        Index-friendly filtering (no functions on column).
        Uses index on reminder_date.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id,
                self.model.reminder_date >= start_date,
                self.model.reminder_date <= end_date
            )
            .order_by(
                self.model.reminder_date.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def filter_by_date_range_school_wide(
        self,
        db: Session,
        school_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeeReminder]:
        """
        Filter reminders by reminder_date range across all students in school.
        Index-friendly filtering.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.reminder_date >= start_date,
                self.model.reminder_date <= end_date
            )
            .order_by(
                self.model.reminder_date.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def filter_by_is_sent(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        is_sent: bool,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeeReminder]:
        """
        Filter reminders by sent status within school tenant.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id,
                self.model.is_sent.is_(is_sent)
            )
            .order_by(
                self.model.reminder_date.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def filter_by_is_sent_school_wide(
        self,
        db: Session,
        school_id: UUID,
        is_sent: bool,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeeReminder]:
        """
        Filter reminders by sent status across all students in school.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.is_sent.is_(is_sent)
            )
            .order_by(
                self.model.reminder_date.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def filter_by_parent_ids(
        self,
        db: Session,
        school_id: UUID,
        parent_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeeReminder]:
        """
        Filter reminders by parent ID containment in JSONB sent_to_parent_ids.
        Uses JSONB containment operator.
        Tenant-safe with school_id filter.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.sent_to_parent_ids.cast(JSONB).contains([str(parent_id)])
            )
            .order_by(
                self.model.reminder_date.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def filter_by_reminder_type(
        self,
        db: Session,
        school_id: UUID,
        reminder_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeeReminder]:
        """
        Filter reminders by reminder_type within school tenant.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.reminder_type == reminder_type
            )
            .order_by(
                self.model.reminder_date.asc(),
                self.model.id.asc()
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
        school_id: UUID,
        reminder_id: UUID
    ) -> Optional[FeeReminder]:
        """
        Lock reminder for update (marking as sent).
        Scoped to school_id for tenant safety.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == reminder_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        # NO soft-delete filter
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_for_update_student_scoped(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        reminder_id: UUID
    ) -> Optional[FeeReminder]:
        """
        Lock reminder for update scoped to school and student.
        Maximum concurrency safety.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == reminder_id,
                self.model.school_id == school_id,
                self.model.student_id == student_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_by_student_fee_for_update(
        self,
        db: Session,
        school_id: UUID,
        student_fee_id: UUID
    ) -> Optional[FeeReminder]:
        """
        Lock reminder by student_fee_id for update.
        Tenant-safe locking.
        NO soft-delete filter.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_fee_id == student_fee_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Bulk Updates
    # -----------------------------------------

    def bulk_mark_as_sent(
        self,
        db: Session,
        school_id: UUID,
        reminder_ids: List[UUID],
        sent_at: datetime
    ) -> int:
        """
        Bulk mark reminders as sent.
        Atomic update statement scoped by school_id.
        Returns count of updated rows.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(reminder_ids),
                self.model.is_sent.is_(False)
            )
            .values(is_sent=True, sent_at=sent_at)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_mark_as_sent_by_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        sent_at: datetime
    ) -> int:
        """
        Bulk mark all unsent reminders for a student as sent.
        Atomic update statement scoped by school and student.
        Returns count of updated rows.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id,
                self.model.is_sent.is_(False)
            )
            .values(is_sent=True, sent_at=sent_at)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_create_reminders(
        self,
        db: Session,
        school_id: UUID,
        reminders: List[FeeReminder]
    ) -> List[FeeReminder]:
        """
        Bulk create reminders with enforced tenant integrity.
        Ensures every reminder belongs to provided school_id.
        Returns created objects.
        """

        if not reminders:
            return []

        for reminder in reminders:
            if reminder.school_id != school_id:
                raise ValueError("Tenant mismatch: reminder.school_id does not match provided school_id")
            db.add(reminder)

        db.flush()
        return reminders

    # -----------------------------------------
    # Aggregations (Null-Safe)
    # -----------------------------------------

    def count_unsent(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID
    ) -> int:
        """
        Count unsent reminders for a student within school.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id,
                self.model.is_sent.is_(False)
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_unsent_school_wide(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count unsent reminders across all students in school.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.is_sent.is_(False)
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_student_fee(
        self,
        db: Session,
        school_id: UUID,
        student_fee_id: UUID
    ) -> int:
        """
        Count total reminders for a student fee record within school.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.student_fee_id == student_fee_id
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID
    ) -> int:
        """
        Count total reminders for a student within school.
        Null-safe aggregation.
        NO soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.student_id == student_id
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0