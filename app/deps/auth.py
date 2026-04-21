# app/deps/auth.py


from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from domains.identity.repositories.accounts.user_repository import UserRepository
from domains.identity.repositories.accounts.user_role_repository import UserRoleRepository

# ---------------------------------------------------------------------
# Config (move to settings later)
# ---------------------------------------------------------------------

SECRET_KEY = "your-secret-key"  # move to env
ALGORITHM = "HS256"

security = HTTPBearer()


# ---------------------------------------------------------------------
# Token Decode
# ---------------------------------------------------------------------

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


# ---------------------------------------------------------------------
# Current User
# ---------------------------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Extract user from JWT token and attach roles.
    """

    token = credentials.credentials
    payload = decode_token(token)

    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    try:
        user_id = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID"
        )

    user_repo = UserRepository()
    user = user_repo.get_by_id(db, None, user_id)  # school_id handled via schema

    if not user or user.is_deleted or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Attach roles
    user_role_repo = UserRoleRepository()
    roles = user_role_repo.list_by_user(db, user.school_id, user.id)

    user.roles_list = [
        ur.role_id for ur in roles if ur.is_active
    ]

    return user


# ---------------------------------------------------------------------
# Optional User (no hard failure)
# ---------------------------------------------------------------------

def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    try:
        if not credentials:
            return None
        return get_current_user(credentials, db)
    except HTTPException:
        return None