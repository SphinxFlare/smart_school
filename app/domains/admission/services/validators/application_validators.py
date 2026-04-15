# validators/application_validators.py

from typing import List, Dict, Any, Optional
from datetime import datetime

from admission.models.applications import AdmissionApplication, AdmissionDocument
from types.admissions import ApplicationStatus, DocumentType


# ---------------------------------------------------------------------
# Field Validation
# ---------------------------------------------------------------------

def validate_required_fields(data: Dict[str, Any]) -> None:
    """
    Validate that all required fields for an application are present.
    
    Args:
        data: Dictionary of incoming application data.
        
    Raises:
        ValueError: If any required field is missing or empty.
    """
    required_fields = ["first_name", "last_name", "date_of_birth", "gender"]
    
    for field in required_fields:
        if not data.get(field):
            raise ValueError(f"Required field '{field}' is missing or empty")

    if not isinstance(data.get("date_of_birth"), datetime):
        raise ValueError("Field 'date_of_birth' must be a valid datetime object")


# ---------------------------------------------------------------------
# State Validation (Application)
# ---------------------------------------------------------------------

def validate_can_submit(application: AdmissionApplication) -> None:
    """
    Validate that an application is in a state allowing submission.
    
    Args:
        application: The AdmissionApplication ORM object.
        
    Raises:
        ValueError: If application is not in DRAFT status.
    """
    if application.status != ApplicationStatus.DRAFT:
        raise ValueError(
            f"Cannot submit application: Current status is {application.status.value}"
        )


def validate_student_linked(application: AdmissionApplication) -> None:
    """
    Validate that an application is linked to a student profile.
    
    Args:
        application: The AdmissionApplication ORM object.
        
    Raises:
        ValueError: If student_id is None.
    """
    if not application.student_id:
        raise ValueError("Application must be linked to a student profile")


def validate_not_enrolled(application: AdmissionApplication) -> None:
    """
    Validate that an application is not already in a terminal enrolled state.
    
    Args:
        application: The AdmissionApplication ORM object.
        
    Raises:
        ValueError: If application is already APPROVED or ENROLLED.
    """
    if application.status in [ApplicationStatus.APPROVED, ApplicationStatus.ENROLLED]:
        raise ValueError(
            f"Cannot process: Application is already {application.status.value}"
        )


# ---------------------------------------------------------------------
# Document Validation
# ---------------------------------------------------------------------

def validate_documents_verified(documents: List[AdmissionDocument]) -> None:
    """
    Validate that all provided documents are verified.
    
    Args:
        documents: List of AdmissionDocument ORM objects.
        
    Raises:
        ValueError: If any document is unverified.
    """
    if not documents:
        # Optional: Enforce at least one document
        # raise ValueError("At least one document is required")
        return

    unverified = [doc for doc in documents if not doc.is_verified]
    if unverified:
        raise ValueError(
            f"{len(unverified)} document(s) are pending verification"
        )


def validate_required_document_types(
    documents: List[AdmissionDocument], 
    required_types: List[DocumentType]
) -> None:
    """
    Validate that all required document types are present and verified.
    
    Args:
        documents: List of existing AdmissionDocument ORM objects.
        required_types: List of DocumentType enums that are mandatory.
        
    Raises:
        ValueError: If a required type is missing or unverified.
    """
    existing_types = {doc.document_type for doc in documents if doc.is_verified}
    
    for req_type in required_types:
        if req_type not in existing_types:
            raise ValueError(f"Required document type '{req_type.value}' is missing or unverified")


# ---------------------------------------------------------------------
# Enrollment Validation
# ---------------------------------------------------------------------

def validate_no_existing_enrollment(enrollment) -> None:
    """
    Validate that no existing enrollment record exists.
    
    Args:
        enrollment: The result of an enrollment lookup (None if not found).
        
    Raises:
        ValueError: If an enrollment record already exists.
    """
    if enrollment:
        raise ValueError("Student is already enrolled for this academic year")