# admission/services/admission/enrollment_service.py


# admission/services/admission/enrollment_service.py

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from admission.models.enrollments import StudentEnrollment
from admission.repositories.enrollments import StudentEnrollmentRepository
from types.admissions import EnrollmentType


class EnrollmentService:
    """
    Service for managing Student Enrollment operations.
    
    Responsibilities:
    - Creating enrollments with integrity checks (uniqueness per year).
    - Generating unique enrollment numbers safely (concurrency safe).
    - Retrieving enrollment records (by ID, student, year, number).
    
    Constraints:
    - No knowledge of Admission Applications or Approval status.
    - No transaction management (commit/rollback delegated to caller).
    - No direct SQL (uses Repository).
    - Multi-tenant safety enforced via school_id arguments.
    - Dependencies point downward (does not call ApplicationService).
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = StudentEnrollmentRepository()

    def create_enrollment(
        self,
        school_id: UUID,
        academic_year_id: UUID,
        student_id: UUID,
        class_id: UUID,
        section_id: UUID,
        enrollment_type: EnrollmentType,
        created_by_id: UUID
    ) -> StudentEnrollment:
        """
        Create a new student enrollment.
        
        Enforces business rules:
        1. Student cannot be enrolled twice in the same academic year.
        2. Enrollment number must be unique per school (generated safely).
        
        Args:
            school_id: Tenant identifier.
            academic_year_id: The academic year UUID.
            student_id: The student UUID.
            class_id: The class UUID.
            section_id: The section UUID.
            enrollment_type: Type of enrollment (e.g., NEW, PROMOTION).
            created_by_id: The user creating the enrollment.
            
        Returns:
            The created StudentEnrollment ORM object.
            
        Raises:
            ValueError: If student is already enrolled in this academic year.
        """
        # 1. Integrity Check: Ensure student isn't already enrolled this year
        existing = self.repository.get_by_student_and_academic_year(
            db=self.db,
            school_id=school_id,
            student_id=student_id,
            academic_year_id=academic_year_id
        )

        if existing:
            raise ValueError(
                f"Student {student_id} is already enrolled in academic year {academic_year_id}"
            )

        # 2. Generate Unique Enrollment Number (Concurrency Safe)
        # Uses row-level lock on the latest enrollment record to prevent race conditions
        enrollment_number = self._generate_enrollment_number(school_id)

        # 3. Create Record
        enrollment = StudentEnrollment(
            school_id=school_id,
            academic_year_id=academic_year_id,
            student_id=student_id,
            class_id=class_id,
            section_id=section_id,
            enrollment_type=enrollment_type,
            enrollment_number=enrollment_number,
            enrollment_date=datetime.utcnow(),
            created_by_id=created_by_id
        )

        # Repository handles flush, Caller handles commit
        return self.repository.create(self.db, enrollment)

    def _generate_enrollment_number(self, school_id: UUID) -> str:
        """
        Generate next unique enrollment number safely.
        Uses row lock + count fallback to avoid duplicates.
        """

        latest = self.repository.get_latest_enrollment_locked(
            db=self.db,
            school_id=school_id
        )

        if latest and latest.enrollment_number:
            try:
                current_num = int(latest.enrollment_number)
                return str(current_num + 1)
            except ValueError:
                # fallback → use count instead of resetting to 1
                total = len(
                    self.repository.list_by_academic_year(
                        db=self.db,
                        school_id=school_id,
                        academic_year_id=latest.academic_year_id,
                        skip=0,
                        limit=1000000,
                    )
                )
                return str(total + 1)

        return "1"

    def get_enrollment(
        self,
        enrollment_id: UUID
    ) -> Optional[StudentEnrollment]:
        """
        Retrieve a specific enrollment by ID.
        
        Args:
            enrollment_id: The UUID of the enrollment.
            
        Returns:
            StudentEnrollment object if found, else None.
        """
        return self.repository.get(self.db, enrollment_id)

    def get_by_student_and_year(
        self,
        school_id: UUID,
        student_id: UUID,
        academic_year_id: UUID
    ) -> Optional[StudentEnrollment]:
        """
        Check if an enrollment exists for a student in a specific year.
        
        Args:
            school_id: Tenant identifier.
            student_id: The student UUID.
            academic_year_id: The academic year UUID.
            
        Returns:
            StudentEnrollment object if found, else None.
        """
        return self.repository.get_by_student_and_academic_year(
            db=self.db,
            school_id=school_id,
            student_id=student_id,
            academic_year_id=academic_year_id
        )

    def get_by_enrollment_number(
        self,
        school_id: UUID,
        enrollment_number: str
    ) -> Optional[StudentEnrollment]:
        """
        Retrieve enrollment by its unique number.
        
        Args:
            school_id: Tenant identifier.
            enrollment_number: The enrollment number string.
            
        Returns:
            StudentEnrollment object if found, else None.
        """
        return self.repository.get_by_enrollment_number(
            db=self.db,
            school_id=school_id,
            enrollment_number=enrollment_number
        )

    def list_by_student(
        self,
        school_id: UUID,
        student_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentEnrollment]:
        """
        List all enrollments for a specific student.
        
        Args:
            school_id: Tenant identifier.
            student_id: The student UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of StudentEnrollment objects.
        """
        return self.repository.list_by_student(
            db=self.db,
            school_id=school_id,
            student_id=student_id,
            skip=skip,
            limit=limit
        )

    def list_by_academic_year(
        self,
        school_id: UUID,
        academic_year_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentEnrollment]:
        """
        List all enrollments for a specific academic year.
        
        Args:
            school_id: Tenant identifier.
            academic_year_id: The academic year UUID.
            skip: Pagination offset.
            limit: Pagination limit.
            
        Returns:
            List of StudentEnrollment objects.
        """
        return self.repository.list_by_academic_year(
            db=self.db,
            school_id=school_id,
            academic_year_id=academic_year_id,
            skip=skip,
            limit=limit
        )