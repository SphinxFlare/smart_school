# communication/services/notification/preference_service.py

from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session

from communication.models.notifications import NotificationPreference
from communication.repositories.notification.notification_repository import NotificationPreferenceRepository


class PreferenceService:
    """
    Service responsible for NotificationPreference.

    Responsibilities:
    - Get user preferences
    - Create default preferences (if needed)
    - Update preferences safely (with locking)

    Notes:
    - One row per user (enforced by DB)
    - Uses row-level locking for updates
    """

    def __init__(self):
        self.repo = NotificationPreferenceRepository()

    # ---------------------------------------------------------
    # Get
    # ---------------------------------------------------------

    def get_preferences(
        self,
        db: Session,
        user_id: UUID
    ) -> Optional[NotificationPreference]:
        return self.repo.get_by_user(db, user_id)

    # ---------------------------------------------------------
    # Create (default)
    # ---------------------------------------------------------

    def create_default_preferences(
        self,
        db: Session,
        user_id: UUID
    ) -> NotificationPreference:
        """
        Create default preferences for a user.

        Assumes:
        - DB enforces unique(user_id)
        """

        existing = self.repo.get_by_user(db, user_id)
        if existing:
            return existing

        preference = NotificationPreference(user_id=user_id)

        return self.repo.create(db, preference)

    # ---------------------------------------------------------
    # Update
    # ---------------------------------------------------------

    def update_preferences(
        self,
        db: Session,
        *,
        user_id: UUID,
        updates: Dict[str, Any]
    ) -> NotificationPreference:
        """
        Update preferences safely.

        Flow:
        - lock row
        - apply only valid fields (handled by repo)
        - flush

        Raises:
        - if preference does not exist
        """

        preference = self.repo.update_preferences(db, user_id, updates)

        if not preference:
            raise ValueError("Notification preferences not found")

        return preference

    # ---------------------------------------------------------
    # Get or Create (utility)
    # ---------------------------------------------------------

    def get_or_create_preferences(
        self,
        db: Session,
        user_id: UUID
    ) -> NotificationPreference:
        """
        Ensures preference row exists.
        """

        preference = self.repo.get_by_user(db, user_id)

        if preference:
            return preference

        preference = NotificationPreference(user_id=user_id)
        return self.repo.create(db, preference)