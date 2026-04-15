# communication/models/messaging.py


from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, Text, Boolean, Integer, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from db.base import Base
import uuid


class Message(Base):
    """
    Role-restricted messaging between users
    """
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    subject = Column(String)
    body = Column(Text, nullable=False)
    context_type = Column(String)  # "attendance", "academics", "concern", "transport", "general"
    context_id = Column(UUID(as_uuid=True))  # ID of related entity (attendance_id, concern_id, etc.)
    is_two_way = Column(Boolean, default=True)  # False = announcement-style, True = conversation
    allow_replies = Column(Boolean, default=True)
    priority = Column(String, default="normal")  # "low", "normal", "high", "urgent"
    attachments = Column(JSONB)
    sent_at = Column(DateTime, default=datetime.utcnow)
    is_draft = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    
    __table_args__ = (
        Index('ix_messages_sender_id', 'sender_id'),
        Index('ix_messages_sent_at', 'sent_at'),
        Index('ix_messages_context', 'context_type', 'context_id'),
    )


class MessageRecipient(Base):
    """
    Message recipients with read/delivery tracking
    """
    __tablename__ = "message_recipients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False)
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    recipient_role = Column(String)  # "student", "parent", "teacher", etc.
    delivery_status = Column(String, default="sent")  # "sent", "delivered", "failed"
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    is_read = Column(Boolean, default=False)
    is_starred = Column(Boolean, default=False)
    deleted_by_recipient = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('message_id', 'recipient_id', name='uq_message_recipient'),
        Index('ix_message_recipients_message_id', 'message_id'),
        Index('ix_message_recipients_recipient_id', 'recipient_id'),
        Index('ix_message_recipients_is_read', 'is_read'),
    )


class MessageReply(Base):
    """
    Replies to messages (for two-way conversations)
    """
    __tablename__ = "message_replies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False)
    parent_reply_id = Column(UUID(as_uuid=True), ForeignKey("message_replies.id"))  # For threading
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    attachments = Column(JSONB)
    sent_at = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_message_replies_message_id', 'message_id'),
        Index('ix_message_replies_parent_reply', 'parent_reply_id'),
        Index('ix_message_replies_sender_id', 'sender_id'),
    )


class ParentTeacherCommunication(Base):
    """
    Dedicated parent-teacher communication tracking
    """
    __tablename__ = "parent_teacher_communications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("staff_members.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("parents.id"), nullable=False)
    communication_date = Column(DateTime, default=datetime.utcnow)
    topic = Column(String, nullable=False)
    description = Column(Text)
    outcome = Column(Text)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    
    __table_args__ = (
        Index('ix_parent_teacher_comm_student', 'student_id'),
        Index('ix_parent_teacher_comm_teacher', 'teacher_id'),
        Index('ix_parent_teacher_comm_parent', 'parent_id'),
        Index('ix_parent_teacher_comm_date', 'communication_date'),
    )


class CallLog(Base):
    """
    Phone call tracking (for call redirection feature)
    """
    __tablename__ = "call_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caller_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    callee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    call_type = Column(String, nullable=False)  # "incoming", "outgoing", "missed"
    duration_seconds = Column(Integer)
    call_started_at = Column(DateTime, nullable=False)
    call_ended_at = Column(DateTime)
    notes = Column(Text)
    recording_path = Column(String)  # Path to call recording (if enabled)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_call_logs_caller_id', 'caller_id'),
        Index('ix_call_logs_callee_id', 'callee_id'),
        Index('ix_call_logs_student_id', 'student_id'),
        Index('ix_call_logs_started_at', 'call_started_at'),
    )