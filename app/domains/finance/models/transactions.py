# finance/models/transactions.py


from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, Numeric, Text, Boolean, Index, Enum as SQLEnum, UniqueConstraint
from db.base import Base
from types.fees import PaymentStatus
from datetime import datetime
import uuid



class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)

    # Optional links
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=True)
    student_fee_id = Column(UUID(as_uuid=True), ForeignKey("student_fees.id"), nullable=True)

    admission_application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("admission_applications.id"),
        nullable=True
    )

    amount = Column(Numeric(12, 2), nullable=False)

    payment_method = Column(String, nullable=False)
    transaction_reference = Column(String)

    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.COMPLETED)

    payment_date = Column(DateTime, nullable=False)

    received_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    remarks = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    __table_args__ = (
        Index("ix_payments_student_id", "student_id"),
        Index("ix_payments_student_fee_id", "student_fee_id"),
        Index("ix_payments_admission_application_id", "admission_application_id"),
        Index("ix_payments_status", "status"),
        Index("ix_payments_school_id", "school_id"),
    )


class Receipt(Base):
    """
    Official receipt document
    """
    __tablename__ = "receipts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False)
    receipt_number = Column(String, nullable=False)  # Auto-generated: REC-2026-00001
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    student_fee_id = Column(UUID(as_uuid=True), ForeignKey("student_fees.id"), nullable=False)
    amount = Column(Numeric, nullable=False)
    date_issued = Column(DateTime, default=datetime.utcnow)
    issued_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    pdf_path = Column(String)  # Path to generated PDF receipt
    is_voided = Column(Boolean, default=False)
    voided_at = Column(DateTime)
    voided_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    void_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_receipts_receipt_number', 'receipt_number'),
        Index('ix_receipts_student_id', 'student_id'),
        Index("ix_receipts_school_id", "school_id"),
        Index("ix_receipts_payment_id", "payment_id"),
        UniqueConstraint("school_id", "receipt_number", name="uq_receipt_school_number")
    )


class Refund(Base):
    """
    Tracking money returned to parents (e.g., student withdrawal or overpayment)
    """
    __tablename__ = "refunds"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    
    amount = Column(Numeric, nullable=False)
    reason = Column(Text, nullable=False)
    refund_method = Column(String, nullable=False)  # "bank_transfer", "cash", "original_method"
    status = Column(String, nullable=False)         # "pending", "processed", "rejected"
    
    processed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    processed_at = Column(DateTime)
    
    transaction_reference = Column(String)  # Bank UTR number, etc.
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_refunds_student_id', 'student_id'),
        Index('ix_refunds_status', 'status'),
        Index("ix_refunds_school_id", "school_id"),
        Index("ix_refunds_payment_id", "payment_id"),
    )