# finance/schemas/payment.py


from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, TYPE_CHECKING, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from .base import DomainBase, TimestampSchema

if TYPE_CHECKING:
    from app.domains.identity.schemas.student import StudentReference
    from app.domains.identity.schemas.user import UserReference
else:
    StudentReference = "StudentReference"
    UserReference = "UserReference"

class PaymentMethodDetails(BaseModel):
    """
    Payment method specific details
    """
    method: str = Field(
        ...,
        pattern=r"^(cash|card|bank_transfer|upi|cheque|online_wallet|net_banking)$",
        description="Payment method type"
    )
    transaction_id: Optional[str] = Field(None, max_length=100)
    bank_name: Optional[str] = Field(None, max_length=100)
    account_number_last4: Optional[str] = Field(None, max_length=4)
    card_type: Optional[str] = Field(None, max_length=50)
    card_last4: Optional[str] = Field(None, max_length=4)
    upi_id: Optional[str] = Field(None, max_length=100)
    cheque_number: Optional[str] = Field(None, max_length=20)
    wallet_name: Optional[str] = Field(None, max_length=50)
    reference_number: Optional[str] = Field(None, max_length=100)

class PaymentBase(DomainBase):
    """
    Base schema for payment transactions
    """
    amount: Decimal = Field(..., decimal_places=2, gt=0, description="Payment amount")
    payment_method: str = Field(
        ...,
        pattern=r"^(cash|card|bank_transfer|upi|cheque|online_wallet|net_banking)$",
        description="Payment method"
    )
    payment_method_details: Optional[PaymentMethodDetails] = None
    transaction_reference: Optional[str] = Field(
        None,
        max_length=100,
        description="Bank/UPI/Transaction reference number"
    )
    payment_date: datetime = Field(..., description="Date and time of payment")
    remarks: Optional[str] = Field(None, max_length=500, description="Additional notes")
    receipt_number: Optional[str] = Field(
        None,
        pattern=r"^[A-Z0-9_]{3,20}-\d{4}-\d{6}$",
        description="Associated receipt number if issued"
    )
    is_partial_payment: bool = Field(default=False, description="Whether this is a partial payment")

    @validator('payment_date')
    def validate_payment_date(cls, v):
        if v > datetime.utcnow():
            raise ValueError('Payment date cannot be in the future')
        return v

class PaymentCreate(PaymentBase):
    """
    Schema for creating a payment
    """
    student_fee_id: UUID
    student_id: UUID
    received_by_id: UUID  # Staff member receiving payment

class PaymentUpdate(BaseModel):
    """
    Schema for updating payment details
    """
    remarks: Optional[str] = None
    transaction_reference: Optional[str] = None
    payment_method_details: Optional[PaymentMethodDetails] = None
    receipt_number: Optional[str] = None

class PaymentRefundRequest(BaseModel):
    """
    Request schema for refunding a payment
    """
    payment_id: UUID
    refund_amount: Decimal = Field(..., decimal_places=2, gt=0)
    refund_reason: str = Field(..., min_length=10, max_length=500)
    refund_method: str = Field(
        ...,
        pattern=r"^(cash|bank_transfer|original_method)$",
        description="How refund should be processed"
    )
    processed_by_id: UUID
    notes: Optional[str] = Field(None, max_length=500)

    @validator('refund_amount')
    def validate_refund_amount(cls, v, values):
        # Validation against original payment amount will be done at service layer
        return v

class PaymentResponse(PaymentBase, TimestampSchema):
    """
    Response schema for payment with relationships
    """
    id: UUID
    student_fee_id: UUID
    student_id: UUID
    received_by_id: UUID
    receipt_issued: bool = False
    is_deleted: bool
    student: StudentReference
    received_by: UserReference
    receipt: Optional["ReceiptReference"] = None
    refund_details: Optional[Dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "student_fee_id": "student-fee-uuid",
                "student_id": "student-uuid",
                "amount": 12500.00,
                "payment_method": "upi",
                "payment_method_details": {
                    "method": "upi",
                    "upi_id": "parent@paytm",
                    "transaction_id": "UPI260215143000XYZ"
                },
                "transaction_reference": "UPI260215143000XYZ",
                "payment_date": "2026-02-15T14:30:00Z",
                "remarks": "Payment received via UPI transfer",
                "receipt_number": "DPS_ROHINI-2026-00045",
                "is_partial_payment": False,
                "received_by_id": "user-uuid",
                "receipt_issued": True,
                "created_at": "2026-02-15T14:30:00Z",
                "is_deleted": False,
                "student": {
                    "id": "student-uuid",
                    "admission_number": "STU2026045",
                    "full_name": "Jamie Smith",
                    "class_name": "Grade 10",
                    "section_name": "A"
                },
                "received_by": {
                    "id": "user-uuid",
                    "full_name": "Mrs. Sunita Verma",
                    "email": "accounts@dpsrohini.edu.in",
                    "role": "admin"
                },
                "receipt": {
                    "id": "receipt-uuid",
                    "receipt_number": "DPS_ROHINI-2026-00045",
                    "pdf_path": "/receipts/2026/DPS_ROHINI-2026-00045.pdf"
                },
                "refund_details": None
            }
        }

