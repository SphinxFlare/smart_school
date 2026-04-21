# app/events/base.py


from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
from datetime import datetime
import uuid


@dataclass
class Event:
    """
    Standard event structure used across the system.
    """
    id: str
    topic: str
    payload: Dict[str, Any]
    created_at: datetime
    key: Optional[str] = None  # useful for Kafka partitioning later

    @staticmethod
    def create(topic: str, payload: Dict[str, Any], key: Optional[str] = None) -> "Event":
        return Event(
            id=str(uuid.uuid4()),
            topic=topic,
            payload=payload,
            created_at=datetime.utcnow(),
            key=key,
        )


class EventPublisher(ABC):
    """
    Contract for publishing events.
    Infrastructure (Redis/Kafka/etc.) implements this.
    """

    @abstractmethod
    def dispatch(self, event: Event) -> bool:
        pass