# app/deps/roles.py


from typing import List

from fastapi import Depends, HTTPException, status

from app.deps.auth import get_current_user
from domains.identity.repositories.accounts.role_repository import RoleRepository
from sqlalchemy.orm import Session
from app.deps.common import get_db


# ---------------------------------------------------------------------
# Require Roles
# ---------------------------------------------------------------------

def require_roles(required_roles: List[str]):
    """
    Dependency to enforce role-based access.

    Usage:
        Depends(require_roles(["ADMIN", "STAFF"]))
    """

    def role_checker(
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        role_repo = RoleRepository()

        # Fetch role names from DB using role IDs
        user_roles = role_repo.get_roles_by_ids(
            db=db,
            school_id=current_user.school_id,
            role_ids=current_user.roles_list
        )

        user_role_names = {role.name.value for role in user_roles}

        if not any(role in user_role_names for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        return current_user

    return role_checker


# ---------------------------------------------------------------------
# Require All Roles (strict)
# ---------------------------------------------------------------------

def require_all_roles(required_roles: List[str]):
    """
    User must have ALL specified roles.
    """

    def role_checker(
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        role_repo = RoleRepository()

        user_roles = role_repo.get_roles_by_ids(
            db=db,
            school_id=current_user.school_id,
            role_ids=current_user.roles_list
        )

        user_role_names = {role.name.value for role in user_roles}

        if not all(role in user_role_names for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        return current_user

    return role_checker