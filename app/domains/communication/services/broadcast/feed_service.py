# communication/services/broadcast/feed_service.py

from typing import List
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from communication.models.broadcast import DailyFeed
from communication.repositories.broadcast.broadcast_repository import DailyFeedRepository


class FeedService:
    """
    Service responsible for DailyFeed operations.

    Responsibilities:
    - Create feed items
    - Retrieve feeds (date range, unread, type)
    - Manage read state

    Notes:
    - School-scoped
    - No soft delete in model
    """

    def __init__(self):
        self.repo = DailyFeedRepository()

    # ---------------------------------------------------------
    # Create
    # ---------------------------------------------------------

    def create_feed(
        self,
        db: Session,
        *,
        school_id: UUID,
        feed_date: datetime,
        item_type: str,
        source_type: str,
        source_id: UUID,
        title: str,
        summary: str | None = None,
        priority: str = "normal",
    ) -> DailyFeed:
        """
        Create a feed item.

        Rules:
        - school_id, feed_date, item_type, source_type, source_id, title required
        """

        if not title or not title.strip():
            raise ValueError("Title cannot be empty")

        if not item_type:
            raise ValueError("item_type is required")

        if not source_type:
            raise ValueError("source_type is required")

        if not source_id:
            raise ValueError("source_id is required")

        if not feed_date:
            raise ValueError("feed_date is required")

        feed = DailyFeed(
            school_id=school_id,
            feed_date=feed_date,
            item_type=item_type,
            source_type=source_type,
            source_id=source_id,
            title=title.strip(),
            summary=summary,
            priority=priority,
        )

        return self.repo.create(db, feed)

    # ---------------------------------------------------------
    # Retrieval
    # ---------------------------------------------------------

    def get_by_date_range(
        self,
        db: Session,
        school_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[DailyFeed]:
        return self.repo.list_feeds_by_date_range(
            db, school_id, start_date, end_date, skip, limit
        )

    def get_unread(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[DailyFeed]:
        return self.repo.list_unread_feeds(db, school_id, skip, limit)

    def get_by_item_type(
        self,
        db: Session,
        school_id: UUID,
        item_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[DailyFeed]:
        return self.repo.filter_by_item_type(db, school_id, item_type, skip, limit)

    def count_unread(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        return self.repo.count_unread_feeds(db, school_id)

    # ---------------------------------------------------------
    # Read State
    # ---------------------------------------------------------

    def mark_as_read(
        self,
        db: Session,
        feed_id: UUID
    ) -> bool:
        return self.repo.mark_feed_as_read(db, feed_id)

    def bulk_mark_as_read(
        self,
        db: Session,
        *,
        school_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        return self.repo.bulk_mark_as_read(db, school_id, start_date, end_date)