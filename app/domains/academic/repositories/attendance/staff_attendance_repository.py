# staff_attendance_repository.py


from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from academic.models.attendance import StaffAttendance

from repositories.base import BaseRepository
from types.types import StaffAttendanceStatus


# =============================================================================
# STAFF ATTENDANCE REPOSITORY
# =============================================================================

class StaffAttendanceRepository(BaseRepository[StaffAttendance]):
    """
    Repository for StaffAttendance persistence operations.
    
    Extends BaseRepository as this model does not contain school_id directly.
    Tenant isolation is enforced upstream by validating staff_member_id ownership.
    
    Responsibilities:
    - Encapsulate daily attendance summary lookup and listing.
    - Support date range queries for reporting.
    - Filter by attendance status.
    - Provide row-locking for safe daily closure updates.
    - Respect unique constraint (staff_member_id, date).
    
    Non-Responsibilities:
    - Tenant isolation (enforced upstream via staff validation).
    - Business logic (working hours computation, status determination).
    - Cross-domain joins to verify school ownership.
    - Soft-delete filtering (model does not support it).
    """

    def __init__(self):
        super().__init__(StaffAttendance)

    def get_by_staff_and_date(
        self,
        db: Session,
        staff_member_id: UUID,
        date: datetime
    ) -> Optional[StaffAttendance]:
        """
        Retrieve attendance record matching the unique constraint.
        
        Used to prevent duplicate attendance entries for the same staff/date.
        
        Args:
            db: Database session.
            staff_member_id: Staff member UUID.
            date: Attendance date.
            
        Returns:
            StaffAttendance object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.staff_member_id == staff_member_id,
            self.model.date == date
        )

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def list_by_staff_and_date_range(
        self,
        db: Session,
        staff_member_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[StaffAttendance]:
        """
        List attendance records for a staff member within a date range.
        
        Ordered by date ascending for chronological view.
        
        Args:
            db: Database session.
            staff_member_id: Staff member UUID.
            start_date: Range start datetime.
            end_date: Range end datetime.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of StaffAttendance ORM objects.
        """
        stmt = select(self.model).where(
            self.model.staff_member_id == staff_member_id,
            self.model.date >= start_date,
            self.model.date <= end_date
        )

        stmt = stmt.order_by(self.model.date.asc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_date_range(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        staff_member_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[StaffAttendance]:
        """
        List attendance records within a date range with optional staff filter.
        
        Useful for school-wide attendance reports.
        
        Args:
            db: Database session.
            start_date: Range start datetime.
            end_date: Range end datetime.
            staff_member_id: Optional staff filter.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of StaffAttendance ORM objects.
        """
        stmt = select(self.model).where(
            self.model.date >= start_date,
            self.model.date <= end_date
        )

        if staff_member_id:
            stmt = stmt.where(self.model.staff_member_id == staff_member_id)

        stmt = stmt.order_by(self.model.date.desc(), self.model.staff_member_id.asc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_status(
        self,
        db: Session,
        staff_member_id: UUID,
        status: StaffAttendanceStatus,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[StaffAttendance]:
        """
        List attendance records filtered by status.
        
        Useful for identifying absent staff or generating absence reports.
        
        Args:
            db: Database session.
            staff_member_id: Staff member UUID.
            status: StaffAttendanceStatus enum value.
            start_date: Optional date range start.
            end_date: Optional date range end.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of StaffAttendance ORM objects.
        """
        stmt = select(self.model).where(
            self.model.staff_member_id == staff_member_id,
            self.model.status == status
        )

        if start_date:
            stmt = stmt.where(self.model.date >= start_date)

        if end_date:
            stmt = stmt.where(self.model.date <= end_date)

        stmt = stmt.order_by(self.model.date.desc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_locked_by_date_range(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        staff_member_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[StaffAttendance]:
        """
        List locked attendance records within a date range.
        
        Useful for identifying closed periods that cannot be modified.
        
        Args:
            db: Database session.
            start_date: Range start datetime.
            end_date: Range end datetime.
            staff_member_id: Optional staff filter.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of locked StaffAttendance ORM objects.
        """
        stmt = select(self.model).where(
            self.model.is_locked.is_(True),
            self.model.date >= start_date,
            self.model.date <= end_date
        )

        if staff_member_id:
            stmt = stmt.where(self.model.staff_member_id == staff_member_id)

        stmt = stmt.order_by(self.model.date.desc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_locked_for_update(
        self,
        db: Session,
        staff_member_id: UUID,
        date: datetime
    ) -> Optional[StaffAttendance]:
        """
        Retrieve attendance record with a row-level lock for safe updates.
        
        Prevents race conditions when closing daily attendance or 
        modifying locked records.
        
        Args:
            db: Database session.
            staff_member_id: Staff member UUID.
            date: Attendance date.
            
        Returns:
            Locked StaffAttendance object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.staff_member_id == staff_member_id,
            self.model.date == date
        )

        stmt = stmt.with_for_update()

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def count_by_status_and_date_range(
        self,
        db: Session,
        staff_member_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> dict[StaffAttendanceStatus, int]:
        """
        Count attendance records grouped by status within a date range.
        
        Useful for attendance summary calculations.
        
        Args:
            db: Database session.
            staff_member_id: Staff member UUID.
            start_date: Range start datetime.
            end_date: Range end datetime.
            
        Returns:
            Dictionary mapping StaffAttendanceStatus to count.
        """
        stmt = select(
            self.model.status,
            func.count(self.model.id).label('count')
        ).where(
            self.model.staff_member_id == staff_member_id,
            self.model.date >= start_date,
            self.model.date <= end_date
        ).group_by(self.model.status)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        
        return {row[0]: row[1] for row in result.all()}

    def sum_working_hours_by_date_range(
        self,
        db: Session,
        staff_member_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """
        Calculate total working hours for a staff member within a date range.
        
        Uses SQL aggregation for efficiency.
        
        Args:
            db: Database session.
            staff_member_id: Staff member UUID.
            start_date: Range start datetime.
            end_date: Range end datetime.
            
        Returns:
            Total working hours as float.
        """
        stmt = select(
            func.sum(self.model.working_hours).label('total_hours')
        ).where(
            self.model.staff_member_id == staff_member_id,
            self.model.date >= start_date,
            self.model.date <= end_date
        )

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        row = result.first()
        
        return float(row[0]) if row[0] else 0.0