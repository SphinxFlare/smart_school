# communication/services/broadcast/announcement_service.py

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from communication.models.broadcast import Announcement
from communication.repositories.broadcast.broadcast_repository import AnnouncementRepository


class AnnouncementService:
    """
    Service responsible for Announcement lifecycle.

    Responsibilities:
    - Create announcement
    - Retrieve announcements (various filters)
    - Increment views

    Notes:
    - School-scoped (multi-tenant)
    - Time-based visibility handled in repository
    """

    def __init__(self):
        self.repo = AnnouncementRepository()

    # ---------------------------------------------------------
    # Create
    # ---------------------------------------------------------

    def create_announcement(
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
    ) -> Announcement:
        """
        Create a new announcement.

        Rules:
        - title and content required
        - published_at required (supports scheduling)
        - expires_at must be > published_at (if provided)
        """

        # ---------- Validation ----------

        if not title or not title.strip():
            raise ValueError("Title cannot be empty")

        if not content or not content.strip():
            raise ValueError("Content cannot be empty")

        if not published_at:
            raise ValueError("published_at is required")

        if expires_at and expires_at <= published_at:
            raise ValueError("expires_at must be greater than published_at")

        # Normalize JSON fields (store as strings where needed)
        target_classes_str = [str(c) for c in target_classes] if target_classes else None
        target_sections_str = [str(s) for s in target_sections] if target_sections else None

        # ---------- Create ----------

        announcement = Announcement(
            school_id=school_id,
            title=title.strip(),
            content=content.strip(),
            announcement_type=announcement_type,
            category=category,
            target_roles=target_roles,
            target_classes=target_classes_str,
            target_sections=target_sections_str,
            published_by_id=published_by_id,
            published_at=published_at,
            expires_at=expires_at,
            is_pinned=is_pinned,
            priority=priority,
            attachments=attachments,
        )

        return self.repo.create(db, announcement)

    # ---------------------------------------------------------
    # Retrieval
    # ---------------------------------------------------------

    def get_published(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Announcement]:
        return self.repo.get_published_by_school(db, school_id, skip, limit)

    def get_pinned(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Announcement]:
        return self.repo.list_pinned_announcements(db, school_id, skip, limit)

    def get_by_type(
        self,
        db: Session,
        school_id: UUID,
        announcement_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Announcement]:
        return self.repo.list_by_type(db, school_id, announcement_type, skip, limit)

    def get_by_category(
        self,
        db: Session,
        school_id: UUID,
        category: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Announcement]:
        return self.repo.list_by_category(db, school_id, category, skip, limit)

    def get_by_role(
        self,
        db: Session,
        school_id: UUID,
        role: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Announcement]:
        return self.repo.filter_by_target_role(db, school_id, role, skip, limit)

    def get_by_class(
        self,
        db: Session,
        school_id: UUID,
        class_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Announcement]:
        return self.repo.filter_by_target_class(db, school_id, class_id, skip, limit)

    def get_by_section(
        self,
        db: Session,
        school_id: UUID,
        section_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Announcement]:
        return self.repo.filter_by_target_section(db, school_id, section_id, skip, limit)

    def get_active(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Announcement]:
        return self.repo.get_active_announcements(db, school_id, skip, limit)

    def count_active(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        return self.repo.count_active_announcements(db, school_id)

    # ---------------------------------------------------------
    # Actions
    # ---------------------------------------------------------

    def increment_views(
        self,
        db: Session,
        announcement_id: UUID
    ) -> Optional[int]:
        return self.repo.increment_views_count(db, announcement_id)

    # ---------------------------------------------------------
    # Delete
    # ---------------------------------------------------------

    def delete_announcement(
        self,
        db: Session,
        announcement_id: UUID
    ) -> None:
        announcement = self.repo.get(db, announcement_id)

        if not announcement:
            raise ValueError("Announcement not found")

        self.repo.delete(db, announcement)