# identity/services/aggregates/identity_aggregate_service.py


from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

from identity.repositories.aggregates.aggregate_repository import IdentityAggregateRepository


class IdentityAggregateService:
    """
    Service for aggregated identity views.

    Responsibilities:
    - Retrieve combined identity data (user + roles + profiles)
    - Provide read-optimized views for APIs
    - No mutations (read-only service)

    Constraints:
    - No business logic
    - No validation (delegated to write services)
    - No direct SQL
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = IdentityAggregateRepository()

    # ---------------------------------------------------------------------
    # User Views
    # ---------------------------------------------------------------------

    def get_user_full_profile(
        self,
        school_id: UUID,
        user_id: UUID
    ):
        """
        Get full user profile including:
        - basic user info
        - roles
        - linked profile (student/parent/staff)
        """
        return self.repository.get_user_full_profile(
            db=self.db,
            school_id=school_id,
            user_id=user_id
        )

    def get_user_with_roles(
        self,
        school_id: UUID,
        user_id: UUID
    ):
        """
        Get user with assigned roles only.
        """
        return self.repository.get_user_with_roles(
            db=self.db,
            school_id=school_id,
            user_id=user_id
        )

    # ---------------------------------------------------------------------
    # Student Views
    # ---------------------------------------------------------------------

    def get_student_with_parents(
        self,
        school_id: UUID,
        student_id: UUID
    ):
        """
        Get student with parent relationships.
        """
        return self.repository.get_student_with_parents(
            db=self.db,
            school_id=school_id,
            student_id=student_id
        )

    def get_student_full_profile(
        self,
        school_id: UUID,
        student_id: UUID
    ):
        """
        Get full student profile:
        - student
        - user
        - parents
        - roles (if needed)
        """
        return self.repository.get_student_full_profile(
            db=self.db,
            school_id=school_id,
            student_id=student_id
        )

    # ---------------------------------------------------------------------
    # Staff Views
    # ---------------------------------------------------------------------

    def get_staff_full_profile(
        self,
        school_id: UUID,
        staff_id: UUID
    ):
        """
        Get full staff profile:
        - staff
        - user
        - roles
        """
        return self.repository.get_staff_full_profile(
            db=self.db,
            school_id=school_id,
            staff_id=staff_id
        )

    # ---------------------------------------------------------------------
    # Lists / Search
    # ---------------------------------------------------------------------

    def list_users_with_roles(
        self,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List:
        """
        List users with their roles.
        """
        return self.repository.list_users_with_roles(
            db=self.db,
            school_id=school_id,
            skip=skip,
            limit=limit
        )

    def list_students_with_parents(
        self,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List:
        """
        List students with parent relationships.
        """
        return self.repository.list_students_with_parents(
            db=self.db,
            school_id=school_id,
            skip=skip,
            limit=limit
        )

    def search_users(
        self,
        school_id: UUID,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List:
        """
        Search users by name/email/phone.
        """
        return self.repository.search_users(
            db=self.db,
            school_id=school_id,
            query=query,
            skip=skip,
            limit=limit
        )