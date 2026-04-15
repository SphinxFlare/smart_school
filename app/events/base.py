# app/events/base.py


from abc import ABC, abstractmethod
from typing import Any, Dict

class EventPublisher(ABC):
    """
    The Interface. Every domain uses this to 'Shout' 
    news without knowing who is listening.
    """
    @abstractmethod
    def dispatch(self, topic: str, payload: Dict[str, Any]) -> bool:
        pass