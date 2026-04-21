# identity/services/profiles/student_service.py


from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from identity.models.profiles import Student
from identity.repositories.profiles.student_repository import StudentRepository
from identity.repositories.accounts.user_repository import UserRepository


class StudentService:
    """
    Service for Student profile management.

    Responsibilities:
    - Create student profile
    - Update student details
    - Enforce admission_number uniqueness
    - Ensure user linkage integrity

    Constraints:
    - One user → one student profile
    - admission_number unique per school
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = StudentRepository()
        self.user_repository = UserRepository()

    # ---------------------------------------------------------------------
    # Create
    # ---------------------------------------------------------------------

    def create_student(
        self,
        school_id: UUID,
        user_id: UUID,
        admission_number: str,
        date_of_birth: datetime,
        emergency_contact_name: Optional[str] = None,
        emergency_contact_phone: Optional[str] = None,
    ) -> Student:
        """
        Create student profile.

        Ensures:
        - User exists
        - No existing student profile for user
        - admission_number is unique
        """

        # Validate user exists
        user = self.user_repository.get_by_id(self.db, school_id, user_id)
        if not user:
            raise ValueError("User not found")

        # Ensure user does not already have a student profile
        existing_profile = self.repository.get_by_user_id(
            self.db,
            school_id,
            user_id
        )
        if existing_profile:
            raise ValueError("Student profile already exists for this user")

        # Validate admission number uniqueness
        existing_adm = self.repository.get_by_admission_number(
            self.db,
            school_id,
            admission_number
        )
        if existing_adm:
            raise ValueError("Admission number already exists")

        student = Student(
            school_id=school_id,
            user_id=user_id,
            admission_number=admission_number,
            date_of_birth=date_of_birth,
            emergency_contact_name=emergency_contact_name,
            emergency_contact_phone=emergency_contact_phone,
        )

        return self.repository.create(self.db, student)

    # ---------------------------------------------------------------------
    # Update
    # ---------------------------------------------------------------------

    def update_student(
        self,
        school_id: UUID,
        student_id: UUID,
        update_data: dict
    ) -> Student:
        """
        Update student profile fields.
        """

        student = self.repository.get_by_id(self.db, school_id, student_id)

        if not student:
            raise ValueError("Student not found")

        restricted_fields = {
            "id", "school_id", "user_id", "created_at"
        }

        for key, value in update_data.items():
            if hasattr(student, key) and key not in restricted_fields:
                setattr(student, key, value)

        self.db.flush()
        return student

    # ---------------------------------------------------------------------
    # Get
    # ---------------------------------------------------------------------

    def get_student(
        self,
        school_id: UUID,
        student_id: UUID
    ) -> Optional[Student]:
        return self.repository.get_by_id(self.db, school_id, student_id)

    def get_by_user(
        self,
        school_id: UUID,
        user_id: UUID
    ) -> Optional[Student]:
        return self.repository.get_by_user_id(self.db, school_id, user_id)

    def get_by_admission_number(
        self,
        school_id: UUID,
        admission_number: str
    ) -> Optional[Student]:
        return self.repository.get_by_admission_number(
            self.db,
            school_id,
            admission_number
        )