# communication/api/notification/notification.py

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from sqlalchemy.orm import Session

from app.deps.auth import get_current_user
from app.deps.common import get_db

from communication.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
)

from communication.services.notification.notification_service import NotificationService
from communication.workflows.notification.dispatch_notification import DispatchNotificationWorkflow


router = APIRouter(prefix="/notifications", tags=["Notifications"])

service = NotificationService()
workflow = DispatchNotificationWorkflow()


# ---------------------------------------------------------
# Dispatch Notification
# ---------------------------------------------------------

@router.post("/", response_model=NotificationResponse)
def dispatch_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notification = workflow.execute(
        db=db,
        school_id=current_user.school_id,
        user_id=current_user.id,  # ignore payload.user_id
        title=payload.title,
        message=payload.message,
        notification_type=payload.notification_type,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        action_url=payload.action_url,
        priority=payload.priority,
    )

    return notification


# ---------------------------------------------------------
# Get Notifications
# ---------------------------------------------------------

@router.get("/", response_model=List[NotificationResponse])
def get_notifications(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    notification_type: Optional[str] = None,
    priority: Optional[str] = None,
    is_read: Optional[bool] = None,
    skip: int = 0,
    limit: int = Query(20, le=100),
):
    return service.get_notifications(
        db=db,
        user_id=current_user.id,
        notification_type=notification_type,
        priority=priority,
        is_read=is_read,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------
# Mark as Read
# ---------------------------------------------------------

@router.post("/{notification_id}/read")
def mark_as_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    success = service.mark_as_read(
        db=db,
        user_id=current_user.id,
        notification_id=notification_id,
    )

    return {"success": success}


# ---------------------------------------------------------
# Unread Count
# ---------------------------------------------------------

@router.get("/unread/count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    count = service.count_unread(
        db=db,
        user_id=current_user.id,
    )

    return {"unread_count": count}