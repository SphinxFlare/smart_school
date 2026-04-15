# welfare/models/meetings.py


from sqlalchemy import (
    Column, String, UUID, ForeignKey, DateTime, Text, Boolean, Integer,
    Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from db.base import Base
import uuid


class Meeting(Base):
    """
    Welfare meeting (parent-teacher, counselor-student, etc.)
    """
    __tablename__ = "meetings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    title = Column(String, nullable=False)
    purpose = Column(Text, nullable=False)
    description = Column(Text)
    scheduled_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    location = Column(String)
    meeting_type = Column(String, nullable=False)  # "parent_teacher", "counselor_student", "staff_meeting", "disciplinary"
    status = Column(String, nullable=False)  # "scheduled", "confirmed", "completed", "cancelled", "rescheduled"
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    
    __table_args__ = (
        Index('ix_meetings_school_id', 'school_id'),
        Index('ix_meetings_scheduled_at', 'scheduled_at'),
        Index('ix_meetings_status', 'status'),
        Index('ix_meetings_created_by', 'created_by_id'),
    )

class MeetingParticipant(Base):
    """
    Meeting attendees with roles and attendance tracking
    """
    __tablename__ = "meeting_participants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("meetings.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)  # "parent", "student", "teacher", "counselor", "admin", "observer"
    invitation_status = Column(String, nullable=False)  # "pending", "accepted", "declined", "tentative"
    attendance_status = Column(String)  # "present", "absent", "late"
    attendance_confirmed_at = Column(DateTime)
    notes = Column(Text)  # Participant-specific notes
    invited_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('meeting_id', 'user_id', name='uq_meeting_participant'),
        Index('ix_meeting_participants_meeting_id', 'meeting_id'),
        Index('ix_meeting_participants_user_id', 'user_id'),
    )


class MeetingAgenda(Base):
    """
    Meeting agenda items
    """
    __tablename__ = "meeting_agendas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("meetings.id"), nullable=False)
    item_order = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    assigned_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    estimated_duration_minutes = Column(Integer)
    status = Column(String, nullable=False)  # "pending", "in_progress", "completed"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_meeting_agendas_meeting_id', 'meeting_id'),
        Index('ix_meeting_agendas_item_order', 'meeting_id', 'item_order'),
    )


class MeetingOutcome(Base):
    """
    Meeting outcomes, decisions, and action items
    """
    __tablename__ = "meeting_outcomes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("meetings.id"), nullable=False)
    outcome_text = Column(Text, nullable=False)
    action_items = Column(JSONB)  # [{"description": "...", "assigned_to": "...", "due_date": "...", "status": "..."}]
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime)
    recorded_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_meeting_outcomes_meeting_id', 'meeting_id'),
        Index('ix_meeting_outcomes_recorded_at', 'recorded_at'),
    )


class MeetingAttendance(Base):
    """
    Detailed attendance tracking for meetings
    """
    __tablename__ = "meeting_attendance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("meetings.id"), nullable=False)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("meeting_participants.id"), nullable=False)
    check_in_time = Column(DateTime)
    check_out_time = Column(DateTime)
    attendance_duration_minutes = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('meeting_id', 'participant_id', name='uq_meeting_attendance'),
        Index('ix_meeting_attendance_meeting_id', 'meeting_id'),
    )