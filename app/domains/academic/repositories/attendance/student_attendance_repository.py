# student_attendance_repository.py# academic/repositories/attendance.py

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from academic.models.attendance import StudentAttendance

from repositories.base import BaseRepository
from types.types import AttendanceStatus


# =============================================================================
# STUDENT ATTENDANCE REPOSITORY
# =============================================================================

class StudentAttendanceRepository(BaseRepository[StudentAttendance]):
    """
    Repository for StudentAttendance persistence operations.
    
    Extends BaseRepository as this model does not contain school_id directly.
    Tenant isolation is enforced upstream by validating section_id or 
    academic_year_id ownership.
    
    Responsibilities:
    - Encapsulate attendance lookup and listing patterns.
    - Support date range queries for reporting.
    - Provide row-locking for safe attendance mark updates.
    - Respect unique constraint (student_id, date).
    
    Non-Responsibilities:
    - Tenant isolation (enforced upstream via section/academic_year validation).
    - Business logic (attendance percentage, leave policies).
    - Cross-domain joins to verify school ownership.
    - Soft-delete filtering (model does not support it).
    """

    def __init__(self):
        super().__init__(StudentAttendance)

    def get_by_student_and_date(
        self,
        db: Session,
        student_id: UUID,
        date: datetime
    ) -> Optional[StudentAttendance]:
        """
        Retrieve attendance record matching the unique constraint.
        
        Used to prevent duplicate attendance entries for the same student/date.
        
        Args:
            db: Database session.
            student_id: Student UUID.
            date: Attendance date (datetime).
            
        Returns:
            StudentAttendance object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.student_id == student_id,
            self.model.date == date
        )

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def list_by_student_and_date_range(
        self,
        db: Session,
        student_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentAttendance]:
        """
        List attendance records for a student within a date range.
        
        Ordered by date ascending for chronological view.
        
        Args:
            db: Database session.
            student_id: Student UUID.
            start_date: Range start datetime.
            end_date: Range end datetime.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of StudentAttendance ORM objects.
        """
        stmt = select(self.model).where(
            self.model.student_id == student_id,
            self.model.date >= start_date,
            self.model.date <= end_date
        )

        stmt = stmt.order_by(self.model.date.asc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_section_and_date(
        self,
        db: Session,
        section_id: UUID,
        date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentAttendance]:
        """
        List attendance records for a section on a specific date.
        
        Useful for daily roll call and attendance marking interfaces.
        
        Args:
            db: Database session.
            section_id: Section UUID (tenant isolation enforced upstream).
            date: Attendance date.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of StudentAttendance ORM objects.
        """
        stmt = select(self.model).where(
            self.model.section_id == section_id,
            self.model.date == date
        )

        stmt = stmt.order_by(self.model.student_id.asc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_academic_year(
        self,
        db: Session,
        academic_year_id: UUID,
        student_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentAttendance]:
        """
        List attendance records for an academic year with optional filters.
        
        Useful for attendance reports and analytics.
        
        Args:
            db: Database session.
            academic_year_id: Academic year UUID (tenant isolation enforced upstream).
            student_id: Optional student filter.
            start_date: Optional date range start.
            end_date: Optional date range end.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of StudentAttendance ORM objects.
        """
        stmt = select(self.model).where(
            self.model.academic_year_id == academic_year_id
        )

        if student_id:
            stmt = stmt.where(self.model.student_id == student_id)

        if start_date:
            stmt = stmt.where(self.model.date >= start_date)

        if end_date:
            stmt = stmt.where(self.model.date <= end_date)

        stmt = stmt.order_by(self.model.date.desc(), self.model.student_id.asc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_status(
        self,
        db: Session,
        section_id: UUID,
        date: datetime,
        status: AttendanceStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentAttendance]:
        """
        List attendance records filtered by status for a section and date.
        
        Useful for identifying absent students or generating absence reports.
        
        Args:
            db: Database session.
            section_id: Section UUID.
            date: Attendance date.
            status: AttendanceStatus enum value.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of StudentAttendance ORM objects.
        """
        stmt = select(self.model).where(
            self.model.section_id == section_id,
            self.model.date == date,
            self.model.status == status
        )

        stmt = stmt.order_by(self.model.student_id.asc())
        stmt = stmt.offset(skip).limit(limit)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_locked_for_update(
        self,
        db: Session,
        student_id: UUID,
        date: datetime
    ) -> Optional[StudentAttendance]:
        """
        Retrieve attendance record with a row-level lock for safe updates.
        
        Prevents race conditions when multiple users mark attendance 
        for the same student on the same date.
        
        Args:
            db: Database session.
            student_id: Student UUID.
            date: Attendance date.
            
        Returns:
            Locked StudentAttendance object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.student_id == student_id,
            self.model.date == date
        )

        stmt = stmt.with_for_update()

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def count_by_status_and_date_range(
        self,
        db: Session,
        student_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> dict[AttendanceStatus, int]:
        """
        Count attendance records grouped by status within a date range.
        
        Useful for attendance summary calculations.
        
        Args:
            db: Database session.
            student_id: Student UUID.
            start_date: Range start datetime.
            end_date: Range end datetime.
            
        Returns:
            Dictionary mapping AttendanceStatus to count.
        """
        stmt = select(
            self.model.status,
            func.count(self.model.id).label('count')
        ).where(
            self.model.student_id == student_id,
            self.model.date >= start_date,
            self.model.date <= end_date
        ).group_by(self.model.status)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        
        return {row[0]: row[1] for row in result.all()}
    
    def exists_by_student_and_date(
        self,
        db: Session,
        student_id: UUID,
        date: datetime
    ) -> bool:

        stmt = select(self.model.id).where(
            self.model.student_id == student_id,
            self.model.date == date
        ).limit(1)

        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None