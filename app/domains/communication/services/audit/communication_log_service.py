# communication/services/audit/communication_log_service.py

from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from communication.models.notifications import CommunicationLog
from communication.repositories.notification.notification_repository import CommunicationLogRepository


class CommunicationLogService:
    """
    Service responsible for CommunicationLog (audit layer).

    Responsibilities:
    - Create log entries
    - Retrieve logs with filters

    Notes:
    - School-scoped
    - No soft delete
    - No business logic decisions (only logging)
    """

    def __init__(self):
        self.repo = CommunicationLogRepository()

    # ---------------------------------------------------------
    # Create
    # ---------------------------------------------------------

    def create_log(
        self,
        db: Session,
        *,
        school_id: UUID,
        communication_type: str,
        status: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        sender_id: Optional[UUID] = None,
        recipient_ids: Optional[List[UUID]] = None,
        channel: Optional[str] = None,
        sent_at: Optional[datetime] = None,
        delivered_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> CommunicationLog:
        """
        Create a communication log entry.

        Rules:
        - school_id, communication_type, status required
        """

        if not communication_type:
            raise ValueError("communication_type is required")

        if not status:
            raise ValueError("status is required")

        log = CommunicationLog(
            school_id=school_id,
            communication_type=communication_type,
            entity_type=entity_type,
            entity_id=entity_id,
            sender_id=sender_id,
            recipient_ids=recipient_ids,
            channel=channel,
            status=status,
            sent_at=sent_at,
            delivered_at=delivered_at,
            error_message=error_message,
            metadata=metadata,
        )

        return self.repo.create(db, log)

    # ---------------------------------------------------------
    # Retrieval
    # ---------------------------------------------------------

    def list_logs(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[CommunicationLog]:
        return self.repo.list_by_school(db, school_id, skip, limit)

    def get_by_type(
        self,
        db: Session,
        school_id: UUID,
        communication_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[CommunicationLog]:
        return self.repo.filter_by_communication_type(
            db, school_id, communication_type, skip, limit
        )

    def get_by_status(
        self,
        db: Session,
        school_id: UUID,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[CommunicationLog]:
        return self.repo.filter_by_status(db, school_id, status, skip, limit)

    def get_by_channel(
        self,
        db: Session,
        school_id: UUID,
        channel: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[CommunicationLog]:
        return self.repo.filter_by_channel(db, school_id, channel, skip, limit)

    def get_by_date_range(
        self,
        db: Session,
        school_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[CommunicationLog]:
        return self.repo.filter_by_date_range(
            db, school_id, start_date, end_date, skip, limit
        )

    def get_by_entity(
        self,
        db: Session,
        school_id: UUID,
        entity_type: str,
        entity_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[CommunicationLog]:
        return self.repo.get_by_entity_reference(
            db, school_id, entity_type, entity_id, skip, limit
        )

    # ---------------------------------------------------------
    # Aggregation
    # ---------------------------------------------------------

    def count_by_status(
        self,
        db: Session,
        school_id: UUID
    ) -> Dict[str, int]:
        return self.repo.count_by_status(db, school_id)