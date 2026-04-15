# types/addmission.py

from enum import Enum

class ApplicationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    WAITLISTED = "waitlisted"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class EnrollmentType(str, Enum):
    NEW_ADMISSION = "new_admission"
    EXISTING_STUDENT = "existing_student"
    TRANSFER_IN = "transfer_in"


class DocumentType(str, Enum):
    BIRTH_CERTIFICATE = "birth_certificate"
    ADDRESS_PROOF = "address_proof"
    PHOTO = "photo"
    TRANSFER_CERTIFICATE = "transfer_certificate"
    PREVIOUS_REPORT_CARD = "previous_report_card"
    OTHER = "other"