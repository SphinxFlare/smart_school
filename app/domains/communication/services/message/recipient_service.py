# communication/services/message/recipient_service.py

from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from communication.models.messaging import MessageRecipient
from communication.repositories.message.messaging_repository import MessageRecipientRepository


class RecipientService:
    """
    Service responsible for MessageRecipient (delivery layer).

    Responsibilities:
    - Add recipients (deduplicated)
    - Inbox retrieval
    - Unread / starred retrieval
    - Read state transitions

    Does NOT handle:
    - message creation
    - recipient resolution (handled by resolver)
    - workflows/events
    """

    def __init__(self):
        self.repo = MessageRecipientRepository()

    # ---------------------------------------------------------
    # Create
    # ---------------------------------------------------------

    def add_recipients(
        self,
        db: Session,
        *,
        message_id: UUID,
        recipient_ids: List[UUID],
        recipient_role: str | None = None,
    ) -> List[MessageRecipient]:
        """
        Add recipients to a message.

        Rules:
        - recipient_ids must not be empty
        - deduplicate before insert
        - avoid duplicates against DB (safety check)
        """

        if not recipient_ids:
            raise ValueError("Recipient list cannot be empty")

        unique_ids = set(recipient_ids)

        recipients: List[MessageRecipient] = []

        for user_id in unique_ids:
            # prevent duplicate insert (DB-level safety)
            if self.repo.exists_by_message_and_recipient(db, message_id, user_id):
                continue

            recipients.append(
                MessageRecipient(
                    message_id=message_id,
                    recipient_id=user_id,
                    recipient_role=recipient_role,
                )
            )

        if recipients:
            db.add_all(recipients)
            db.flush()

        return recipients

    # ---------------------------------------------------------
    # Inbox / Retrieval
    # ---------------------------------------------------------

    def get_inbox(
        self,
        db: Session,
        recipient_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[MessageRecipient]:
        return self.repo.list_inbox_messages(db, recipient_id, skip, limit)

    def get_unread_messages(
        self,
        db: Session,
        recipient_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[MessageRecipient]:
        return self.repo.list_unread_messages(db, recipient_id, skip, limit)

    def get_starred_messages(
        self,
        db: Session,
        recipient_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[MessageRecipient]:
        return self.repo.list_starred_messages(db, recipient_id, skip, limit)

    def count_unread(
        self,
        db: Session,
        recipient_id: UUID
    ) -> int:
        return self.repo.count_unread_messages(db, recipient_id)

    # ---------------------------------------------------------
    # Read State
    # ---------------------------------------------------------

    def mark_as_read(
        self,
        db: Session,
        *,
        recipient_id: UUID,
        message_id: UUID
    ) -> bool:
        return self.repo.mark_as_read(db, recipient_id, message_id)

    def bulk_mark_as_read(
        self,
        db: Session,
        *,
        recipient_id: UUID,
        message_ids: List[UUID]
    ) -> int:
        if not message_ids:
            return 0

        return self.repo.bulk_mark_as_read(db, recipient_id, message_ids)