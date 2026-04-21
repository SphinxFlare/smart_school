# communication/api/notification/preference.py

from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.deps.auth import get_current_user
from app.deps.common import get_db

from communication.schemas.notification import NotificationPreferenceUpdate
from communication.models.notifications import NotificationPreference

from communication.services.notification.preference_service import PreferenceService


router = APIRouter(prefix="/preferences", tags=["Notification Preferences"])

service = PreferenceService()


# ---------------------------------------------------------
# Get Preferences
# ---------------------------------------------------------

@router.get("/", response_model=NotificationPreference)
def get_preferences(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    pref = service.get_or_create(
        db=db,
        user_id=current_user.id,
    )
    return pref


# ---------------------------------------------------------
# Update Preferences
# ---------------------------------------------------------

@router.put("/", response_model=NotificationPreference)
def update_preferences(
    payload: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    updated = service.update_preferences(
        db=db,
        user_id=current_user.id,  # ignore payload.user_id
        email_enabled=payload.email_enabled,
        sms_enabled=payload.sms_enabled,
        push_enabled=payload.push_enabled,
        in_app_enabled=payload.in_app_enabled,
        transport_notifications=payload.transport_notifications,
        attendance_notifications=payload.attendance_notifications,
        exam_notifications=payload.exam_notifications,
        fee_notifications=payload.fee_notifications,
        concern_notifications=payload.concern_notifications,
        message_notifications=payload.message_notifications,
        system_notifications=payload.system_notifications,
        quiet_hours_enabled=payload.quiet_hours_enabled,
        quiet_hours_start=payload.quiet_hours_start,
        quiet_hours_end=payload.quiet_hours_end,
    )

    return updated