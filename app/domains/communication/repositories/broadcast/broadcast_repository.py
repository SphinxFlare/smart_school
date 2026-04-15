# communication/repositories/broadcast/broadcast_repository.py


from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update
from sqlalchemy.dialects.postgresql import JSONB

from repositories.base import SchoolScopedRepository
from communication.models.broadcast import Announcement, Bulletin, DailyFeed


# ==========================================================
# Announcement Repository
# ==========================================================

class AnnouncementRepository(SchoolScopedRepository[Announcement]):
    """
    Repository for Announcement model operations.
    Handles school-scoped announcement persistence with soft-delete safety.
    """

    def __init__(self):
        super().__init__(Announcement)

    # -----------------------------------------
    # Published Announcements
    # -----------------------------------------

    def get_published_by_school(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Announcement]:
        """
        Retrieve published announcements by school.
        Filters by published_at <= now and (expires_at IS NULL OR expires_at > now).
        Preserves index usage on published_at and expires_at.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.published_at <= now,
                (self.model.expires_at.is_(None)) | (self.model.expires_at > now)
            )
            .order_by(
                self.model.is_pinned.desc(),
                self.model.priority.desc(),
                self.model.published_at.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_pinned_announcements(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Announcement]:
        """
        List pinned announcements ordered by is_pinned DESC, priority DESC, published_at DESC.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.is_pinned.is_(True),
                self.model.published_at <= now,
                (self.model.expires_at.is_(None)) | (self.model.expires_at > now)
            )
            .order_by(
                self.model.is_pinned.desc(),
                self.model.priority.desc(),
                self.model.published_at.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_type(
        self,
        db: Session,
        school_id: UUID,
        announcement_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Announcement]:
        """
        List announcements by type with deterministic ordering.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.announcement_type == announcement_type,
                self.model.published_at <= now,
                (self.model.expires_at.is_(None)) | (self.model.expires_at > now)
            )
            .order_by(self.model.published_at.desc(), self.model.id.desc())
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_category(
        self,
        db: Session,
        school_id: UUID,
        category: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Announcement]:
        """
        List announcements by category with deterministic ordering.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.category == category,
                self.model.published_at <= now,
                (self.model.expires_at.is_(None)) | (self.model.expires_at > now)
            )
            .order_by(self.model.published_at.desc(), self.model.id.desc())
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Target Filtering (JSONB)
    # -----------------------------------------

    def filter_by_target_role(
        self,
        db: Session,
        school_id: UUID,
        role: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Announcement]:
        """
        Filter announcements by target role using JSONB containment.
        Uses ? operator for JSONB array containment.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.target_roles.contains([role]),
                self.model.published_at <= now,
                (self.model.expires_at.is_(None)) | (self.model.expires_at > now)
            )
            .order_by(self.model.published_at.desc(), self.model.id.desc())
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def filter_by_target_class(
        self,
        db: Session,
        school_id: UUID,
        class_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Announcement]:
        """
        Filter announcements by target class using JSONB containment.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.target_classes.contains([str(class_id)]),
                self.model.published_at <= now,
                (self.model.expires_at.is_(None)) | (self.model.expires_at > now)
            )
            .order_by(self.model.published_at.desc(), self.model.id.desc())
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def filter_by_target_section(
        self,
        db: Session,
        school_id: UUID,
        section_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Announcement]:
        """
        Filter announcements by target section using JSONB containment.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.target_sections.contains([str(section_id)]),
                self.model.published_at <= now,
                (self.model.expires_at.is_(None)) | (self.model.expires_at > now)
            )
            .order_by(self.model.published_at.desc(), self.model.id.desc())
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Active Announcements
    # -----------------------------------------

    def get_active_announcements(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Announcement]:
        """
        Retrieve active (non-expired) announcements.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.published_at <= now,
                (self.model.expires_at.is_(None)) | (self.model.expires_at > now)
            )
            .order_by(self.model.published_at.desc(), self.model.id.desc())
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def count_active_announcements(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count active announcements with null-safe aggregation.
        """
        now = datetime.utcnow()
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.published_at <= now,
                (self.model.expires_at.is_(None)) | (self.model.expires_at > now)
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # View Counter (Row Locking)
    # -----------------------------------------

    def increment_views_count(
        self,
        db: Session,
        announcement_id: UUID
    ) -> Optional[int]:
        """
        Increment views_count using row locking to prevent race conditions.
        Returns the new count value.
        """
        # Lock the row for update
        stmt = (
            select(self.model)
            .where(self.model.id == announcement_id)
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        announcement = result.scalar_one_or_none()

        if announcement:
            announcement.views_count = (announcement.views_count or 0) + 1
            db.flush()
            return announcement.views_count
        return None


# ==========================================================
# Bulletin Repository
# ==========================================================

class BulletinRepository(SchoolScopedRepository[Bulletin]):
    """
    Repository for Bulletin model operations.
    Handles school-scoped bulletin persistence with soft-delete safety.
    """

    def __init__(self):
        super().__init__(Bulletin)

    # -----------------------------------------
    # Published Bulletins
    # -----------------------------------------

    def list_published_bulletins(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Bulletin]:
        """
        List published bulletins ordered by display_order ASC, published_at DESC.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.is_published.is_(True),
                self.model.published_at <= now,
                (self.model.expires_at.is_(None)) | (self.model.expires_at > now)
            )
            .order_by(
                self.model.display_order.asc(),
                self.model.published_at.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def filter_active_bulletins(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Bulletin]:
        """
        Filter active (published and not expired) bulletins.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.is_published.is_(True),
                self.model.published_at <= now,
                (self.model.expires_at.is_(None)) | (self.model.expires_at > now)
            )
            .order_by(self.model.published_at.desc(), self.model.id.desc())
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def filter_by_category(
        self,
        db: Session,
        school_id: UUID,
        category: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Bulletin]:
        """
        Filter bulletins by category with deterministic ordering.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.category == category,
                self.model.is_published.is_(True),
                self.model.published_at <= now,
                (self.model.expires_at.is_(None)) | (self.model.expires_at > now)
            )
            .order_by(self.model.display_order.asc())
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def count_published_bulletins(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count published bulletins with null-safe aggregation.
        """
        now = datetime.utcnow()
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.is_published.is_(True),
                self.model.published_at <= now,
                (self.model.expires_at.is_(None)) | (self.model.expires_at > now)
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # View Counter (Row Locking)
    # -----------------------------------------

    def increment_views_count(
        self,
        db: Session,
        bulletin_id: UUID
    ) -> Optional[int]:
        """
        Increment views_count using row locking to prevent race conditions.
        Returns the new count value.
        """
        stmt = (
            select(self.model)
            .where(self.model.id == bulletin_id)
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        bulletin = result.scalar_one_or_none()

        if bulletin:
            bulletin.views_count = (bulletin.views_count or 0) + 1
            db.flush()
            return bulletin.views_count
        return None


# ==========================================================
# Daily Feed Repository
# ==========================================================

class DailyFeedRepository(SchoolScopedRepository[DailyFeed]):
    """
    Repository for DailyFeed model operations.
    NOTE: DailyFeed model does NOT have is_deleted, so no soft-delete filtering applied.
    """

    def __init__(self):
        super().__init__(DailyFeed)

    # -----------------------------------------
    # Feed Listing
    # -----------------------------------------

    def list_feeds_by_date_range(
        self,
        db: Session,
        school_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[DailyFeed]:
        """
        List feeds by school and date range ordered by priority DESC, created_at DESC.
        Preserves index usage on school_id and feed_date.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.feed_date >= start_date,
                self.model.feed_date <= end_date
            )
            .order_by(
                self.model.priority.desc(),
                self.model.created_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        # NO soft-delete filter (model lacks is_deleted)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_unread_feeds(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[DailyFeed]:
        """
        List unread feeds for a school.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.is_read.is_(False)
            )
            .order_by(
                self.model.priority.desc(),
                self.model.created_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def filter_by_item_type(
        self,
        db: Session,
        school_id: UUID,
        item_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[DailyFeed]:
        """
        Filter feeds by item_type with deterministic ordering.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.item_type == item_type
            )
            .order_by(
                self.model.priority.desc(),
                self.model.created_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Read Status (Row Locking)
    # -----------------------------------------

    def mark_feed_as_read(
        self,
        db: Session,
        feed_id: UUID
    ) -> bool:
        """
        Mark feed as read using row locking.
        Returns True if successful, False if feed not found.
        """
        stmt = (
            select(self.model)
            .where(self.model.id == feed_id)
            .with_for_update()
        )
        result = db.execute(stmt)
        feed = result.scalar_one_or_none()

        if feed:
            feed.is_read = True
            feed.read_count = (feed.read_count or 0) + 1
            db.flush()
            return True
        return False

    def bulk_mark_as_read(
        self,
        db: Session,
        school_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """
        Bulk mark feeds as read for a school/date range.
        Returns count of updated rows.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.feed_date >= start_date,
                self.model.feed_date <= end_date,
                self.model.is_read.is_(False)
            )
            .values(
                is_read=True,
                read_count=self.model.read_count + 1
            )
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    # -----------------------------------------
    # Count Operations
    # -----------------------------------------

    def count_unread_feeds(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count unread items with null-safe aggregation.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.is_read.is_(False)
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0