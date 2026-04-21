# app/events/publishers/redis_pub.py

import json
import logging
import redis

from ..base import EventPublisher, Event


logger = logging.getLogger(__name__)


class RedisEventPublisher(EventPublisher):
    """
    Redis implementation of EventPublisher.

    - Safe initialization
    - Uses connection pool
    - Publishes standardized Event payload
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

    def dispatch(self, event: Event) -> bool:
        """
        Publishes an Event to a Redis channel (topic).
        """

        if not self.client:
            logger.warning("Redis client not available, event not dispatched")
            return False

        try:
            message = json.dumps(
                {
                    "id": event.id,
                    "topic": event.topic,
                    "payload": event.payload,
                    "created_at": event.created_at.isoformat(),
                    "key": event.key,
                },
                default=str,
            )

            self.client.publish(event.topic, message)

            logger.info(f"Event dispatched → topic={event.topic}, id={event.id}")
            return True

        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.error(f"Failed to dispatch event {event.id}: {e}")
            return False