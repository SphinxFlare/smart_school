# identity/api/aggregates/router.py


from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps.common import get_db
from app.deps.auth import get_current_user
from app.deps.roles import require_roles

from domains.identity.services.aggregates.identity_aggregate_service import (
    IdentityAggregateService
)


router = APIRouter(prefix="/identity", tags=["Identity Aggregates"])


# ---------------------------------------------------------------------
# USER AGGREGATES
# ---------------------------------------------------------------------

@router.get("/users/{user_id}/full")
def get_user_full_profile(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN", "STAFF"]))
):
    service = IdentityAggregateService(db)

    data = service.get_user_full_profile(
        school_id=current_user.school_id,
        user_id=user_id
    )

    if not data:
        raise HTTPException(status_code=404, detail="User not found")

    return data


@router.get("/users/{user_id}/roles")
def get_user_with_roles(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN", "STAFF"]))
):
    service = IdentityAggregateService(db)

    data = service.get_user_with_roles(
        school_id=current_user.school_id,
        user_id=user_id
    )

    if not data:
        raise HTTPException(status_code=404, detail="User not found")

    return data


# ---------------------------------------------------------------------
# STUDENT AGGREGATES
# ---------------------------------------------------------------------

@router.get("/students/{student_id}/parents")
def get_student_with_parents(
    student_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN", "STAFF"]))
):
    service = IdentityAggregateService(db)

    data = service.get_student_with_parents(
        school_id=current_user.school_id,
        student_id=student_id
    )

    if not data:
        raise HTTPException(status_code=404, detail="Student not found")

    return data


@router.get("/students/{student_id}/full")
def get_student_full_profile(
    student_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN", "STAFF"]))
):
    service = IdentityAggregateService(db)

    data = service.get_student_full_profile(
        school_id=current_user.school_id,
        student_id=student_id
    )

    if not data:
        raise HTTPException(status_code=404, detail="Student not found")

    return data


# ---------------------------------------------------------------------
# STAFF AGGREGATES
# ---------------------------------------------------------------------

@router.get("/staff/{staff_id}/full")
def get_staff_full_profile(
    staff_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN", "STAFF"]))
):
    service = IdentityAggregateService(db)

    data = service.get_staff_full_profile(
        school_id=current_user.school_id,
        staff_id=staff_id
    )

    if not data:
        raise HTTPException(status_code=404, detail="Staff not found")

    return data


# ---------------------------------------------------------------------
# LISTS / SEARCH
# ---------------------------------------------------------------------

@router.get("/users")
def list_users_with_roles(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN"])),
    skip: int = 0,
    limit: int = 100
):
    service = IdentityAggregateService(db)

    return service.list_users_with_roles(
        school_id=current_user.school_id,
        skip=skip,
        limit=limit
    )


@router.get("/students")
def list_students_with_parents(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN"])),
    skip: int = 0,
    limit: int = 100
):
    service = IdentityAggregateService(db)

    return service.list_students_with_parents(
        school_id=current_user.school_id,
        skip=skip,
        limit=limit
    )


@router.get("/search/users")
def search_users(
    query: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["ADMIN", "STAFF"])),
    skip: int = 0,
    limit: int = 100
):
    service = IdentityAggregateService(db)

    return service.search_users(
        school_id=current_user.school_id,
        query=query,
        skip=skip,
        limit=limit
    )