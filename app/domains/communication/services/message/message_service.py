# communication/services/message/message_service.py

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from communication.models.messaging import Message
from communication.repositories.message.messaging_repository import MessageRepository


class MessageService:
    """
    Service responsible for Message entity lifecycle.

    Responsibilities:
    - Create (draft / sent)
    - Retrieve (single, lists, context)
    - State transitions (draft → sent)
    - Soft delete

    Does NOT handle:
    - recipients
    - replies
    - workflows/events
    """

    def __init__(self):
        self.repo = MessageRepository()

    # ---------------------------------------------------------
    # Create
    # ---------------------------------------------------------

    def create_message(
        self,
        db: Session,
        *,
        sender_id: UUID,
        body: str,
        subject: Optional[str] = None,
        context_type: Optional[str] = None,
        context_id: Optional[UUID] = None,
        is_two_way: bool = True,
        allow_replies: bool = True,
        priority: str = "normal",
        attachments: Optional[dict] = None,
        is_draft: bool = False,
    ) -> Message:
        """
        Create a message.

        Rules:
        - body must not be empty
        - context_type and context_id must be provided together
        - draft → sent_at = None
        - sent → sent_at = now
        """

        # ---------- Validation ----------

        if not body or not body.strip():
            raise ValueError("Message body cannot be empty")

        if (context_type and not context_id) or (context_id and not context_type):
            raise ValueError("context_type and context_id must be provided together")

        # ---------- State ----------

        sent_at = None if is_draft else datetime.utcnow()

        message = Message(
            sender_id=sender_id,
            subject=subject,
            body=body.strip(),
            context_type=context_type,
            context_id=context_id,
            is_two_way=is_two_way,
            allow_replies=allow_replies,
            priority=priority,
            attachments=attachments,
            sent_at=sent_at,
            is_draft=is_draft,
        )

        return self.repo.create(db, message)

    # ---------------------------------------------------------
    # Retrieval
    # ---------------------------------------------------------

    def get_message(
        self,
        db: Session,
        message_id: UUID
    ) -> Optional[Message]:
        return self.repo.get(db, message_id)

    def get_sent_messages(
        self,
        db: Session,
        sender_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        return self.repo.get_sent_messages(db, sender_id, skip, limit)

    def get_drafts(
        self,
        db: Session,
        sender_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        return self.repo.list_drafts_by_sender(db, sender_id, skip, limit)

    def get_by_context(
        self,
        db: Session,
        context_type: str,
        context_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        return self.repo.filter_by_context(db, context_type, context_id, skip, limit)

    def get_conversation_thread(
        self,
        db: Session,
        context_type: str,
        context_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        return self.repo.list_conversation_thread(db, context_type, context_id, skip, limit)

    def count_sent_messages(
        self,
        db: Session,
        user_id: UUID
    ) -> int:
        return self.repo.count_messages_by_user(db, user_id)

    # ---------------------------------------------------------
    # State Transition
    # ---------------------------------------------------------

    def publish_draft(
        self,
        db: Session,
        message_id: UUID
    ) -> Message:
        """
        Convert draft → sent.

        Uses row locking to ensure consistency.
        """

        message = self.repo.lock_message_for_update(db, message_id)

        if not message:
            raise ValueError("Message not found")

        if not message.is_draft:
            raise ValueError("Message is already sent")

        message.is_draft = False
        message.sent_at = datetime.utcnow()

        db.flush()

        return message

    # ---------------------------------------------------------
    # Delete
    # ---------------------------------------------------------

    def delete_message(
        self,
        db: Session,
        message_id: UUID
    ) -> None:
        message = self.repo.get(db, message_id)

        if not message:
            raise ValueError("Message not found")

        self.repo.delete(db, message)