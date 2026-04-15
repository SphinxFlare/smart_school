# communication/models/notifications.py


from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, Text, Boolean, Index
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from db.base import Base
import uuid



class Notification(Base):
    """
    System-generated notifications for users
    """
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String, nullable=False)  # "transport", "attendance", "exam", "fee", "concern", "message", "system"
    entity_type = Column(String)  # "transport_trip", "attendance", "exam", "fee", "concern", "message"
    entity_id = Column(UUID(as_uuid=True))  # ID of related entity
    action_url = Column(String)  # Deep link to relevant screen
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    sent_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    priority = Column(String, default="normal")  # "low", "normal", "high"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_notifications_user_id', 'user_id'),
        Index('ix_notifications_is_read', 'is_read'),
        Index('ix_notifications_sent_at', 'sent_at'),
        Index('ix_notifications_type', 'notification_type'),
    )


class NotificationPreference(Base):
    """
    User notification preferences per channel and type
    """
    __tablename__ = "notification_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)
    
    # Per-type preferences
    transport_notifications = Column(Boolean, default=True)
    attendance_notifications = Column(Boolean, default=True)
    exam_notifications = Column(Boolean, default=True)
    fee_notifications = Column(Boolean, default=True)
    concern_notifications = Column(Boolean, default=True)
    message_notifications = Column(Boolean, default=True)
    system_notifications = Column(Boolean, default=True)
    
    # Quiet hours
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String)  # "22:00"
    quiet_hours_end = Column(String)  # "07:00"
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_notification_preferences_user_id', 'user_id'),
    )


class CommunicationLog(Base):
    """
    Audit log of all communications (messages, notifications, announcements)
    """
    __tablename__ = "communication_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    communication_type = Column(String, nullable=False)  # "message", "notification", "announcement", "email", "sms"
    entity_type = Column(String)  # "message", "notification", "announcement"
    entity_id = Column(UUID(as_uuid=True))
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    recipient_ids = Column(JSONB)  # Array of recipient user IDs
    channel = Column(String)  # "email", "sms", "push", "in_app"
    status = Column(String, nullable=False)  # "queued", "sent", "delivered", "failed"
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    error_message = Column(Text)
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_communication_logs_school_id', 'school_id'),
        Index('ix_communication_logs_type', 'communication_type'),
        Index('ix_communication_logs_status', 'status'),
        Index('ix_communication_logs_created_at', 'created_at'),
    )
