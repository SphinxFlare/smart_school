# academic/api/deps.py

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps.common import get_db
from app.deps.auth import get_current_user


# ---------------------------------------------------------
# DB Dependency (re-export for local module usage)
# ---------------------------------------------------------
def get_academic_db(db: Session = Depends(get_db)) -> Session:
    return db


# ---------------------------------------------------------
# Current User (strict)
# ---------------------------------------------------------
def get_academic_user(current_user=Depends(get_current_user)):
    return current_user


# ---------------------------------------------------------
# School Context (CRITICAL)
# ---------------------------------------------------------
def get_school_context(current_user=Depends(get_current_user)):
    """
    Extract school_id from authenticated user.

    This is the ONLY trusted source of tenant context.
    """
    if not getattr(current_user, "school_id", None):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with any school"
        )

    return current_user.school_id


# ---------------------------------------------------------
# Combined Context (used most of the time)
# ---------------------------------------------------------
def get_context(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Standard dependency bundle:
    - db session
    - current user
    - school_id

    Usage:
        db, user, school_id = Depends(get_context)
    """
    if not getattr(current_user, "school_id", None):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid school context"
        )

    return db, current_user, current_user.school_id


# ---------------------------------------------------------
# Pagination Dependency (optional standardization)
# ---------------------------------------------------------
def get_pagination(skip: int = 0, limit: int = 50):
    """
    Standard pagination control.

    Caps:
    - limit max = 100
    """
    if limit > 100:
        limit = 100

    if skip < 0:
        skip = 0

    return skip, limit