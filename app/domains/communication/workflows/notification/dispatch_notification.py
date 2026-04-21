# communication/workflows/notification/dispatch_notification.py

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from communication.services.notification.notification_service import NotificationService
from communication.services.notification.delivery_service import DeliveryService
from communication.services.audit.communication_log_service import CommunicationLogService

from app.events.base import Event
from app.events.outbox.repository import OutboxRepository


class DispatchNotificationWorkflow:
    """
    Orchestrates notification dispatch.

    Flow:
    - create notification
    - resolve delivery channels
    - create communication log
    - write outbox event
    """

    def __init__(self):
        self.notification_service = NotificationService()
        self.delivery_service = DeliveryService()
        self.log_service = CommunicationLogService()

    def execute(
        self,
        db: Session,
        *,
        school_id: UUID,
        user_id: UUID,
        title: str,
        message: str,
        notification_type: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        action_url: Optional[str] = None,
        priority: str = "normal",
    ):
        # -----------------------------------------------------
        # Step 1: Create Notification
        # -----------------------------------------------------

        notification = self.notification_service.create_notification(
            db=db,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            entity_type=entity_type,
            entity_id=entity_id,
            action_url=action_url,
            priority=priority,
        )

        # -----------------------------------------------------
        # Step 2: Resolve Delivery Channels
        # -----------------------------------------------------

        channels = self.delivery_service.resolve_channels(
            db=db,
            user_id=user_id,
            notification_type=notification_type,
        )

        # -----------------------------------------------------
        # Step 3: Create Communication Log
        # -----------------------------------------------------

        status = "queued" if channels else "skipped"

        self.log_service.create_log(
            db=db,
            school_id=school_id,
            communication_type="notification",
            entity_type="notification",
            entity_id=notification.id,
            sender_id=None,
            recipient_ids=[user_id],
            channel=",".join(channels) if channels else None,
            status=status,
            metadata={
                "notification_type": notification_type,
                "priority": priority,
            },
        )

        # -----------------------------------------------------
        # Step 4: Outbox Event (only if channels exist)
        # -----------------------------------------------------

        if channels:
            event = Event(
                topic="communication.notification.dispatch",
                payload={
                    "notification_id": str(notification.id),
                    "user_id": str(user_id),
                    "channels": channels,
                    "title": title,
                    "message": message,
                    "priority": priority,
                },
            )

            outbox = OutboxRepository(db)
            outbox.add(event)

        return notification