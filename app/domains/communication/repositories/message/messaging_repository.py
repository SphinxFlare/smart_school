# communication/repositories/message/messaging_repository.py


from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from repositories.base import BaseRepository
from communication.models.messaging import (
    Message,
    MessageRecipient,
    MessageReply,
    ParentTeacherCommunication,
    CallLog
)


# ==========================================================
# Message Repository
# ==========================================================

class MessageRepository(BaseRepository[Message]):
    """
    Repository for Message model operations.
    NOT school-scoped (extends BaseRepository).
    All queries use SQLAlchemy 2.0 select() style with deterministic ordering.
    """

    def __init__(self):
        super().__init__(Message)

    # -----------------------------------------
    # Sent Messages
    # -----------------------------------------

    def get_sent_messages(
        self,
        db: Session,
        sender_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        """
        Retrieve non-draft sent messages ordered by sent_at DESC, id DESC.
        Filters: sender_id, is_draft=False, sent_at IS NOT NULL.
        Soft-delete aware.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.sender_id == sender_id,
                self.model.is_draft.is_(False),
                self.model.sent_at.is_not(None)
            )
            .order_by(
                self.model.sent_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Draft Messages
    # -----------------------------------------

    def list_drafts_by_sender(
        self,
        db: Session,
        sender_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        """
        List drafts by sender ordered by created_at DESC, id DESC.
        Soft-delete aware.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.sender_id == sender_id,
                self.model.is_draft.is_(True)
            )
            .order_by(
                self.model.created_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Context Filtering
    # -----------------------------------------

    def filter_by_context(
        self,
        db: Session,
        context_type: str,
        context_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        """
        Filter messages by context_type/context_id.
        Uses composite index on (context_type, context_id).
        Ordered by sent_at DESC, id DESC.
        Soft-delete aware.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.context_type == context_type,
                self.model.context_id == context_id
            )
            .order_by(
                self.model.sent_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Conversation Thread
    # -----------------------------------------

    def list_conversation_thread(
        self,
        db: Session,
        context_type: str,
        context_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        """
        List conversation thread by context (context_type, context_id, is_two_way=True).
        NOT by message id - this retrieves all messages in the same context.
        Ordered by sent_at ASC, id ASC for chronological thread order.
        Soft-delete aware.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.context_type == context_type,
                self.model.context_id == context_id,
                self.model.is_two_way.is_(True)
            )
            .order_by(
                self.model.sent_at.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Count Operations
    # -----------------------------------------

    def count_messages_by_user(
        self,
        db: Session,
        user_id: UUID
    ) -> int:
        """
        Count messages sent by a user (non-draft only).
        Null-safe aggregation with soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.sender_id == user_id,
                self.model.is_draft.is_(False)
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # Row Locking
    # -----------------------------------------

    def lock_message_for_update(
        self,
        db: Session,
        message_id: UUID
    ) -> Optional[Message]:
        """
        Lock a message for update to prevent concurrent modifications.
        Uses with_for_update() and soft-delete filtering.
        """
        stmt = (
            select(self.model)
            .where(self.model.id == message_id)
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()


# ==========================================================
# Message Recipient Repository
# ==========================================================

class MessageRecipientRepository(BaseRepository[MessageRecipient]):
    """
    Repository for MessageRecipient model operations.
    NOT school-scoped (extends BaseRepository).
    All joins explicitly exclude soft-deleted Message rows.
    """

    def __init__(self):
        super().__init__(MessageRecipient)

    # -----------------------------------------
    # Existence Checks
    # -----------------------------------------

    def exists_by_message_and_recipient(
        self,
        db: Session,
        message_id: UUID,
        recipient_id: UUID
    ) -> bool:
        """
        Enforce uniqueness integrity via efficient existence check.
        Uses select(self.model.id).limit(1) for performance.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.message_id == message_id,
                self.model.recipient_id == recipient_id
            )
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    # -----------------------------------------
    # Inbox Operations
    # -----------------------------------------

    def list_inbox_messages(
        self,
        db: Session,
        recipient_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[MessageRecipient]:
        """
        List inbox messages for a recipient.
        Joins Message explicitly, filters deleted_by_recipient=False.
        Explicitly excludes soft-deleted Message rows (Message.is_deleted=False).
        Ordered by Message.sent_at DESC, MessageRecipient.id DESC.
        """
        stmt = (
            select(self.model)
            .join(Message, self.model.message_id == Message.id)
            .where(
                self.model.recipient_id == recipient_id,
                self.model.deleted_by_recipient.is_(False),
                Message.is_deleted.is_(False)
            )
            .order_by(
                Message.sent_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_unread_messages(
        self,
        db: Session,
        recipient_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[MessageRecipient]:
        """
        List unread messages for a recipient.
        Uses index on is_read.
        Explicitly excludes soft-deleted Message rows.
        Ordered by Message.sent_at DESC, MessageRecipient.id DESC.
        """
        stmt = (
            select(self.model)
            .join(Message, self.model.message_id == Message.id)
            .where(
                self.model.recipient_id == recipient_id,
                self.model.is_read.is_(False),
                self.model.deleted_by_recipient.is_(False),
                Message.is_deleted.is_(False)
            )
            .order_by(
                Message.sent_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def count_unread_messages(
        self,
        db: Session,
        recipient_id: UUID
    ) -> int:
        """
        Count unread messages efficiently using indexed fields only.
        Null-safe aggregation.
        Explicitly excludes soft-deleted Message rows.
        """
        stmt = (
            select(func.count(self.model.id))
            .join(Message, self.model.message_id == Message.id)
            .where(
                self.model.recipient_id == recipient_id,
                self.model.is_read.is_(False),
                self.model.deleted_by_recipient.is_(False),
                Message.is_deleted.is_(False)
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def list_starred_messages(
        self,
        db: Session,
        recipient_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[MessageRecipient]:
        """
        List starred messages for a recipient.
        Explicitly excludes soft-deleted Message rows.
        Ordered by Message.sent_at DESC, MessageRecipient.id DESC.
        """
        stmt = (
            select(self.model)
            .join(Message, self.model.message_id == Message.id)
            .where(
                self.model.recipient_id == recipient_id,
                self.model.is_starred.is_(True),
                self.model.deleted_by_recipient.is_(False),
                Message.is_deleted.is_(False)
            )
            .order_by(
                Message.sent_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Read Status (Row Locking)
    # -----------------------------------------

    def mark_as_read(
        self,
        db: Session,
        recipient_id: UUID,
        message_id: UUID
    ) -> bool:
        """
        Mark as read with row locking (updating is_read and read_at).
        Returns True if successful.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.recipient_id == recipient_id,
                self.model.message_id == message_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        recipient = result.scalar_one_or_none()

        if recipient:
            recipient.is_read = True
            recipient.read_at = now
            db.flush()
            return True
        return False

    def bulk_mark_as_read(
        self,
        db: Session,
        recipient_id: UUID,
        message_ids: List[UUID]
    ) -> int:
        """
        Bulk mark messages as read for a recipient.
        Returns count of updated rows.
        """
        now = datetime.utcnow()
        stmt = (
            update(self.model)
            .where(
                self.model.recipient_id == recipient_id,
                self.model.message_id.in_(message_ids),
                self.model.is_read.is_(False)
            )
            .values(is_read=True, read_at=now)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0


# ==========================================================
# Message Reply Repository
# ==========================================================

class MessageReplyRepository(BaseRepository[MessageReply]):
    """
    Repository for MessageReply model operations.
    NOT school-scoped (extends BaseRepository).
    All queries use deterministic ordering with stable tie-breakers.
    """

    def __init__(self):
        super().__init__(MessageReply)

    # -----------------------------------------
    # Reply Listing
    # -----------------------------------------

    def list_replies_for_message(
        self,
        db: Session,
        message_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[MessageReply]:
        """
        List replies for a message (top-level replies only).
        Filters: message_id and parent_reply_id IS NULL.
        Ordered by sent_at ASC, id ASC for thread order.
        Soft-delete aware.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.message_id == message_id,
                self.model.parent_reply_id.is_(None)
            )
            .order_by(
                self.model.sent_at.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_child_replies(
        self,
        db: Session,
        parent_reply_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[MessageReply]:
        """
        List child replies by parent_reply_id.
        Uses index on parent_reply_id.
        Ordered by sent_at ASC, id ASC for thread order.
        Soft-delete aware.
        """
        stmt = (
            select(self.model)
            .where(self.model.parent_reply_id == parent_reply_id)
            .order_by(
                self.model.sent_at.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Row Locking
    # -----------------------------------------

    def lock_reply_for_update(
        self,
        db: Session,
        reply_id: UUID
    ) -> Optional[MessageReply]:
        """
        Lock reply row if needed for edit operations.
        Uses with_for_update() and soft-delete filtering.
        """
        stmt = (
            select(self.model)
            .where(self.model.id == reply_id)
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()


# ==========================================================
# Parent Teacher Communication Repository
# ==========================================================

class ParentTeacherCommunicationRepository(BaseRepository[ParentTeacherCommunication]):
    """
    Repository for ParentTeacherCommunication model operations.
    NOT school-scoped (extends BaseRepository).
    All queries use deterministic ordering with stable tie-breakers.
    """

    def __init__(self):
        super().__init__(ParentTeacherCommunication)

    # -----------------------------------------
    # Filtering by Entity
    # -----------------------------------------

    def filter_by_student(
        self,
        db: Session,
        student_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ParentTeacherCommunication]:
        """
        Filter communications by student.
        Uses index on student_id.
        Ordered by communication_date DESC, id DESC.
        Soft-delete aware.
        """
        stmt = (
            select(self.model)
            .where(self.model.student_id == student_id)
            .order_by(
                self.model.communication_date.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def filter_by_teacher(
        self,
        db: Session,
        teacher_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ParentTeacherCommunication]:
        """
        Filter communications by teacher.
        Uses index on teacher_id.
        Ordered by communication_date DESC, id DESC.
        Soft-delete aware.
        """
        stmt = (
            select(self.model)
            .where(self.model.teacher_id == teacher_id)
            .order_by(
                self.model.communication_date.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def filter_by_parent(
        self,
        db: Session,
        parent_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ParentTeacherCommunication]:
        """
        Filter communications by parent.
        Uses index on parent_id.
        Ordered by communication_date DESC, id DESC.
        Soft-delete aware.
        """
        stmt = (
            select(self.model)
            .where(self.model.parent_id == parent_id)
            .order_by(
                self.model.communication_date.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Date Range Filtering
    # -----------------------------------------

    def filter_by_date_range(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[ParentTeacherCommunication]:
        """
        Filter communications by date range.
        Preserves index usage on communication_date.
        Ordered by communication_date DESC, id DESC.
        Soft-delete aware.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.communication_date >= start_date,
                self.model.communication_date <= end_date
            )
            .order_by(
                self.model.communication_date.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Follow-up Filtering
    # -----------------------------------------

    def filter_follow_up_required(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[ParentTeacherCommunication]:
        """
        Filter communications requiring follow-up.
        Ordered by communication_date DESC, id DESC.
        Soft-delete aware.
        """
        stmt = (
            select(self.model)
            .where(self.model.follow_up_required.is_(True))
            .order_by(
                self.model.communication_date.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def filter_upcoming_follow_ups(
        self,
        db: Session,
        reference_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[ParentTeacherCommunication]:
        """
        Filter upcoming follow-ups.
        Filters: follow_up_required=True AND follow_up_date IS NOT NULL AND follow_up_date >= reference_date.
        Ordered by follow_up_date ASC, id ASC.
        Soft-delete aware.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.follow_up_required.is_(True),
                self.model.follow_up_date.is_not(None),
                self.model.follow_up_date >= reference_date
            )
            .order_by(
                self.model.follow_up_date.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Row Locking
    # -----------------------------------------

    def lock_for_update(
        self,
        db: Session,
        communication_id: UUID
    ) -> Optional[ParentTeacherCommunication]:
        """
        Lock for updates to prevent concurrent modifications.
        Uses with_for_update() and soft-delete filtering.
        """
        stmt = (
            select(self.model)
            .where(self.model.id == communication_id)
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()


# ==========================================================
# Call Log Repository
# ==========================================================

class CallLogRepository(BaseRepository[CallLog]):
    """
    Repository for CallLog model operations.
    NOT school-scoped (extends BaseRepository).
    NOTE: CallLog model does NOT have is_deleted, so NO soft-delete filtering.
    All queries use deterministic ordering with stable tie-breakers.
    """

    def __init__(self):
        super().__init__(CallLog)

    # -----------------------------------------
    # Filtering by Caller/Callee
    # -----------------------------------------

    def filter_by_caller(
        self,
        db: Session,
        caller_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[CallLog]:
        """
        Filter call logs by caller.
        Uses index on caller_id.
        Ordered by call_started_at DESC, id DESC.
        NO soft-delete filter (model lacks is_deleted).
        """
        stmt = (
            select(self.model)
            .where(self.model.caller_id == caller_id)
            .order_by(
                self.model.call_started_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def filter_by_callee(
        self,
        db: Session,
        callee_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[CallLog]:
        """
        Filter call logs by callee.
        Uses index on callee_id.
        Ordered by call_started_at DESC, id DESC.
        NO soft-delete filter (model lacks is_deleted).
        """
        stmt = (
            select(self.model)
            .where(self.model.callee_id == callee_id)
            .order_by(
                self.model.call_started_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def filter_by_student(
        self,
        db: Session,
        student_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[CallLog]:
        """
        Filter call logs by student.
        Uses index on student_id.
        Ordered by call_started_at DESC, id DESC.
        NO soft-delete filter (model lacks is_deleted).
        """
        stmt = (
            select(self.model)
            .where(self.model.student_id == student_id)
            .order_by(
                self.model.call_started_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Date Range Filtering
    # -----------------------------------------

    def filter_by_date_range(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[CallLog]:
        """
        Filter call logs by date range.
        Preserves index usage on call_started_at.
        Ordered by call_started_at DESC, id DESC.
        NO soft-delete filter (model lacks is_deleted).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.call_started_at >= start_date,
                self.model.call_started_at <= end_date
            )
            .order_by(
                self.model.call_started_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Call Type Filtering
    # -----------------------------------------

    def filter_by_call_type(
        self,
        db: Session,
        call_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[CallLog]:
        """
        Filter call logs by call_type.
        Ordered by call_started_at DESC, id DESC.
        NO soft-delete filter (model lacks is_deleted).
        """
        stmt = (
            select(self.model)
            .where(self.model.call_type == call_type)
            .order_by(
                self.model.call_started_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())
