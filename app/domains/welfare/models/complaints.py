# welfare/models/complaints.py


from sqlalchemy import (
    Column, String, UUID, ForeignKey, DateTime, Text, Boolean,
    Enum as SQLEnum, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from db.base import Base
import uuid
from types.types import ConcernType



class Concern(Base):
    """
    Student concern/flag raised by teachers, parents, or students
    """
    __tablename__ = "concerns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    type = Column(SQLEnum(ConcernType), nullable=False)
    custom_type = Column(JSONB)  # {"type": "bullying", "label": "Bullying Incident"}
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String, nullable=False)  # "low", "medium", "high", "critical"
    status = Column(String, nullable=False)  # "reported", "under_review", "assigned", "resolved", "closed"
    reported_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reported_at = Column(DateTime, default=datetime.utcnow)
    reviewed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    is_anonymous = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    
    __table_args__ = (
        Index('ix_concerns_student_id', 'student_id'),
        Index('ix_concerns_status', 'status'),
        Index('ix_concerns_reported_at', 'reported_at'),
        Index('ix_concerns_type', 'type'),
    )


class ConcernAssignment(Base):
    """
    Assignment of concern to responsible staff member (counselor/teacher)
    """
    __tablename__ = "concern_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concern_id = Column(UUID(as_uuid=True), ForeignKey("concerns.id"), nullable=False)
    assigned_to_id = Column(UUID(as_uuid=True), ForeignKey("staff_members.id"), nullable=False)
    assigned_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime)
    priority = Column(String, nullable=False)  # "low", "medium", "high", "urgent"
    status = Column(String, nullable=False)  # "pending", "in_progress", "completed"
    completed_at = Column(DateTime)
    completion_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_concern_assignments_concern_id', 'concern_id'),
        Index('ix_concern_assignments_assigned_to', 'assigned_to_id'),
        Index('ix_concern_assignments_status', 'status'),
    )


class ConcernComment(Base):
    """
    Threaded comments on concerns for collaboration
    """
    __tablename__ = "concern_comments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concern_id = Column(UUID(as_uuid=True), ForeignKey("concerns.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    comment = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)  # True = only visible to staff, False = visible to parents
    parent_visibility = Column(String)  # "visible", "hidden", "partial"
    attachments = Column(JSONB)  # [{"name": "photo.jpg", "path": "..."}]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    
    __table_args__ = (
        Index('ix_concern_comments_concern_id', 'concern_id'),
        Index('ix_concern_comments_created_at', 'created_at'),
    )


class ConcernHistory(Base):
    """
    Audit trail of concern status changes and actions
    """
    __tablename__ = "concern_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concern_id = Column(UUID(as_uuid=True), ForeignKey("concerns.id"), nullable=False)
    action = Column(String, nullable=False)  # "status_changed", "assigned", "escalated", "resolved"
    previous_value = Column(JSONB)
    new_value = Column(JSONB)
    changed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    
    __table_args__ = (
        Index('ix_concern_history_concern_id', 'concern_id'),
        Index('ix_concern_history_changed_at', 'changed_at'),
    )


class Escalation(Base):
    """
    Concern escalation workflow
    """
    __tablename__ = "escalations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concern_id = Column(UUID(as_uuid=True), ForeignKey("concerns.id"), nullable=False)
    escalated_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    escalated_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    escalated_at = Column(DateTime, default=datetime.utcnow)
    reason = Column(Text, nullable=False)
    priority = Column(String, nullable=False)  # "low", "medium", "high", "urgent"
    due_date = Column(DateTime)
    status = Column(String, nullable=False)  # "pending", "acknowledged", "resolved"
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_escalations_concern_id', 'concern_id'),
        Index('ix_escalations_escalated_at', 'escalated_at'),
        Index('ix_escalations_status', 'status'),
    )