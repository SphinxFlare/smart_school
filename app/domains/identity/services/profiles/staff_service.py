# identity/services/profiles/staff_service.py


from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from identity.models.profiles import StaffMember
from identity.repositories.profiles.staff_repository import StaffRepository
from identity.repositories.accounts.user_repository import UserRepository


class StaffService:
    """
    Service for Staff profile management.

    Responsibilities:
    - Create staff profile
    - Update staff details
    - Enforce employee_id uniqueness
    - Ensure one staff profile per user
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = StaffRepository()
        self.user_repository = UserRepository()

    # ---------------------------------------------------------------------
    # Create
    # ---------------------------------------------------------------------

    def create_staff(
        self,
        school_id: UUID,
        user_id: UUID,
        employee_id: str,
        position: str,
        date_of_joining: datetime,
        department: Optional[str] = None,
        qualifications: Optional[dict] = None,
    ) -> StaffMember:
        """
        Create staff profile.

        Ensures:
        - User exists
        - No existing staff profile for user
        - employee_id is unique within school
        """

        user = self.user_repository.get_by_id(self.db, school_id, user_id)
        if not user:
            raise ValueError("User not found")

        existing_profile = self.repository.get_by_user_id(
            self.db,
            school_id,
            user_id
        )
        if existing_profile:
            raise ValueError("Staff profile already exists for this user")

        existing_emp = self.repository.get_by_employee_id(
            self.db,
            school_id,
            employee_id
        )
        if existing_emp:
            raise ValueError("Employee ID already exists")

        staff = StaffMember(
            school_id=school_id,
            user_id=user_id,
            employee_id=employee_id,
            position=position,
            department=department,
            date_of_joining=date_of_joining,
            qualifications=qualifications,
        )

        return self.repository.create(self.db, staff)

    # ---------------------------------------------------------------------
    # Update
    # ---------------------------------------------------------------------

    def update_staff(
        self,
        school_id: UUID,
        staff_id: UUID,
        update_data: dict
    ) -> StaffMember:
        """
        Update staff profile fields.
        """

        staff = self.repository.get_by_id(self.db, school_id, staff_id)

        if not staff:
            raise ValueError("Staff member not found")

        restricted_fields = {
            "id", "school_id", "user_id", "employee_id", "created_at"
        }

        for key, value in update_data.items():
            if hasattr(staff, key) and key not in restricted_fields:
                setattr(staff, key, value)

        self.db.flush()
        return staff

    # ---------------------------------------------------------------------
    # Get
    # ---------------------------------------------------------------------

    def get_staff(
        self,
        school_id: UUID,
        staff_id: UUID
    ) -> Optional[StaffMember]:
        return self.repository.get_by_id(self.db, school_id, staff_id)

    def get_by_user(
        self,
        school_id: UUID,
        user_id: UUID
    ) -> Optional[StaffMember]:
        return self.repository.get_by_user_id(self.db, school_id, user_id)

    def get_by_employee_id(
        self,
        school_id: UUID,
        employee_id: str
    ) -> Optional[StaffMember]:
        return self.repository.get_by_employee_id(
            self.db,
            school_id,
            employee_id
        )