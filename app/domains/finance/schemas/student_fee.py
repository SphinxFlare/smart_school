# finance/schemas/student_fee.py


from pydantic import BaseModel, Field, validator
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from .base import DomainBase, TimestampSchema

if TYPE_CHECKING:
    from app.domains.identity.schemas.student import StudentReference
    from .fee_structure import FeeCategoryReference
    from .payment import PaymentSummary
else:
    StudentReference = "StudentReference"
    FeeCategoryReference = "FeeCategoryReference"
    PaymentSummary = "PaymentSummary"

class StudentFeeBase(DomainBase):
    amount_due: Decimal = Field(..., decimal_places=2, gt=0)
    amount_paid: Decimal = Field(default=0.00, decimal_places=2, ge=0)
    due_date: datetime
    status: str = Field(
        ...,
        pattern=r"^(pending|partial|paid|waived|overdue)$",
        description="Current payment status"
    )
    waived_reason: Optional[str] = Field(None, max_length=500)

    @validator('amount_paid')
    def validate_payment_amount(cls, v, values):
        if v > values.get('amount_due', v):
            raise ValueError('Amount paid cannot exceed amount due')
        return v
    
    @validator('status')
    def validate_status_logic(cls, v, values):
        amount_due = values.get('amount_due', 0)
        amount_paid = values.get('amount_paid', 0)
        
        if v == "paid" and amount_paid < amount_due:
            raise ValueError('Status cannot be "paid" when amount paid is less than amount due')
        if v == "waived" and not values.get('waived_reason'):
            raise ValueError('Waived reason required when status is "waived"')
        return v

class StudentFeeCreate(StudentFeeBase):
    student_id: UUID
    fee_structure_id: UUID
    academic_year_id: UUID

class StudentFeeUpdate(BaseModel):
    amount_paid: Optional[Decimal] = None
    status: Optional[str] = None
    waived_reason: Optional[str] = None
    due_date: Optional[datetime] = None

class StudentFeeResponse(StudentFeeBase, TimestampSchema):
    id: UUID
    student_id: UUID
    fee_structure_id: UUID
    academic_year_id: UUID
    is_deleted: bool
    student: StudentReference
    fee_category: FeeCategoryReference
    remaining_amount: Decimal = Field(default=0.00, decimal_places=2)
    overdue_days: int = 0
    last_payment_date: Optional[datetime] = None
    payment_summary: Optional["PaymentSummary"] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "d4e5f6a7-b8c9-0123-def4-567890123456",
                "student_id": "student-uuid",
                "fee_structure_id": "fee-structure-uuid",
                "academic_year_id": "academic-year-uuid",
                "amount_due": 45000.00,
                "amount_paid": 38250.00,
                "due_date": "2026-04-30T23:59:59Z",
                "status": "partial",
                "waived_reason": None,
                "student": {
                    "id": "student-uuid",
                    "admission_number": "STU2026045",
                    "full_name": "Jamie Smith",
                    "class_name": "Grade 10",
                    "section_name": "A"
                },
                "fee_category": {
                    "id": "category-uuid",
                    "name": "Annual Tuition Fee",
                    "type": "yearly",
                    "custom_type": None
                },
                "remaining_amount": 6750.00,
                "overdue_days": 0,
                "last_payment_date": "2026-02-15T14:30:00Z",
                "payment_summary": {
                    "total_paid": 38250.00,
                    "payment_count": 3,
                    "last_payment_date": "2026-02-15T14:30:00Z"
                },
                "created_at": "2026-01-20T09:15:00Z",
                "is_deleted": False
            }
        }

class StudentFeeWithPayments(StudentFeeResponse):
    """Student fee with detailed payment history"""
    payments: List["PaymentResponse"] = []

class StudentFeeSummary(BaseModel):
    """Summary of student's fee status across all categories"""
    student_id: UUID
    student_name: str
    admission_number: str
    class_section: str
    total_fees_due: Decimal = Field(default=0.00, decimal_places=2)
    total_fees_paid: Decimal = Field(default=0.00, decimal_places=2)
    total_fees_overdue: Decimal = Field(default=0.00, decimal_places=2)
    pending_fee_categories: List[str] = []
    overall_status: str  # "clear", "partial", "overdue"

class BulkStudentFeeUpdate(BaseModel):
    """Request for bulk updating student fees"""
    student_fee_ids: List[UUID] = Field(..., min_items=1, max_items=100)
    status: Optional[str] = Field(None, pattern=r"^(pending|partial|paid|waived)$")
    amount_paid: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    notes: Optional[str] = Field(None, max_length=500)

    @validator('student_fee_ids')
    def validate_ids_unique(cls, v):
        if len(set(v)) != len(v):
            raise ValueError('Duplicate student fee IDs not allowed')
        return v

class FeeStatusReport(BaseModel):
    """Comprehensive fee status report for analytics"""
    academic_year: str
    class_name: Optional[str] = None
    section_name: Optional[str] = None
    total_students: int = 0
    total_fees_assessed: Decimal = Field(default=0.00, decimal_places=2)
    total_fees_collected: Decimal = Field(default=0.00, decimal_places=2)
    collection_percentage: float = Field(default=0.0, ge=0, le=100)
    overdue_count: int = 0
    overdue_amount: Decimal = Field(default=0.00, decimal_places=2)
    waived_count: int = 0
    waived_amount: Decimal = Field(default=0.00, decimal_places=2)

# Resolve forward references
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .payment import PaymentResponse
else:
    PaymentResponse = "PaymentResponse"

StudentFeeResponse.model_rebuild()
StudentFeeWithPayments.model_rebuild()