class PaymentSummary(BaseModel):
    """
    Summary of payment statistics
    """
    total_paid: Decimal = Field(default=0.00, decimal_places=2)
    payment_count: int = 0
    last_payment_date: Optional[datetime] = None
    average_payment_amount: Decimal = Field(default=0.00, decimal_places=2)
    payment_methods_breakdown: Dict[str, int] = Field(default_factory=dict)
    recent_payments: Optional[List["PaymentResponse"]] = Field(None, max_items=5)

class PaymentHistoryResponse(BaseModel):
    """
    Complete payment history for a student
    """
    student_id: UUID
    student_name: str
    admission_number: str
    class_section: str
    total_fees_due: Decimal = Field(default=0.00, decimal_places=2)
    total_paid: Decimal = Field(default=0.00, decimal_places=2)
    outstanding_balance: Decimal = Field(default=0.00, decimal_places=2)
    payments: List[PaymentResponse]
    payment_summary: PaymentSummary

class BulkPaymentCreate(BaseModel):
    """
    Schema for bulk creating payments for multiple student fees
    """
    payments: List[PaymentCreate] = Field(..., min_items=1, max_items=100)
    auto_generate_receipts: bool = Field(default=True)

    @validator('payments')
    def validate_payments_unique(cls, v):
        student_fee_ids = [p.student_fee_id for p in v]
        if len(student_fee_ids) != len(set(student_fee_ids)):
            raise ValueError('Duplicate student_fee_id not allowed in bulk operation')
        return v

class PaymentFilter(BaseModel):
    """
    Filter schema for payment queries
    """
    student_id: Optional[UUID] = None
    student_fee_id: Optional[UUID] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_amount: Optional[Decimal] = Field(None, ge=0)
    payment_method: Optional[str] = None
    received_by_id: Optional[UUID] = None
    has_receipt: Optional[bool] = None
    is_partial_payment: Optional[bool] = None
    include_deleted: bool = False
    page: int = Field(default=1, ge=1)
    size: int = Field(default=50, ge=1, le=100)

    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v and values.get('date_from') and v < values['date_from']:
            raise ValueError('date_to must be after date_from')
        return v
    
    @validator('max_amount')
    def validate_amount_range(cls, v, values):
        if v and values.get('min_amount') and v < values['min_amount']:
            raise ValueError('max_amount must be greater than min_amount')
        return v

class PaymentStatistics(BaseModel):
    """
    Comprehensive payment statistics for analytics
    """
    total_payments: int = 0
    total_amount: Decimal = Field(default=0.00, decimal_places=2)
    average_payment_amount: Decimal = Field(default=0.00, decimal_places=2)
    payments_by_method: Dict[str, int] = Field(default_factory=dict)
    payments_by_month: Dict[str, Dict[str, Decimal]] = Field(
        default_factory=dict,
        description="Key: YYYY-MM, Value: {count: int, amount: Decimal}"
    )
    partial_payments_count: int = 0
    partial_payments_amount: Decimal = Field(default=0.00, decimal_places=2)
    receipts_issued_count: int = 0
    refunds_count: int = 0
    refunds_amount: Decimal = Field(default=0.00, decimal_places=2)

class PaymentReceiptLink(BaseModel):
    """
    Link payment to existing receipt
    """
    payment_id: UUID
    receipt_id: UUID
    linked_by_id: UUID
    notes: Optional[str] = Field(None, max_length=200)

class RefundResponse(BaseModel):
    """
    Response schema for refund operations
    """
    refund_id: UUID
    original_payment_id: UUID
    refund_amount: Decimal
    refund_method: str
    refund_date: datetime
    refund_reason: str
    processed_by_id: UUID
    processed_by: UserReference
    status: str = Field(default="completed", pattern=r"^(pending|completed|failed)$")
    transaction_reference: Optional[str] = None
    notes: Optional[str] = None

# Forward reference for ReceiptReference
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .receipt import ReceiptReference
else:
    ReceiptReference = "ReceiptReference"

# Resolve forward references
PaymentResponse.model_rebuild()
PaymentSummary.model_rebuild()
PaymentHistoryResponse.model_rebuild()
RefundResponse.model_rebuild()