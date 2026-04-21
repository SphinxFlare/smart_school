# communication/api/broadcast/feed.py

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, Query

from sqlalchemy.orm import Session

from app.deps.auth import get_current_user
from app.deps.common import get_db

from communication.services.broadcast.feed_service import FeedService
from communication.models.broadcast import DailyFeed


router = APIRouter(prefix="/feeds", tags=["Feeds"])

service = FeedService()


# ---------------------------------------------------------
# Get Feed (basic + filters)
# ---------------------------------------------------------

@router.get("/", response_model=List[DailyFeed])
def get_feed(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    item_type: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(20, le=100),
):
    return service.get_feed(
        db=db,
        school_id=current_user.school_id,
        date_from=date_from,
        date_to=date_to,
        item_type=item_type,
        priority=priority,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------
# Mark Feed as Read
# ---------------------------------------------------------

@router.post("/{feed_id}/read")
def mark_feed_as_read(
    feed_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    success = service.mark_as_read(
        db=db,
        feed_id=feed_id,
        user_id=current_user.id,
    )

    return {"success": success}


# ---------------------------------------------------------
# Get Unread Count
# ---------------------------------------------------------

@router.get("/unread/count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    count = service.count_unread(
        db=db,
        school_id=current_user.school_id,
        user_id=current_user.id,
    )

    return {"unread_count": count}


# ---------------------------------------------------------
# Create Feed (internal/admin use)
# ---------------------------------------------------------

@router.post("/", response_model=DailyFeed)
def create_feed(
    school_id: UUID,
    feed_date: datetime,
    item_type: str,
    source_type: str,
    source_id: UUID,
    title: str,
    summary: Optional[str] = None,
    priority: str = "normal",
    db: Session = Depends(get_db),
):
    return service.create_feed(
        db=db,
        school_id=school_id,
        feed_date=feed_date,
        item_type=item_type,
        source_type=source_type,
        source_id=source_id,
        title=title,
        summary=summary,
        priority=priority,
    )