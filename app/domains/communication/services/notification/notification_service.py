# communication/services/notification/notification_service.py

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from communication.models.notifications import Notification
from communication.repositories.notification.notification_repository import NotificationRepository


class NotificationService:
    """
    Service responsible for Notification lifecycle.

    Responsibilities:
    - Create notification
    - Retrieve notifications
    - Read state management

    Notes:
    - User-scoped (NOT school-scoped)
    - Time-based visibility handled in repo
    """

    def __init__(self):
        self.repo = NotificationRepository()

    # ---------------------------------------------------------
    # Create
    # ---------------------------------------------------------

    def create_notification(
        self,
        db: Session,
        *,
        user_id: UUID,
        title: str,
        message: str,
        notification_type: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        action_url: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        priority: str = "normal",
    ) -> Notification:
        """
        Create notification.

        Rules:
        - title, message, notification_type required
        """

        if not title or not title.strip():
            raise ValueError("Title cannot be empty")

        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        if not notification_type:
            raise ValueError("notification_type is required")

        notification = Notification(
            user_id=user_id,
            title=title.strip(),
            message=message.strip(),
            notification_type=notification_type,
            entity_type=entity_type,
            entity_id=entity_id,
            action_url=action_url,
            expires_at=expires_at,
            priority=priority,
        )

        return self.repo.create(db, notification)

    # ---------------------------------------------------------
    # Retrieval
    # ---------------------------------------------------------

    def get_notifications(
        self,
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        return self.repo.list_by_user(db, user_id, skip, limit)

    def get_unread_notifications(
        self,
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        return self.repo.list_unread_notifications(db, user_id, skip, limit)

    def get_by_type(
        self,
        db: Session,
        user_id: UUID,
        notification_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        return self.repo.filter_by_notification_type(
            db, user_id, notification_type, skip, limit
        )

    def get_active_notifications(
        self,
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        return self.repo.filter_active_notifications(db, user_id, skip, limit)

    def count_unread(
        self,
        db: Session,
        user_id: UUID
    ) -> int:
        return self.repo.count_unread_notifications(db, user_id)

    # ---------------------------------------------------------
    # Read State
    # ---------------------------------------------------------

    def mark_as_read(
        self,
        db: Session,
        *,
        notification_id: UUID,
        user_id: UUID
    ) -> bool:
        return self.repo.mark_as_read(db, notification_id, user_id)

    def bulk_mark_as_read(
        self,
        db: Session,
        *,
        user_id: UUID,
        notification_ids: List[UUID]
    ) -> int:
        if not notification_ids:
            return 0

        return self.repo.bulk_mark_as_read(db, user_id, notification_ids)