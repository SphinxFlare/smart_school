# finance/schemas/__init__.py

# Finance domain public schema interface
from .base import DomainBase, TimestampSchema
from .payment import (
    PaymentMethodDetails, PaymentBase, PaymentCreate, PaymentUpdate,
    PaymentRefundRequest, PaymentResponse, PaymentSummary,
    PaymentHistoryResponse, BulkPaymentCreate, PaymentFilter,
    PaymentStatistics, PaymentReceiptLink, RefundResponse
)
from .fee_category import (
    CustomFeeType, FeeCategoryBase, FeeCategoryCreate, FeeCategoryUpdate,
    FeeCategoryResponse, FeeCategoryReference, CustomFeeCategoryExample
)
from .fee_structure import (
    FeeStructureBase, FeeStructureCreate, FeeStructureUpdate,
    FeeStructureResponse, FeeStructureSummary, FeeStructureBreakdown,
    BulkFeeStructureCreate
)
from .student_fee import (
    StudentFeeBase, StudentFeeCreate, StudentFeeUpdate,
    StudentFeeResponse, StudentFeeWithPayments, StudentFeeSummary,
    BulkStudentFeeUpdate, FeeStatusReport
)
from .receipt import (
    ReceiptNumberGenerator, ReceiptBase, ReceiptCreate, ReceiptUpdate,
    VoidReceiptRequest, ReceiptResponse, ReceiptWithPaymentDetails,
    ReceiptListFilter, ReceiptStatistics, ReceiptDownloadResponse
)
from .fee_waiver import (
    FeeWaiverBase, FeeWaiverCreate, FeeWaiverUpdate, FeeWaiverApprovalRequest,
    FeeWaiverResponse, FeeWaiverSummary, WaiverApprovalWorkflow
)
from .fee_reminder import (
    ReminderChannel, FeeReminderBase, FeeReminderCreate, FeeReminderUpdate,
    FeeReminderResponse, BulkFeeReminderCreate, ReminderStatistics, ReminderLog
)

__all__ = [
    # Base schemas
    "DomainBase", "TimestampSchema",
    
    # Payment
    "PaymentMethodDetails", "PaymentBase", "PaymentCreate", "PaymentUpdate",
    "PaymentRefundRequest", "PaymentResponse", "PaymentSummary",
    "PaymentHistoryResponse", "BulkPaymentCreate", "PaymentFilter",
    "PaymentStatistics", "PaymentReceiptLink", "RefundResponse",
    
    # Fee Category
    "CustomFeeType", "FeeCategoryBase", "FeeCategoryCreate", "FeeCategoryUpdate",
    "FeeCategoryResponse", "FeeCategoryReference", "CustomFeeCategoryExample",
    
    # Fee Structure
    "FeeStructureBase", "FeeStructureCreate", "FeeStructureUpdate",
    "FeeStructureResponse", "FeeStructureSummary", "FeeStructureBreakdown",
    "BulkFeeStructureCreate",
    
    # Student Fee
    "StudentFeeBase", "StudentFeeCreate", "StudentFeeUpdate",
    "StudentFeeResponse", "StudentFeeWithPayments", "StudentFeeSummary",
    "BulkStudentFeeUpdate", "FeeStatusReport",
    
    # Receipt
    "ReceiptNumberGenerator", "ReceiptBase", "ReceiptCreate", "ReceiptUpdate",
    "VoidReceiptRequest", "ReceiptResponse", "ReceiptWithPaymentDetails",
    "ReceiptListFilter", "ReceiptStatistics", "ReceiptDownloadResponse",
    
    # Fee Waiver
    "FeeWaiverBase", "FeeWaiverCreate", "FeeWaiverUpdate", "FeeWaiverApprovalRequest",
    "FeeWaiverResponse", "FeeWaiverSummary", "WaiverApprovalWorkflow",
    
    # Fee Reminder
    "ReminderChannel", "FeeReminderBase", "FeeReminderCreate", "FeeReminderUpdate",
    "FeeReminderResponse", "BulkFeeReminderCreate", "ReminderStatistics", "ReminderLog",
]