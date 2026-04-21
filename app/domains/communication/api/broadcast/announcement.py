# communication/api/broadcast/announcement.py

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from sqlalchemy.orm import Session

from app.deps.auth import get_current_user
from app.deps.common import get_db

from communication.schemas.announcement import (
    AnnouncementCreate,
    AnnouncementResponse,
)

from communication.services.broadcast.announcement_service import AnnouncementService
from communication.services.common.audience_filter import AudienceFilter
from communication.workflows.broadcast.publish_announcement import PublishAnnouncementWorkflow


router = APIRouter(prefix="/announcements", tags=["Announcements"])

service = AnnouncementService()
workflow = PublishAnnouncementWorkflow()
audience_filter = AudienceFilter()


# ---------------------------------------------------------
# Create Announcement
# ---------------------------------------------------------

@router.post("/", response_model=AnnouncementResponse)
def create_announcement(
    payload: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    announcement = workflow.execute(
        db=db,
        school_id=current_user.school_id,
        title=payload.title,
        content=payload.content,
        announcement_type=payload.announcement_type,
        published_by_id=current_user.id,
        published_at=payload.published_at,
        category=payload.category,
        target_roles=payload.target_roles,
        target_classes=payload.target_class_ids,
        target_sections=payload.target_section_ids,
        expires_at=payload.expires_at,
        is_pinned=payload.is_pinned,
        priority=payload.priority,
        attachments=[a.model_dump() for a in payload.attachments],
    )

    return announcement


# ---------------------------------------------------------
# Get Active Announcements (with audience filter)
# ---------------------------------------------------------

@router.get("/active", response_model=List[AnnouncementResponse])
def get_active_announcements(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    skip: int = 0,
    limit: int = Query(20, le=100),
):
    announcements = service.get_active(
        db=db,
        school_id=current_user.school_id,
        skip=skip,
        limit=limit,
    )

    return audience_filter.filter_announcements(
        announcements,
        user_role=current_user.role,  # depends on your user model
        class_id=getattr(current_user, "class_id", None),
        section_id=getattr(current_user, "section_id", None),
    )


# ---------------------------------------------------------
# Get Pinned
# ---------------------------------------------------------

@router.get("/pinned", response_model=List[AnnouncementResponse])
def get_pinned(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    skip: int = 0,
    limit: int = Query(20, le=100),
):
    return service.get_pinned(
        db=db,
        school_id=current_user.school_id,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------
# Filter by Type
# ---------------------------------------------------------

@router.get("/type/{announcement_type}", response_model=List[AnnouncementResponse])
def get_by_type(
    announcement_type: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    skip: int = 0,
    limit: int = Query(20, le=100),
):
    return service.get_by_type(
        db=db,
        school_id=current_user.school_id,
        announcement_type=announcement_type,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------
# Filter by Category
# ---------------------------------------------------------

@router.get("/category/{category}", response_model=List[AnnouncementResponse])
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