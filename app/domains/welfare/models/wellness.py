# welfare/models/wellness.py


from sqlalchemy import (
    Column, String, UUID, ForeignKey, DateTime, Text, Boolean, Integer,
    Index
)
from datetime import datetime
from db.base import Base
import uuid



class StudentObservation(Base):
    """
    Teacher micro-observations about student behavior/performance
    """
    __tablename__ = "student_observations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("staff_members.id"), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    observation_date = Column(DateTime, nullable=False)
    category = Column(String, nullable=False)  # "academic", "behaviour", "social", "health"
    description = Column(Text, nullable=False)
    severity = Column(String)  # "positive", "neutral", "concerning"
    action_taken = Column(Text)
    shared_with_parents = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    
    __table_args__ = (
        Index('ix_student_observations_student_id', 'student_id'),
        Index('ix_student_observations_teacher_id', 'teacher_id'),
        Index('ix_student_observations_date', 'observation_date'),
        Index('ix_student_observations_category', 'category'),
    )


class WellnessCheck(Base):
    """
    Periodic student wellness checks by counselor
    """
    __tablename__ = "wellness_checks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    counselor_id = Column(UUID(as_uuid=True), ForeignKey("staff_members.id"), nullable=False)
    check_date = Column(DateTime, nullable=False)
    academic_wellness = Column(Integer)  # 1-5 scale
    emotional_wellness = Column(Integer)  # 1-5 scale
    social_wellness = Column(Integer)  # 1-5 scale
    physical_wellness = Column(Integer)  # 1-5 scale
    notes = Column(Text)
    recommendations = Column(Text)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    
    __table_args__ = (
        Index('ix_wellness_checks_student_id', 'student_id'),
        Index('ix_wellness_checks_check_date', 'check_date'),
    )