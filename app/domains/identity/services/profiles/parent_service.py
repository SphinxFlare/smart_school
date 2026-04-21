# identity/services/profiles/parent_service.py


from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

from identity.models.profiles import Parent, StudentParent
from identity.repositories.profiles.parent_repository import ParentRepository
from identity.repositories.profiles.student_repository import StudentRepository
from identity.repositories.profiles.student_parent_repository import StudentParentRepository
from identity.repositories.accounts.user_repository import UserRepository


class ParentService:
    """
    Service for Parent profile and student-parent relationships.

    Responsibilities:
    - Create parent profile
    - Link parent to student
    - Manage primary guardian
    - Prevent duplicate relationships
    """

    def __init__(self, db: Session):
        self.db = db
        self.parent_repo = ParentRepository()
        self.student_repo = StudentRepository()
        self.student_parent_repo = StudentParentRepository()
        self.user_repo = UserRepository()

    # ---------------------------------------------------------------------
    # Create Parent
    # ---------------------------------------------------------------------

    def create_parent(
        self,
        school_id: UUID,
        user_id: UUID,
        occupation: Optional[str] = None,
    ) -> Parent:
        """
        Create parent profile.

        Ensures:
        - User exists
        - No existing parent profile for user
        """

        user = self.user_repo.get_by_id(self.db, school_id, user_id)
        if not user:
            raise ValueError("User not found")

        existing = self.parent_repo.get_by_user_id(
            self.db,
            school_id,
            user_id
        )
        if existing:
            raise ValueError("Parent profile already exists for this user")

        parent = Parent(
            school_id=school_id,
            user_id=user_id,
            occupation=occupation,
        )

        return self.parent_repo.create(self.db, parent)

    # ---------------------------------------------------------------------
    # Link Parent ↔ Student
    # ---------------------------------------------------------------------

    def link_parent_to_student(
        self,
        school_id: UUID,
        student_id: UUID,
        parent_id: UUID,
        relationship: str,
        is_primary: bool = False
    ) -> StudentParent:
        """
        Link a parent to a student.

        Ensures:
        - Student exists
        - Parent exists
        - No duplicate mapping
        - Only one primary guardian per student
        """

        student = self.student_repo.get_by_id(self.db, school_id, student_id)
        if not student:
            raise ValueError("Student not found")

        parent = self.parent_repo.get_by_id(self.db, school_id, parent_id)
        if not parent:
            raise ValueError("Parent not found")

        existing = self.student_parent_repo.get_by_student_and_parent(
            self.db,
            school_id,
            student_id,
            parent_id
        )

        if existing:
            return existing  # idempotent

        # Handle primary guardian logic
        if is_primary:
            self.student_parent_repo.bulk_set_primary_guardian(
                self.db,
                school_id,
                student_id,
                parent_id
            )

        mapping = StudentParent(
            school_id=school_id,
            student_id=student_id,
            parent_id=parent_id,
            relationship=relationship,
            is_primary=is_primary,
        )

        return self.student_parent_repo.create(self.db, mapping)

    # ---------------------------------------------------------------------
    # Get
    # ---------------------------------------------------------------------

    def get_parent(
        self,
        school_id: UUID,
        parent_id: UUID
    ) -> Optional[Parent]:
        return self.parent_repo.get_by_id(self.db, school_id, parent_id)

    def get_by_user(
        self,
        school_id: UUID,
        user_id: UUID
    ) -> Optional[Parent]:
        return self.parent_repo.get_by_user_id(self.db, school_id, user_id)

    def list_parents_by_student(
        self,
        school_id: UUID,
        student_id: UUID
    ) -> List[StudentParent]:
        return self.student_parent_repo.list_by_student(
            self.db,
            school_id,
            student_id
        )

    def list_students_by_parent(
        self,
        school_id: UUID,
        parent_id: UUID
    ) -> List[StudentParent]:
        return self.student_parent_repo.list_by_parent(
            self.db,
            school_id,
            parent_id
        )