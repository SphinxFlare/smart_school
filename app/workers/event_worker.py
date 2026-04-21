# app/workers/event_worker.py

import time
import logging

from sqlalchemy.orm import Session

from app.events.base import Event
from app.events.publishers.redis_pub import RedisEventPublisher
from app.events.outbox.repository import OutboxRepository


logger = logging.getLogger(__name__)


class EventWorker:
    """
    Reads events from outbox and publishes them using EventPublisher.
    """

    def __init__(
        self,
        db: Session,
        publisher: RedisEventPublisher,
        poll_interval: float = 2.0,
        batch_size: int = 100,
        max_retries: int = 5,
    ):
        self.db = db
        self.publisher = publisher
        self.poll_interval = poll_interval
        self.batch_size = batch_size
        self.max_retries = max_retries

        self.repo = OutboxRepository(db)

    def run(self):
        logger.info("Event worker started")

        while True:
            try:
                events = self.repo.get_pending(limit=self.batch_size)

                if not events:
                    time.sleep(self.poll_interval)
                    continue

                for record in events:
                    event = Event(
                        id=record.id,
                        topic=record.topic,
                        payload=record.payload,
                        created_at=record.created_at,
                    )

                    success = self.publisher.dispatch(event)

                    if success:
                        self.repo.mark_sent(record.id)
                    else:
                        if record.retry_count >= self.max_retries:
                            logger.error(
                                f"Event {record.id} failed permanently after retries"
                            )
                            self.repo.mark_failed(record.id)
                        else:
                            self.repo.mark_failed(record.id)

                self.db.commit()

            except Exception as e:
                logger.exception(f"Worker error: {e}")
                self.db.rollback()
                time.sleep(self.poll_interval)