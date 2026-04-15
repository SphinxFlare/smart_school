# admission/services/rules/status_transitions.py

from typing import Dict, List
from types.admissions import ApplicationStatus


# ---------------------------------------------------------------------
# Static Rule Definitions
# ---------------------------------------------------------------------

VALID_APPLICATION_TRANSITIONS: Dict[ApplicationStatus, List[ApplicationStatus]] = {
    ApplicationStatus.DRAFT: [ApplicationStatus.SUBMITTED],
    ApplicationStatus.SUBMITTED: [
        ApplicationStatus.UNDER_REVIEW, 
        ApplicationStatus.REJECTED,
        ApplicationStatus.APPROVED
    ],
    ApplicationStatus.UNDER_REVIEW: [
        ApplicationStatus.APPROVED, 
        ApplicationStatus.REJECTED,
        ApplicationStatus.SUBMITTED  # Allow re-submission if info requested
    ],
    ApplicationStatus.APPROVED: [
        ApplicationStatus.ENROLLED  # Transition to enrolled once enrollment is created
    ],
    ApplicationStatus.REJECTED: [],  # Terminal state
    ApplicationStatus.ENROLLED: [],  # Terminal state
}


# ---------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------

def is_valid_transition(from_status: ApplicationStatus, to_status: ApplicationStatus) -> bool:
    """
    Check if a status transition is allowed based on static rules.
    
    Args:
        from_status: The current status.
        to_status: The target status.
        
    Returns:
        True if transition is allowed, False otherwise.
    """
    allowed_next_statuses = VALID_APPLICATION_TRANSITIONS.get(from_status, [])
    return to_status in allowed_next_statuses


def get_allowed_transitions(from_status: ApplicationStatus) -> List[ApplicationStatus]:
    """
    Retrieve all allowed next statuses for a given current status.
    
    Args:
        from_status: The current status.
        
    Returns:
        List of allowed ApplicationStatus values.
    """
    return VALID_APPLICATION_TRANSITIONS.get(from_status, [])