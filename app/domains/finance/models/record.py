# finance/models/record.py


from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, Numeric, Text, Boolean, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from db.base import Base
from datetime import datetime
import uuid


class StudentFee(Base):
    """
    Individual student fee record (instance of fee structure)
    """
    __tablename__ = "student_fees"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    fee_structure_id = Column(UUID(as_uuid=True), ForeignKey("fee_structures.id"), nullable=False)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False)
    amount_due = Column(Numeric, nullable=False)
    amount_paid = Column(Numeric, default=0.0)
    status = Column(String, nullable=False)  # "pending", "partial", "paid", "waived"
    due_date = Column(DateTime, nullable=False)
    waived_reason = Column(Text)  # If status = "waived"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    
    __table_args__ = (
        UniqueConstraint('school_id', 'student_id', 'fee_structure_id', name='uq_student_fee_structure'),
        Index('ix_student_fees_student_id', 'student_id'),
        Index('ix_student_fees_status', 'status'),
    )


class FeeWaiver(Base):
    """
    Record of fee waivers with approval workflow
    """
    __tablename__ = "fee_waivers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    student_fee_id = Column(UUID(as_uuid=True), ForeignKey("student_fees.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    amount_waived = Column(Numeric, nullable=False)
    reason = Column(Text, nullable=False)
    approved_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, nullable=False)  # "pending", "approved", "rejected"
    rejection_reason = Column(Text)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    
    __table_args__ = (
        Index('ix_fee_waivers_student_id', 'student_id'),
        Index('ix_fee_waivers_status', 'status'),
    )


class FeeReminder(Base):
    """
    Automated fee reminder tracking
    """
    __tablename__ = "fee_reminders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    student_fee_id = Column(UUID(as_uuid=True), ForeignKey("student_fees.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    reminder_date = Column(DateTime, nullable=False)
    reminder_type = Column(String, nullable=False)  # "email", "sms", "notification"
    sent_to_parent_ids = Column(JSONB)  # Array of parent IDs notified
    sent_at = Column(DateTime)
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_fee_reminders_student_fee_id', 'student_fee_id'),
        Index('ix_fee_reminders_reminder_date', 'reminder_date'),
    )