# punch_log_repository.py



# academic/repositories/attendance.py

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select

from academic.models.attendance import StaffPunchLog

from repositories.base import BaseRepository
from types.types import PunchType


# =============================================================================
# STAFF PUNCH LOG REPOSITORY
# =============================================================================

class StaffPunchLogRepository(BaseRepository[StaffPunchLog]):
    """
    Repository for StaffPunchLog persistence operations.
    
    Extends BaseRepository as this model does not contain school_id directly.
    Tenant isolation is enforced upstream by validating staff_member_id ownership.
    
    Responsibilities:
    - Encapsulate punch log retrieval patterns.
    - Support date range queries for daily aggregation.
    - Filter by validation status and punch type.
    - Provide ordered retrieval for audit trails.
    
    Non-Responsibilities:
    - Tenant isolation (enforced upstream via staff validation).
    - Business logic (working hours calculation, daily status derivation).
    - Cross-domain joins to verify school ownership.
    - Soft-delete filtering (model does not support it).
    """

    def __init__(self):
        super().__init__(StaffPunchLog)

    def list_by_staff_and_date_range(
        self,
        db: Session,
        staff_member_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[StaffPunchLog]:
        """
        List punch logs for a staff member within a date range.
        
        Ordered by punch_time ascending for chronological audit trail.
        
        Args:
            db: Database session.
            staff_member_id: Staff member UUID.
            start_date: Range start datetime.
            end_date: Range end datetime.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of StaffPunchLog ORM objects.
        """
        stmt = select(self.model).where(
            self.model.staff_member_id == staff_member_id,
            self.model.punch_time >= start_date,
            self.model.punch_time <= end_date
        )

        stmt = stmt.order_by(self.model.punch_time.asc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_staff(
        self,
        db: Session,
        staff_member_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StaffPunchLog]:
        """
        List all punch logs for a staff member.
        
        Ordered by punch_time descending (most recent first).
        
        Args:
            db: Database session.
            staff_member_id: Staff member UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of StaffPunchLog ORM objects.
        """
        stmt = select(self.model).where(
            self.model.staff_member_id == staff_member_id
        )

        stmt = stmt.order_by(self.model.punch_time.desc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_latest_punch(
        self,
        db: Session,
        staff_member_id: UUID
    ) -> Optional[StaffPunchLog]:
        """
        Retrieve the most recent punch log for a staff member.
        
        Useful for determining current check-in/check-out status.
        
        Args:
            db: Database session.
            staff_member_id: Staff member UUID.
            
        Returns:
            Most recent StaffPunchLog object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.staff_member_id == staff_member_id
        )

        stmt = stmt.order_by(self.model.punch_time.desc()).limit(1)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def list_by_validation_status(
        self,
        db: Session,
        staff_member_id: UUID,
        is_valid: bool,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[StaffPunchLog]:
        """
        List punch logs filtered by validation status.
        
        Useful for reviewing invalid punches that need attention.
        
        Args:
            db: Database session.
            staff_member_id: Staff member UUID.
            is_valid: Boolean filter (True for valid, False for invalid).
            start_date: Optional date range start.
            end_date: Optional date range end.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of StaffPunchLog ORM objects.
        """
        stmt = select(self.model).where(
            self.model.staff_member_id == staff_member_id,
            self.model.is_valid == is_valid
        )

        if start_date:
            stmt = stmt.where(self.model.punch_time >= start_date)

        if end_date:
            stmt = stmt.where(self.model.punch_time <= end_date)

        stmt = stmt.order_by(self.model.punch_time.desc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_punch_type(
        self,
        db: Session,
        staff_member_id: UUID,
        punch_type: PunchType,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[StaffPunchLog]:
        """
        List punch logs filtered by punch type (CHECK_IN or CHECK_OUT).
        
        Useful for analyzing check-in/check-out patterns.
        
        Args:
            db: Database session.
            staff_member_id: Staff member UUID.
            punch_type: PunchType enum value.
            start_date: Optional date range start.
            end_date: Optional date range end.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of StaffPunchLog ORM objects.
        """
        stmt = select(self.model).where(
            self.model.staff_member_id == staff_member_id,
            self.model.punch_type == punch_type
        )

        if start_date:
            stmt = stmt.where(self.model.punch_time >= start_date)

        if end_date:
            stmt = stmt.where(self.model.punch_time <= end_date)

        stmt = stmt.order_by(self.model.punch_time.desc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_for_daily_aggregation(
        self,
        db: Session,
        staff_member_id: UUID,
        date: datetime
    ) -> List[StaffPunchLog]:
        """
        List all punch logs for a staff member on a specific date.
        
        Ordered by punch_time ascending for daily aggregation processing.
        
        Args:
            db: Database session.
            staff_member_id: Staff member UUID.
            date: Date to aggregate (datetime).
            
        Returns:
            List of StaffPunchLog ORM objects for the day.
        """
        # Use date truncation for matching (assuming date is midnight)
        from sqlalchemy import cast, Date
        
        
        stmt = select(self.model).where(
            self.model.staff_member_id == staff_member_id,
            cast(self.model.punch_time, Date) == cast(date, Date)
        )

        stmt = stmt.order_by(self.model.punch_time.asc())

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())


