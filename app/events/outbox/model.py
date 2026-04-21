# app/events/outbox/model.py

from sqlalchemy import Column, String, DateTime, Integer, Index
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from app.db.base import Base


class OutboxEvent(Base):
    """
    Outbox table for reliable event publishing.

    Events are written here inside the same DB transaction
    as domain changes, then processed by a worker.
    """

    __tablename__ = "outbox_events"

    id = Column(String, primary_key=True)  # same as Event.id
    topic = Column(String, nullable=False)
    payload = Column(JSONB, nullable=False)

    status = Column(String, default="pending", nullable=False)
    # pending | sent | failed

    retry_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime)

    __table_args__ = (
        Index("ix_outbox_status", "status"),
        Index("ix_outbox_created_at", "created_at"),
    )