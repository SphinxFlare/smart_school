# welfare/schemas/__init__.py


"""
Welfare Domain Schemas
Public interface for all welfare-related data schemas
"""

# Base schemas
from .base import (
    DomainBase,
    TimestampSchema
)

# Concern management schemas
from .concern import (
    CustomConcernType,
    ConcernBase,
    ConcernCreate,
    ConcernUpdate,
    ConcernResponse,
    ConcernReference,
    ConcernAssignmentBase,
    ConcernAssignmentCreate,
    ConcernAssignmentUpdate,
    ConcernAssignmentResponse,
    ConcernCommentBase,
    ConcernCommentCreate,
    ConcernCommentUpdate,
    ConcernCommentResponse,
    ConcernHistoryEntry,
    EscalationBase,
    EscalationCreate,
    EscalationUpdate,
    EscalationResponse,
    ConcernSummary,
    ConcernFilter,
    BulkConcernCreate,
    ConcernAnalytics,
    ConcernExportFormat,
    ConcernNotificationSettings
)

# Meeting management schemas
from .meeting import (
    MeetingParticipantBase,
    MeetingParticipantCreate,
    MeetingParticipantUpdate,
    MeetingParticipantResponse,
    MeetingAgendaBase,
    MeetingAgendaCreate,
    MeetingAgendaUpdate,
    MeetingAgendaResponse,
    MeetingOutcomeBase,
    MeetingOutcomeCreate,
    MeetingOutcomeUpdate,
    MeetingOutcomeResponse,
    MeetingAttendanceBase,
    MeetingAttendanceCreate,
    MeetingAttendanceUpdate,
    MeetingAttendanceResponse,
    MeetingBase,
    MeetingCreate,
    MeetingUpdate,
    MeetingResponse,
    MeetingSummary,
    MeetingFilter,
    MeetingStatistics,
    MeetingReminder
)

# Observation & wellness schemas
from .observation import (
    StudentObservationBase,
    StudentObservationCreate,
    StudentObservationUpdate,
    StudentObservationResponse,
    ObservationSummary,
    ObservationTrend,
    WellnessCheckBase,
    WellnessCheckCreate,
    WellnessCheckUpdate,
    WellnessCheckResponse,
    WellnessCheckReference,
    WellnessCheckSummary,
    BulkObservationCreate,
    ObservationReportFilter
)

__all__ = [
    # ======================
    # BASE SCHEMAS
    # ======================
    "DomainBase",
    "TimestampSchema",
    
    # ======================
    # CONCERN MANAGEMENT
    # ======================
    "CustomConcernType",
    "ConcernBase",
    "ConcernCreate",
    "ConcernUpdate",
    "ConcernResponse",
    "ConcernReference",
    "ConcernAssignmentBase",
    "ConcernAssignmentCreate",
    "ConcernAssignmentUpdate",
    "ConcernAssignmentResponse",
    "ConcernCommentBase",
    "ConcernCommentCreate",
    "ConcernCommentUpdate",
    "ConcernCommentResponse",
    "ConcernHistoryEntry",
    "EscalationBase",
    "EscalationCreate",
    "EscalationUpdate",
    "EscalationResponse",
    "ConcernSummary",
    "ConcernFilter",
    "BulkConcernCreate",
    "ConcernAnalytics",
    "ConcernExportFormat",
    "ConcernNotificationSettings",
    
    # ======================
    # MEETING MANAGEMENT
    # ======================
    "MeetingParticipantBase",
    "MeetingParticipantCreate",
    "MeetingParticipantUpdate",
    "MeetingParticipantResponse",
    "MeetingAgendaBase",
    "MeetingAgendaCreate",
    "MeetingAgendaUpdate",
    "MeetingAgendaResponse",
    "MeetingOutcomeBase",
    "MeetingOutcomeCreate",
    "MeetingOutcomeUpdate",
    "MeetingOutcomeResponse",
    "MeetingAttendanceBase",
    "MeetingAttendanceCreate",
    "MeetingAttendanceUpdate",
    "MeetingAttendanceResponse",
    "MeetingBase",
    "MeetingCreate",
    "MeetingUpdate",
    "MeetingResponse",
    "MeetingSummary",
    "MeetingFilter",
    "MeetingStatistics",
    "MeetingReminder",
    
    # ======================
    # OBSERVATION & WELLNESS
    # ======================
    "StudentObservationBase",
    "StudentObservationCreate",
    "StudentObservationUpdate",
    "StudentObservationResponse",
    "ObservationSummary",
    "ObservationTrend",
    "WellnessCheckBase",
    "WellnessCheckCreate",
    "WellnessCheckUpdate",
    "WellnessCheckResponse",
    "WellnessCheckReference",
    "WellnessCheckSummary",
    "BulkObservationCreate",
    "ObservationReportFilter",
]

# Module-level documentation
__doc__ = """
Welfare Domain Schemas Package

This package contains all Pydantic schemas for the welfare domain, covering:
- Student concern management (reporting, assignment, escalation, resolution)
- Meeting management (scheduling, participants, agenda, outcomes)
- Student observations and wellness checks

All schemas follow strict validation rules and domain boundaries.
Cross-domain references use forward references to prevent circular imports.

Usage:
    from app.domains.welfare.schemas import ConcernCreate, MeetingResponse
"""