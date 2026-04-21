# identity/api/users/router.py


from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.auth.auth_router import hash_password
from app.deps.auth import get_current_user
from app.deps.roles import require_roles
from app.deps.common import get_db

from domains.identity.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
)

from domains.identity.services.users.user_service import UserService


router = APIRouter(prefix="/users", tags=["Users"])


# ---------------------------------------------------------------------
# Create User
# ---------------------------------------------------------------------

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN"]))
):
    service = UserService(db)

    try:
        user = service.create_user(
            school_id=payload.school_id,
            email=payload.email,
            password_hash = hash_password(payload.password),  
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            date_of_birth=payload.date_of_birth,
        )
        return user

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------
# Get Current User
# ---------------------------------------------------------------------

@router.get("/me", response_model=UserResponse)
def get_me(current_user = Depends(get_current_user)):
    return current_user


# ---------------------------------------------------------------------
# Get User by ID
# ---------------------------------------------------------------------

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN", "STAFF"]))
):
    service = UserService(db)

    user = service.get_user(
        school_id=current_user.school_id,
        user_id=user_id
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# ---------------------------------------------------------------------
# List Users
# ---------------------------------------------------------------------

@router.get("/", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN"])),
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
):
    service = UserService(db)

    return service.list_users(
        school_id=current_user.school_id,
        skip=skip,
        limit=limit,
        is_active=is_active,
    )


# ---------------------------------------------------------------------
# Update User
# ---------------------------------------------------------------------

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN"]))
):
    service = UserService(db)

    try:
        user = service.update_user(
            school_id=current_user.school_id,
            user_id=user_id,
            update_data=payload.model_dump(exclude_unset=True)
        )
        return user

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---------------------------------------------------------------------
# Delete User (Soft Delete)
# ---------------------------------------------------------------------

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN"]))
):
    service = UserService(db)

    try:
        service.delete_user(
            school_id=current_user.school_id,
            user_id=user_id
        )
        return None

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))