# app/events/outbox/repository.py

from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from .model import OutboxEvent
from app.events.base import Event


class OutboxRepository:
    """
    Handles persistence of outbox events.
    Used by workflows (write) and workers (read/update).
    """

    def __init__(self, db: Session):
        self.db = db

    # --- Write (from workflows) ---
    def add(self, event: Event) -> OutboxEvent:
        record = OutboxEvent(
            id=event.id,
            topic=event.topic,
            payload=event.payload,
            status="pending",
            created_at=event.created_at,
        )
        self.db.add(record)
        return record

    # --- Read (for worker) ---
    def get_pending(self, limit: int = 100) -> List[OutboxEvent]:
        return (
            self.db.query(OutboxEvent)
            .filter(OutboxEvent.status == "pending")
            .order_by(OutboxEvent.created_at.asc())
            .limit(limit)
            .all()
        )

    # --- Update ---
    def mark_sent(self, event_id: str) -> None:
        event = self._get(event_id)
        if not event:
            return

        event.status = "sent"
        event.processed_at = datetime.utcnow()

    def mark_failed(self, event_id: str) -> None:
        event = self._get(event_id)
        if not event:
            return

        event.status = "failed"
        event.retry_count += 1
        event.processed_at = datetime.utcnow()

    # --- Internal ---
    def _get(self, event_id: str) -> Optional[OutboxEvent]:
        return (
            self.db.query(OutboxEvent)
            .filter(OutboxEvent.id == event_id)
            .one_or_none()
        )