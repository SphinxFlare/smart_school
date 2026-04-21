# communication/events/handlers.py

from typing import Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session

from communication.events.topics import CommunicationTopics

from communication.services.notification.notification_service import NotificationService
from communication.services.notification.delivery_service import DeliveryService
from communication.services.audit.communication_log_service import CommunicationLogService


class CommunicationEventHandler:
    """
    Handles communication domain events.

    This class is invoked by the event worker.
    """

    def __init__(self, db: Session):
        self.db = db

        self.notification_service = NotificationService()
        self.delivery_service = DeliveryService()
        self.log_service = CommunicationLogService()

    # ---------------------------------------------------------
    # Entry Point
    # ---------------------------------------------------------

    def handle(self, topic: str, payload: Dict[str, Any]) -> None:
        """
        Dispatch event to correct handler.
        """

        if topic == CommunicationTopics.MESSAGE_SENT:
            self._handle_message_sent(payload)

        elif topic == CommunicationTopics.NOTIFICATION_DISPATCH:
            self._handle_notification_dispatch(payload)

        elif topic == CommunicationTopics.ANNOUNCEMENT_PUBLISHED:
            self._handle_announcement_published(payload)

        else:
            # unknown event → ignore safely
            return

    # ---------------------------------------------------------
    # Handlers
    # ---------------------------------------------------------

    def _handle_message_sent(self, payload: Dict[str, Any]) -> None:
        """
        Trigger notifications for message recipients.
        """

        recipient_ids = payload.get("recipient_ids", [])
        sender_id = payload.get("sender_id")
        message_id = payload.get("message_id")

        for rid in recipient_ids:
            self.notification_service.create_notification(
                db=self.db,
                user_id=UUID(rid),
                title="New Message",
                message="You have received a new message",
                notification_type="message",
                entity_type="message",
                entity_id=UUID(message_id),
            )

    def _handle_notification_dispatch(self, payload: Dict[str, Any]) -> None:
        """
        Final dispatch layer (infra trigger point).
        """

        user_id = UUID(payload["user_id"])
        channels = payload.get("channels", [])

        # Here is where external integrations would happen
        # (push/email/sms). Keeping it abstract for now.

        # Log delivery attempt
        self.log_service.create_log(
            db=self.db,
            school_id=None,  # optional if not available
            communication_type="notification",
            entity_type="notification",
            entity_id=UUID(payload["notification_id"]),
            recipient_ids=[user_id],
            channel=",".join(channels) if channels else None,
            status="sent",
        )

    def _handle_announcement_published(self, payload: Dict[str, Any]) -> None:
        """
        Future: fan-out announcement notifications.
        Currently left minimal by design.
        """

        # Intentionally minimal:
        # - you may later trigger:
        #   - bulk notifications
        #   - websocket broadcast
        #   - cache invalidation

        pass