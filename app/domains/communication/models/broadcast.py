# communication/models/broadcast.py

from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, Text, Boolean, Integer, Index
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from db.base import Base
import uuid


class Announcement(Base):
    """
    School-wide announcements, notices, holidays, events
    """
    __tablename__ = "announcements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    announcement_type = Column(String, nullable=False)  # "notice", "holiday", "event", "activity", "urgent"
    category = Column(String)  # "academic", "administrative", "sports", "cultural", "general"
    target_roles = Column(JSONB)  # ["student", "parent", "teacher", "staff"] - who can see this
    target_classes = Column(JSONB)  # [class_id1, class_id2] - specific classes
    target_sections = Column(JSONB)  # [section_id1, section_id2] - specific sections
    published_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    published_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime)  # When announcement should no longer be visible
    is_pinned = Column(Boolean, default=False)  # Show at top
    priority = Column(String, default="normal")  # "low", "normal", "high", "urgent"
    attachments = Column(JSONB)  # [{"name": "file.pdf", "path": "...", "type": "document"}]
    views_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    
    __table_args__ = (
        Index('ix_announcements_school_id', 'school_id'),
        Index('ix_announcements_published_at', 'published_at'),
        Index('ix_announcements_expires_at', 'expires_at'),
        Index('ix_announcements_type', 'announcement_type'),
        Index('ix_announcements_priority', 'priority'),
    )


class DailyFeed(Base):
    """
    Aggregated daily feed items for dashboard
    Auto-generated from announcements, exams, concerns, etc.
    """
    __tablename__ = "daily_feeds"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    feed_date = Column(DateTime, nullable=False)
    item_type = Column(String, nullable=False)  # "announcement", "exam", "holiday", "event", "concern_update", "birthday"
    source_type = Column(String, nullable=False)  # "announcement", "exam", "concern", "student", "meeting"
    source_id = Column(UUID(as_uuid=True), nullable=False)  # ID of source entity
    title = Column(String, nullable=False)
    summary = Column(Text)
    priority = Column(String, default="normal")  # "low", "normal", "high"
    is_read = Column(Boolean, default=False)
    read_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_daily_feeds_school_date', 'school_id', 'feed_date'),
        Index('ix_daily_feeds_item_type', 'item_type'),
        Index('ix_daily_feeds_priority', 'priority'),
        Index('ix_daily_feeds_created_at', 'created_at'),
    )


class Bulletin(Base):
    """
    School bulletin board for important information
    """
    __tablename__ = "bulletins"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String, nullable=False)  # "academic", "administrative", "sports", "cultural", "important"
    display_order = Column(Integer, default=0)
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime)
    expires_at = Column(DateTime)
    published_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    views_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    
    __table_args__ = (
        Index('ix_bulletins_school_id', 'school_id'),
        Index('ix_bulletins_category', 'category'),
        Index('ix_bulletins_published', 'is_published', 'published_at'),
    )