# identity/services/profiles/driver_service.py


from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from identity.models.profiles import Driver
from identity.repositories.profiles.driver_repository import DriverRepository
from identity.repositories.profiles.staff_repository import StaffRepository


class DriverService:
    """
    Service for Driver profile management.

    Responsibilities:
    - Create driver profile (linked to staff)
    - Update driver details
    - Enforce license uniqueness
    - Ensure one driver per staff member
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = DriverRepository()
        self.staff_repository = StaffRepository()

    # ---------------------------------------------------------------------
    # Create
    # ---------------------------------------------------------------------

    def create_driver(
        self,
        school_id: UUID,
        staff_member_id: UUID,
        license_number: str,
        license_type: str,
        license_expiry: datetime,
        status
    ) -> Driver:
        """
        Create driver profile.

        Ensures:
        - Staff exists
        - No existing driver for staff member
        - license_number is unique within school
        """

        # Validate staff exists
        staff = self.staff_repository.get_by_id(
            self.db,
            school_id,
            staff_member_id
        )
        if not staff:
            raise ValueError("Staff member not found")

        # Ensure one driver per staff
        existing = self.repository.get_by_staff_member_id(
            self.db,
            school_id,
            staff_member_id
        )
        if existing:
            raise ValueError("Driver profile already exists for this staff member")

        # Validate license uniqueness
        existing_license = self.repository.get_by_license_number(
            self.db,
            school_id,
            license_number
        )
        if existing_license:
            raise ValueError("License number already exists")

        driver = Driver(
            school_id=school_id,
            staff_member_id=staff_member_id,
            license_number=license_number,
            license_type=license_type,
            license_expiry=license_expiry,
            status=status,
        )

        return self.repository.create(self.db, driver)

    # ---------------------------------------------------------------------
    # Update
    # ---------------------------------------------------------------------

    def update_driver(
        self,
        school_id: UUID,
        driver_id: UUID,
        update_data: dict
    ) -> Driver:
        """
        Update driver profile fields.
        """

        driver = self.repository.get_by_id(self.db, school_id, driver_id)

        if not driver:
            raise ValueError("Driver not found")

        restricted_fields = {
            "id", "school_id", "staff_member_id", "license_number", "created_at"
        }

        for key, value in update_data.items():
            if hasattr(driver, key) and key not in restricted_fields:
                setattr(driver, key, value)

        self.db.flush()
        return driver

    # ---------------------------------------------------------------------
    # Get
    # ---------------------------------------------------------------------

    def get_driver(
        self,
        school_id: UUID,
        driver_id: UUID
    ) -> Optional[Driver]:
        return self.repository.get_by_id(self.db, school_id, driver_id)

    def get_by_staff_member(
        self,
        school_id: UUID,
        staff_member_id: UUID
    ) -> Optional[Driver]:
        return self.repository.get_by_staff_member_id(
            self.db,
            school_id,
            staff_member_id
        )

    def get_by_license_number(
        self,
        school_id: UUID,
        license_number: str
    ) -> Optional[Driver]:
        return self.repository.get_by_license_number(
            self.db,
            school_id,
            license_number
        )