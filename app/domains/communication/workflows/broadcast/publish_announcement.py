# communication/workflows/broadcast/publish_announcement.py

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from communication.services.broadcast.announcement_service import AnnouncementService
from communication.services.broadcast.feed_service import FeedService

from app.events.base import Event
from app.events.outbox.repository import OutboxRepository


class PublishAnnouncementWorkflow:
    """
    Orchestrates announcement publishing.

    Flow:
    - create announcement
    - create feed entry (optional)
    - write outbox event
    """

    def __init__(self):
        self.announcement_service = AnnouncementService()
        self.feed_service = FeedService()

    def execute(
        self,
        db: Session,
        *,
        school_id: UUID,
        title: str,
        content: str,
        announcement_type: str,
        published_by_id: UUID,
        published_at: datetime,
        category: Optional[str] = None,
        target_roles: Optional[List[str]] = None,
        target_classes: Optional[List[UUID]] = None,
        target_sections: Optional[List[UUID]] = None,
        expires_at: Optional[datetime] = None,
        is_pinned: bool = False,
        priority: str = "normal",
        attachments: Optional[dict] = None,
        create_feed: bool = True,
    ):
        # -----------------------------------------------------
        # Step 1: Create Announcement
        # -----------------------------------------------------

        announcement = self.announcement_service.create_announcement(
            db=db,
            school_id=school_id,
            title=title,
            content=content,
            announcement_type=announcement_type,
            published_by_id=published_by_id,
            published_at=published_at,
            category=category,
            target_roles=target_roles,
            target_classes=target_classes,
            target_sections=target_sections,
            expires_at=expires_at,
            is_pinned=is_pinned,
            priority=priority,
            attachments=attachments,
        )

        # -----------------------------------------------------
        # Step 2: Create Feed (optional)
        # -----------------------------------------------------

        if create_feed:
            self.feed_service.create_feed(
                db=db,
                school_id=school_id,
                feed_date=published_at,
                item_type="announcement",
                source_type="announcement",
                source_id=announcement.id,
                title=title,
                summary=content[:200] if content else None,
                priority=priority,
            )

        # -----------------------------------------------------
        # Step 3: Outbox Event
        # -----------------------------------------------------

        event = Event(
            topic="communication.announcement.published",
            payload={
                "announcement_id": str(announcement.id),
                "school_id": str(school_id),
                "type": announcement_type,
                "priority": priority,
                "is_pinned": is_pinned,
            },
        )

        outbox = OutboxRepository(db)
        outbox.add(event)

        return announcement