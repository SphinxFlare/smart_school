# communication/workflows/message/send_message.py

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from communication.services.message.message_service import MessageService
from communication.services.message.recipient_service import RecipientService
from communication.services.common.recipient_resolver import RecipientResolver

from app.events.base import Event
from app.events.outbox.repository import OutboxRepository


class SendMessageWorkflow:
    """
    Orchestrates sending a message.

    Flow:
    - create message
    - if draft → stop
    - resolve recipients
    - validate recipients
    - persist recipients
    - write outbox event
    """

    def __init__(self):
        self.message_service = MessageService()
        self.recipient_service = RecipientService()
        self.resolver = RecipientResolver()

    def execute(
        self,
        db: Session,
        *,
        sender_id: UUID,
        body: str,
        subject: Optional[str] = None,
        user_ids: Optional[List[UUID]] = None,
        roles: Optional[List[str]] = None,
        class_ids: Optional[List[UUID]] = None,
        section_ids: Optional[List[UUID]] = None,
        context_type: Optional[str] = None,
        context_id: Optional[UUID] = None,
        is_two_way: bool = True,
        allow_replies: bool = True,
        priority: str = "normal",
        attachments: Optional[dict] = None,
        is_draft: bool = False,
    ):
        # -----------------------------------------------------
        # Step 1: Create Message
        # -----------------------------------------------------

        message = self.message_service.create_message(
            db=db,
            sender_id=sender_id,
            body=body,
            subject=subject,
            context_type=context_type,
            context_id=context_id,
            is_two_way=is_two_way,
            allow_replies=allow_replies,
            priority=priority,
            attachments=attachments,
            is_draft=is_draft,
        )

        # -----------------------------------------------------
        # Step 2: Draft → stop
        # -----------------------------------------------------

        if is_draft:
            return message

        # -----------------------------------------------------
        # Step 3: Resolve Recipients
        # -----------------------------------------------------

        recipient_ids = self.resolver.resolve(
            db=db,
            user_ids=user_ids,
            roles=roles,
            class_ids=class_ids,
            section_ids=section_ids,
        )

        if not recipient_ids:
            raise ValueError("No recipients resolved")

        # -----------------------------------------------------
        # Step 4: Persist Recipients
        # -----------------------------------------------------

        self.recipient_service.add_recipients(
            db=db,
            message_id=message.id,
            recipient_ids=recipient_ids,
        )

        # -----------------------------------------------------
        # Step 5: Outbox Event
        # -----------------------------------------------------

        event = Event(
            topic="communication.message.sent",
            payload={
                "message_id": str(message.id),
                "sender_id": str(sender_id),
                "recipient_ids": [str(rid) for rid in recipient_ids],
                "context_type": context_type,
                "context_id": str(context_id) if context_id else None,
                "priority": priority,
            },
        )

        outbox = OutboxRepository(db)
        outbox.add(event)

        return message