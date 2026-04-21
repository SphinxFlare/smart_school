# identity/services/roles/role_service.py


from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from identity.models.accounts import Role
from identity.repositories.accounts.role_repository import RoleRepository
from types.types import UserRoleType


class RoleService:
    """
    Service for Role management.

    Responsibilities:
    - Create roles
    - Update role metadata (description, permissions)
    - Retrieve roles (single, list)
    - Enforce uniqueness (role name per school)

    Constraints:
    - No direct SQL
    - No transaction commit
    - Business validation handled here
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = RoleRepository()

    # ---------------------------------------------------------------------
    # Create
    # ---------------------------------------------------------------------

    def create_role(
        self,
        school_id: UUID,
        name: UserRoleType,
        description: Optional[str] = None,
        permissions: Optional[str] = None,
    ) -> Role:
        """
        Create a new role for a school.

        Ensures:
        - Role name is unique within the school
        """

        existing = self.repository.get_by_name(
            db=self.db,
            school_id=school_id,
            name=name
        )

        if existing:
            raise ValueError(f"Role '{name.value}' already exists")

        role = Role(
            school_id=school_id,
            name=name,
            description=description,
            permissions=permissions,
        )

        return self.repository.create(self.db, role)

    # ---------------------------------------------------------------------
    # Update
    # ---------------------------------------------------------------------

    def update_role(
        self,
        school_id: UUID,
        role_id: UUID,
        description: Optional[str] = None,
        permissions: Optional[str] = None,
    ) -> Role:
        """
        Update role metadata.

        Only allows updating:
        - description
        - permissions
        """

        role = self.repository.get_by_id(
            db=self.db,
            school_id=school_id,
            role_id=role_id
        )

        if not role:
            raise ValueError(f"Role {role_id} not found")

        if description is not None:
            role.description = description

        if permissions is not None:
            role.permissions = permissions

        self.db.flush()
        return role

    # ---------------------------------------------------------------------
    # Get
    # ---------------------------------------------------------------------

    def get_role(
        self,
        school_id: UUID,
        role_id: UUID
    ) -> Optional[Role]:
        """
        Retrieve role by ID.
        """
        return self.repository.get_by_id(
            db=self.db,
            school_id=school_id,
            role_id=role_id
        )

    def get_role_by_name(
        self,
        school_id: UUID,
        name: UserRoleType
    ) -> Optional[Role]:
        """
        Retrieve role by name.
        """
        return self.repository.get_by_name(
            db=self.db,
            school_id=school_id,
            name=name
        )

    # ---------------------------------------------------------------------
    # List
    # ---------------------------------------------------------------------

    def list_roles(
        self,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Role]:
        """
        List roles for a school.
        """
        return self.repository.list_by_school(
            db=self.db,
            school_id=school_id,
            skip=skip,
            limit=limit
        )