# communication/services/notification/delivery_service.py

from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from communication.models.notifications import Notification
from communication.services.notification.preference_service import PreferenceService


class DeliveryService:
    """
    Service responsible for delivery decision logic.

    Responsibilities:
    - Decide delivery channels (in_app, email, sms, push)
    - Respect user preferences
    - Respect quiet hours
    - Prepare delivery plan (NOT actually send)

    Does NOT:
    - send notifications (handled by handlers / infra)
    - create notifications
    - access external systems
    """

    def __init__(self):
        self.preference_service = PreferenceService()

    # ---------------------------------------------------------
    # Channel Resolution
    # ---------------------------------------------------------

    def resolve_channels(
        self,
        db: Session,
        *,
        user_id: UUID,
        notification_type: str,
    ) -> List[str]:
        """
        Determine allowed delivery channels for a notification.

        Returns:
        - list of channels ["in_app", "email", "sms", "push"]
        """

        pref = self.preference_service.get_or_create_preferences(db, user_id)

        channels: List[str] = []

        # ---------- Global channel toggles ----------

        if pref.in_app_enabled:
            channels.append("in_app")

        if pref.email_enabled:
            channels.append("email")

        if pref.sms_enabled:
            channels.append("sms")

        if pref.push_enabled:
            channels.append("push")

        # ---------- Type-based filtering ----------

        type_map = {
            "transport": pref.transport_notifications,
            "attendance": pref.attendance_notifications,
            "exam": pref.exam_notifications,
            "fee": pref.fee_notifications,
            "concern": pref.concern_notifications,
            "message": pref.message_notifications,
            "system": pref.system_notifications,
        }

        if notification_type in type_map and not type_map[notification_type]:
            return []  # user disabled this type entirely

        # ---------- Quiet hours ----------

        if pref.quiet_hours_enabled:
            if self._is_quiet_hours(pref.quiet_hours_start, pref.quiet_hours_end):
                # allow only in_app during quiet hours
                return ["in_app"] if "in_app" in channels else []

        return channels

    # ---------------------------------------------------------
    # Delivery Plan
    # ---------------------------------------------------------

    def build_delivery_plan(
        self,
        db: Session,
        *,
        notification: Notification
    ) -> dict:
        """
        Build delivery plan for a notification.

        Returns:
        {
            "user_id": ...,
            "channels": [...],
            "notification_id": ...
        }
        """

        channels = self.resolve_channels(
            db=db,
            user_id=notification.user_id,
            notification_type=notification.notification_type,
        )

        return {
            "user_id": str(notification.user_id),
            "notification_id": str(notification.id),
            "channels": channels,
        }

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def _is_quiet_hours(
        self,
        start: str,
        end: str
    ) -> bool:
        """
        Check if current time is within quiet hours.

        Format: "HH:MM"
        """

        if not start or not end:
            return False

        from datetime import datetime

        now = datetime.utcnow().time()

        start_time = datetime.strptime(start, "%H:%M").time()
        end_time = datetime.strptime(end, "%H:%M").time()

        # handles overnight ranges (e.g., 22:00 → 07:00)
        if start_time < end_time:
            return start_time <= now <= end_time
        else:
            return now >= start_time or now <= end_time