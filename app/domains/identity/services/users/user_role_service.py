# identity/services/users/user_role_service.py


from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from identity.models.accounts import UserRole
from identity.repositories.accounts.user_role_repository import UserRoleRepository
from identity.repositories.accounts.user_repository import UserRepository
from identity.repositories.accounts.role_repository import RoleRepository


class UserRoleService:
    """
    Service for managing user-role assignments.

    Responsibilities:
    - Assign role to user
    - Revoke role
    - List roles of a user
    - List users of a role
    - Ensure idempotency (no duplicate assignments)

    Constraints:
    - No direct SQL
    - No transaction commit
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = UserRoleRepository()
        self.user_repository = UserRepository()
        self.role_repository = RoleRepository()

    # ---------------------------------------------------------------------
    # Assign Role
    # ---------------------------------------------------------------------

    def assign_role(
        self,
        school_id: UUID,
        user_id: UUID,
        role_id: UUID
    ) -> UserRole:
        """
        Assign a role to a user.

        Ensures:
        - User exists
        - Role exists
        - No duplicate active assignment (idempotent)
        """

        # Validate user
        user = self.user_repository.get_by_id(self.db, school_id, user_id)
        if not user:
            raise ValueError("User not found")

        # Validate role
        role = self.role_repository.get_by_id(self.db, school_id, role_id)
        if not role:
            raise ValueError("Role not found")

        # Idempotency check
        existing = self.repository.get_by_user_and_role(
            self.db,
            school_id,
            user_id,
            role_id
        )

        if existing:
            if existing.is_active:
                return existing  # already assigned
            else:
                # reactivate existing mapping
                locked = self.repository.lock_by_user_and_role_for_update(
                    self.db,
                    school_id,
                    user_id,
                    role_id
                )
                locked.is_active = True
                self.db.flush()
                return locked

        # Create new assignment
        assignment = UserRole(
            user_id=user_id,
            role_id=role_id,
            is_active=True
        )

        return self.repository.create(self.db, assignment)

    # ---------------------------------------------------------------------
    # Revoke Role
    # ---------------------------------------------------------------------

    def revoke_role(
        self,
        school_id: UUID,
        user_id: UUID,
        role_id: UUID
    ) -> None:
        """
        Revoke (deactivate) a role from a user.
        """

        assignment = self.repository.lock_by_user_and_role_for_update(
            self.db,
            school_id,
            user_id,
            role_id
        )

        if not assignment:
            raise ValueError("Role assignment not found")

        assignment.is_active = False
        self.db.flush()

    # ---------------------------------------------------------------------
    # Get
    # ---------------------------------------------------------------------

    def list_roles_by_user(
        self,
        school_id: UUID,
        user_id: UUID
    ) -> List[UserRole]:
        """
        List all role assignments for a user.
        """
        return self.repository.list_by_user(
            self.db,
            school_id,
            user_id
        )

    def list_users_by_role(
        self,
        school_id: UUID,
        role_id: UUID
    ) -> List[UserRole]:
        """
        List all users assigned to a role.
        """
        return self.repository.list_by_role(
            self.db,
            school_id,
            role_id
        )

    def has_role(
        self,
        school_id: UUID,
        user_id: UUID,
        role_id: UUID
    ) -> bool:
        """
        Check if a user has a specific active role.
        """
        assignment = self.repository.get_by_user_and_role(
            self.db,
            school_id,
            user_id,
            role_id
        )
        return bool(assignment and assignment.is_active)