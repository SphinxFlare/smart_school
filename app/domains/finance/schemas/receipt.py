# finance/schemas/receipt.py


from pydantic import BaseModel, Field, validator
from typing import Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from .base import DomainBase, TimestampSchema

if TYPE_CHECKING:
    from app.domains.identity.schemas.student import StudentReference
    from app.domains.identity.schemas.user import UserReference
    from .fee_structure import FeeCategoryReference
else:
    StudentReference = "StudentReference"
    UserReference = "UserReference"
    FeeCategoryReference = "FeeCategoryReference"

class ReceiptNumberGenerator(BaseModel):
    """
    Helper schema for receipt number generation
    Format: {school_code}-{year}-{sequence}
    Example: DPS_ROHINI-2026-00001
    """
    school_code: str = Field(..., pattern=r"^[A-Z0-9_]{3,20}$")
    year: int = Field(..., ge=2000, le=2100)
    sequence: int = Field(..., ge=1, le=999999)

    def generate(self) -> str:
        return f"{self.school_code}-{self.year}-{self.sequence:06d}"

class ReceiptBase(DomainBase):
    receipt_number: str = Field(
        ...,
        pattern=r"^[A-Z0-9_]{3,20}-\d{4}-\d{6}$",
        description="Format: SCHOOLCODE-YEAR-SEQUENCE"
    )
    amount: Decimal = Field(..., decimal_places=2, gt=0)
    date_issued: datetime = Field(default_factory=datetime.utcnow)
    pdf_path: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=500)

class ReceiptCreate(ReceiptBase):
    payment_id: UUID
    student_id: UUID
    student_fee_id: UUID
    issued_by_id: UUID

class ReceiptUpdate(BaseModel):
    notes: Optional[str] = None
    pdf_path: Optional[str] = None

class VoidReceiptRequest(BaseModel):
    """Request to void a receipt"""
    void_reason: str = Field(..., min_length=10, max_length=500)
    voided_by_id: UUID

class ReceiptResponse(ReceiptBase, TimestampSchema):
    id: UUID
    payment_id: UUID
    student_id: UUID
    student_fee_id: UUID
    issued_by_id: UUID
    is_voided: bool = False
    voided_at: Optional[datetime] = None
    voided_by_id: Optional[UUID] = None
    void_reason: Optional[str] = None
    student: StudentReference
    issued_by: UserReference
    fee_category: FeeCategoryReference
    payment_method: str
    transaction_reference: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                "payment_id": "payment-uuid",
                "student_id": "student-uuid",
                "student_fee_id": "student-fee-uuid",
                "receipt_number": "DPS_ROHINI-2026-00045",
                "amount": 12500.00,
                "date_issued": "2026-02-15T14:30:00Z",
                "issued_by_id": "user-uuid",
                "pdf_path": "/receipts/2026/DPS_ROHINI-2026-00045.pdf",
                "notes": "Payment received via UPI transfer",
                "is_voided": False,
                "student": {
                    "id": "student-uuid",
                    "admission_number": "STU2026045",
                    "full_name": "Jamie Smith",
                    "class_name": "Grade 10",
                    "section_name": "A"
                },
                "issued_by": {
                    "id": "user-uuid",
                    "full_name": "Mrs. Sunita Verma",
                    "email": "accounts@dpsrohini.edu.in",
                    "role": "admin"
                },
                "fee_category": {
                    "id": "category-uuid",
                    "name": "Quarterly Tuition Fee",
                    "type": "other",
                    "custom_type": {
                        "type": "quarterly_tuition",
                        "label": "Quarterly Tuition Fee",
                        "description": "Q3 tuition fee"
                    }
                },
                "payment_method": "upi",
                "transaction_reference": "UPI260215143000XYZ",
                "created_at": "2026-02-15T14:30:00Z"
            }
        }

class ReceiptWithPaymentDetails(ReceiptResponse):
    """Extended receipt with full payment breakdown"""
    payment_date: datetime
    payment_received_by: UserReference
    previous_balance: Decimal = Field(default=0.00, decimal_places=2)
    remaining_balance: Decimal = Field(default=0.00, decimal_places=2)
    is_fully_paid: bool = False

class ReceiptListFilter(BaseModel):
    """Filter schema for receipt listing endpoints"""
    student_id: Optional[UUID] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_amount: Optional[Decimal] = Field(None, ge=0)
    is_voided: Optional[bool] = None
    receipt_number: Optional[str] = Field(None, max_length=50)
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

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

class ReceiptStatistics(BaseModel):
    """Aggregated receipt statistics"""
    total_receipts: int = 0
    total_amount: Decimal = Field(default=0.00, decimal_places=2)
    voided_receipts: int = 0
    voided_amount: Decimal = Field(default=0.00, decimal_places=2)
    average_receipt_amount: Decimal = Field(default=0.00, decimal_places=2)
    receipts_by_month: dict[str, int] = Field(default_factory=dict)
    receipts_by_category: dict[str, int] = Field(default_factory=dict)

class ReceiptDownloadResponse(BaseModel):
    """Response for receipt download endpoint"""
    receipt_id: UUID
    receipt_number: str
    download_url: str
    expires_at: datetime
    file_size_bytes: int
    content_type: str = "application/pdf"

# Resolve forward references
ReceiptResponse.model_rebuild()
ReceiptWithPaymentDetails.model_rebuild()