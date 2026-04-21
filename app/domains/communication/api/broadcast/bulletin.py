# communication/api/broadcast/bulletin.py

from typing import List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, Query

from sqlalchemy.orm import Session

from app.deps.auth import get_current_user
from app.deps.common import get_db

from communication.services.broadcast.bulletin_service import BulletinService
from communication.models.broadcast import Bulletin


router = APIRouter(prefix="/bulletins", tags=["Bulletins"])

service = BulletinService()


# ---------------------------------------------------------
# Create Bulletin
# ---------------------------------------------------------

@router.post("/", response_model=Bulletin)
def create_bulletin(
    title: str,
    content: str,
    category: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.create_bulletin(
        db=db,
        school_id=current_user.school_id,
        title=title,
        content=content,
        category=category,
        published_by_id=current_user.id,
    )


# ---------------------------------------------------------
# Publish Bulletin
# ---------------------------------------------------------

@router.post("/{bulletin_id}/publish")
def publish_bulletin(
    bulletin_id: UUID,
    db: Session = Depends(get_db),
):
    service.publish(
        db=db,
        bulletin_id=bulletin_id,
        published_at=datetime.utcnow(),
    )
    return {"success": True}


# ---------------------------------------------------------
# Unpublish Bulletin
# ---------------------------------------------------------

@router.post("/{bulletin_id}/unpublish")
def unpublish_bulletin(
    bulletin_id: UUID,
    db: Session = Depends(get_db),
):
    service.unpublish(
        db=db,
        bulletin_id=bulletin_id,
    )
    return {"success": True}


# ---------------------------------------------------------
# Get Active Bulletins
# ---------------------------------------------------------

@router.get("/active", response_model=List[Bulletin])
def get_active_bulletins(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    skip: int = 0,
    limit: int = Query(20, le=100),
):
    return service.get_active(
        db=db,
        school_id=current_user.school_id,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------
# Get by Category
# ---------------------------------------------------------

@router.get("/category/{category}", response_model=List[Bulletin])
def get_by_category(
    category: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    skip: int = 0,
    limit: int = Query(20, le=100),
):
    return service.get_by_category(
        db=db,
        school_id=current_user.school_id,
        category=category,
        skip=skip,
        limit=limit,
    )