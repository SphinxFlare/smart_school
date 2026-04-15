# app/events/redis_pub.py

import json
import logging
from typing import Any, Dict
import redis

from .base import EventPublisher


logger = logging.getLogger(__name__)


class RedisEventPublisher(EventPublisher):
    """
    Production-grade Redis implementation of the EventPublisher.

    - Safe initialization (app won't crash if Redis is down)
    - Non-blocking dispatch
    - Uses connection pool
    """

    def __init__(self, redis_url: str):
        self.client = None

        try:
            self.pool = redis.ConnectionPool.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=5.0,
            )

            self.client = redis.Redis(connection_pool=self.pool)

        except Exception as e:
            logger.error(f"Redis init failed: {e}")
            self.client = None

    def dispatch(self, topic: str, payload: Dict[str, Any]) -> bool:
        """
        Publishes a message to a Redis channel.

        Returns:
            True if dispatched
            False if failed or Redis unavailable
        """

        if not self.client:
            logger.warning("Redis client not available, event not dispatched")
            return False

        try:
            message = json.dumps(payload, default=str)

            self.client.publish(topic, message)

            logger.info(f"Successfully dispatched event to {topic}")
            return True

        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.error(f"Failed to dispatch event to {topic}: {e}")
            return False