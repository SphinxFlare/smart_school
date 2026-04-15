# finance/schemas/fee_waiver.py


from pydantic import BaseModel, Field, validator
from typing import Optional, TYPE_CHECKING
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

class FeeWaiverBase(DomainBase):
    amount_waived: Decimal = Field(..., decimal_places=2, gt=0)
    reason: str = Field(..., min_length=10, max_length=1000)
    supporting_documents: Optional[list[str]] = Field(None, max_items=10)
    waiver_type: str = Field(
        default="full",
        pattern=r"^(full|partial|scholarship|financial_aid|other)$",
        description="Type of waiver"
    )
    status: str = Field(
        default="pending",
        pattern=r"^(pending|approved|rejected)$",
        description="Approval status"
    )
    rejection_reason: Optional[str] = Field(None, max_length=500)

    @validator('supporting_documents')
    def validate_document_paths(cls, v):
        if v:
            for path in v:
                if not path.startswith('/') and not path.startswith('http'):
                    raise ValueError('Document paths must be absolute or URLs')
        return v

class FeeWaiverCreate(FeeWaiverBase):
    student_fee_id: UUID
    student_id: UUID
    created_by_id: UUID

class FeeWaiverUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern=r"^(approved|rejected)$")
    rejection_reason: Optional[str] = None
    approved_by_id: Optional[UUID] = None

class FeeWaiverApprovalRequest(FeeWaiverBase):
    """Request schema for creating waiver with auto-approval workflow"""
    student_fee_id: UUID
    student_id: UUID
    auto_approve: bool = Field(default=False, description="Skip approval workflow if True")
    approval_notes: Optional[str] = Field(None, max_length=500)

class FeeWaiverResponse(FeeWaiverBase, TimestampSchema):
    id: UUID
    student_fee_id: UUID
    student_id: UUID
    approved_by_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    created_by_id: UUID
    is_deleted: bool
    student: StudentReference
    approved_by: Optional[UserReference] = None
    created_by: UserReference
    original_fee_amount: Decimal = Field(default=0.00, decimal_places=2)
    waiver_percentage: float = Field(default=0.0, ge=0, le=100)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "e5f6a7b8-c9d0-1234-ef56-789012345678",
                "student_fee_id": "student-fee-uuid",
                "student_id": "student-uuid",
                "amount_waived": 15000.00,
                "reason": "Student qualifies for economic hardship scholarship program. Family income below threshold as per government guidelines.",
                "supporting_documents": [
                    "/documents/waivers/income_certificate_2026.pdf",
                    "/documents/waivers/scholarship_approval_letter.pdf"
                ],
                "waiver_type": "scholarship",
                "status": "approved",
                "rejection_reason": None,
                "approved_by_id": "user-uuid",
                "approved_at": "2026-02-10T11:30:00Z",
                "created_by_id": "user-uuid",
                "created_at": "2026-02-05T09:15:00Z",
                "is_deleted": False,
                "student": {
                    "id": "student-uuid",
                    "admission_number": "STU2026078",
                    "full_name": "Rahul Kumar",
                    "class_name": "Grade 8",
                    "section_name": "B"
                },
                "approved_by": {
                    "id": "user-uuid",
                    "full_name": "Dr. Sunita Menon",
                    "email": "principal@dpsrohini.edu.in",
                    "role": "admin"
                },
                "created_by": {
                    "id": "user-uuid",
                    "full_name": "Mrs. Priya Sharma",
                    "email": "accounts@dpsrohini.edu.in",
                    "role": "admin"
                },
                "original_fee_amount": 45000.00,
                "waiver_percentage": 33.33
            }
        }

class FeeWaiverSummary(BaseModel):
    """Summary statistics for fee waivers"""
    total_waivers: int = 0
    approved_waivers: int = 0
    rejected_waivers: int = 0
    pending_waivers: int = 0
    total_amount_waived: Decimal = Field(default=0.00, decimal_places=2)
    average_waiver_amount: Decimal = Field(default=0.00, decimal_places=2)
    waivers_by_type: dict[str, int] = Field(default_factory=dict)
    waivers_by_status: dict[str, int] = Field(default_factory=dict)

class WaiverApprovalWorkflow(BaseModel):
    """Workflow tracking for waiver approvals"""
    waiver_id: UUID
    current_status: str
    approval_history: list[dict] = Field(default_factory=list)
    pending_approvals: list[UserReference] = Field(default_factory=list)
    can_approve: bool = False
    can_reject: bool = False

# Resolve forward references
FeeWaiverResponse.model_rebuild()
WaiverApprovalWorkflow.model_rebuild()