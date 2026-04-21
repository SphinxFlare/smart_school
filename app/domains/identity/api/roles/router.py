# identity/api/roles/router.py


from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps.common import get_db
from app.deps.roles import require_roles

from domains.identity.schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
)

from domains.identity.services.roles.role_service import RoleService


router = APIRouter(prefix="/roles", tags=["Roles"])


# ---------------------------------------------------------------------
# Create Role
# ---------------------------------------------------------------------

@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN"]))
):
    service = RoleService(db)

    try:
        role = service.create_role(
            school_id=current_user.school_id,
            name=payload.name,
            description=payload.description,
            permissions=payload.permissions,
        )
        return role

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------
# Get Role by ID
# ---------------------------------------------------------------------

@router.get("/{role_id}", response_model=RoleResponse)
def get_role(
    role_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN", "STAFF"]))
):
    service = RoleService(db)

    role = service.get_role(
        school_id=current_user.school_id,
        role_id=role_id
    )

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    return role


# ---------------------------------------------------------------------
# List Roles
# ---------------------------------------------------------------------

@router.get("/", response_model=List[RoleResponse])
def list_roles(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN"])),
    skip: int = 0,
    limit: int = 100,
):
    service = RoleService(db)

    return service.list_roles(
        school_id=current_user.school_id,
        skip=skip,
        limit=limit
    )


# ---------------------------------------------------------------------
# Update Role
# ---------------------------------------------------------------------

@router.put("/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: UUID,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN"]))
):
    service = RoleService(db)

    try:
        role = service.update_role(
            school_id=current_user.school_id,
            role_id=role_id,
            description=payload.description,
            permissions=payload.permissions,
        )
        return role

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))