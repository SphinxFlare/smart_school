# finance/schemas/fee_structure.py


from pydantic import BaseModel, Field, validator
from typing import Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from .base import DomainBase, TimestampSchema

if TYPE_CHECKING:
    from .fee_category import FeeCategoryReference
    from app.domains.identity.schemas.class_section import ClassSectionReference
    from app.domains.identity.schemas.school import SchoolReference
else:
    FeeCategoryReference = "FeeCategoryReference"
    ClassSectionReference = "ClassSectionReference"
    SchoolReference = "SchoolReference"

class FeeStructureBase(DomainBase):
    amount: Decimal = Field(..., decimal_places=2, gt=0, description="Fee amount in currency")
    due_date: datetime = Field(..., description="Payment due date")
    late_fee_amount: Decimal = Field(default=0.00, decimal_places=2, ge=0, description="Fixed late fee amount")
    late_fee_after_days: int = Field(default=0, ge=0, le=30, description="Days after due date before late fee applies")
    late_fee_percentage: Optional[Decimal] = Field(
        None,
        decimal_places=2,
        ge=0,
        le=100,
        description="Percentage late fee (alternative to fixed amount)"
    )
    description: Optional[str] = Field(None, max_length=500)
    payment_instructions: Optional[str] = Field(None, max_length=1000)
    is_published: bool = Field(default=False, description="Published to parents/students")

    @validator('late_fee_percentage')
    def validate_late_fee_type(cls, v, values):
        if v and values.get('late_fee_amount') and values['late_fee_amount'] > 0:
            raise ValueError('Cannot specify both fixed late fee amount and percentage')
        return v
    
    @validator('due_date')
    def validate_due_date_future(cls, v):
        from datetime import datetime as dt
        if v < dt.utcnow():
            raise ValueError('Due date cannot be in the past')
        return v

class FeeStructureCreate(FeeStructureBase):
    school_id: UUID
    category_id: UUID
    class_id: UUID
    section_id: Optional[UUID] = None
    academic_year_id: UUID
    created_by_id: UUID

class FeeStructureUpdate(BaseModel):
    amount: Optional[Decimal] = None
    due_date: Optional[datetime] = None
    late_fee_amount: Optional[Decimal] = None
    late_fee_after_days: Optional[int] = None
    late_fee_percentage: Optional[Decimal] = None
    description: Optional[str] = None
    payment_instructions: Optional[str] = None
    is_published: Optional[bool] = None
    is_active: Optional[bool] = None

class FeeStructureBreakdown(BaseModel):
    """Detailed breakdown of fee structure"""
    base_amount: Decimal
    late_fee_amount: Decimal
    late_fee_percentage: Optional[Decimal] = None
    total_due: Decimal  # Calculated field

    @validator('total_due', always=True)
    def calculate_total_due(cls, v, values):
        base = values.get('base_amount', 0)
        late = values.get('late_fee_amount', 0)
        return base + late

class FeeStructureResponse(FeeStructureBase, TimestampSchema):
    id: UUID
    school_id: UUID
    category_id: UUID
    class_id: UUID
    section_id: Optional[UUID] = None
    academic_year_id: UUID
    created_by_id: UUID
    is_deleted: bool
    category: FeeCategoryReference
    class_section: ClassSectionReference
    school: SchoolReference
    total_students: int = 0
    total_collected: Decimal = Field(default=0.00, decimal_places=2)
    collection_percentage: float = Field(default=0.0, ge=0, le=100)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "school_id": "school-uuid",
                "category_id": "category-uuid",
                "category": {
                    "id": "category-uuid",
                    "name": "Annual Tuition Fee",
                    "type": "yearly",
                    "custom_type": None
                },
                "class_section": {
                    "class_id": "class-uuid",
                    "class_name": "Grade 10",
                    "section_id": "section-uuid",
                    "section_name": "A"
                },
                "school": {
                    "id": "school-uuid",
                    "name": "Delhi Public School - Rohini Campus",
                    "code": "DPS_ROHINI",
                    "city": "New Delhi"
                },
                "academic_year_id": "academic-year-uuid",
                "amount": 45000.00,
                "due_date": "2026-04-30T23:59:59Z",
                "late_fee_amount": 500.00,
                "late_fee_after_days": 7,
                "late_fee_percentage": None,
                "description": "Annual tuition fee for Grade 10 Section A",
                "payment_instructions": "Payment can be made via UPI, Bank Transfer, or at school office. UPI ID: fees@dpsrohini.edu.in",
                "is_published": True,
                "created_by_id": "user-uuid",
                "created_at": "2026-01-15T10:30:00Z",
                "is_deleted": False,
                "total_students": 40,
                "total_collected": 38250.00,
                "collection_percentage": 85.0
            }
        }

class FeeStructureSummary(BaseModel):
    """Compact summary for listing views"""
    id: UUID
    category_name: str
    class_name: str
    section_name: Optional[str] = None
    amount: Decimal
    due_date: datetime
    is_published: bool
    collection_percentage: float

class BulkFeeStructureCreate(BaseModel):
    """
    Schema for creating fee structures for multiple classes/sections at once
    """
    school_id: UUID
    category_id: UUID
    academic_year_id: UUID
    created_by_id: UUID
    structures: list[FeeStructureBase] = Field(..., min_items=1, max_items=50)
    apply_to_all_classes: bool = Field(default=False)
    class_ids: Optional[list[UUID]] = Field(None, min_items=1)
    section_ids: Optional[list[UUID]] = None  # If None, applies to all sections in class

    @validator('structures')
    def validate_structures(cls, v):
        if len(v) > 50:
            raise ValueError('Maximum 50 structures allowed in bulk operation')
        return v

# Resolve forward references
FeeStructureResponse.model_rebuild()