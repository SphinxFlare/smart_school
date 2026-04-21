# communication/services/broadcast/bulletin_service.py

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from communication.models.broadcast import Bulletin
from communication.repositories.broadcast.broadcast_repository import BulletinRepository


class BulletinService:
    """
    Service responsible for Bulletin lifecycle.

    Responsibilities:
    - Create bulletin
    - Retrieve bulletins (published, active, category)
    - Increment views

    Notes:
    - School-scoped
    - Visibility controlled by is_published, published_at, expires_at
    """

    def __init__(self):
        self.repo = BulletinRepository()

    # ---------------------------------------------------------
    # Create
    # ---------------------------------------------------------

    def create_bulletin(
        self,
        db: Session,
        *,
        school_id: UUID,
        title: str,
        content: str,
        category: str,
        published_by_id: UUID,
        is_published: bool = False,
        published_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        display_order: int = 0,
    ) -> Bulletin:
        """
        Create a bulletin.

        Rules:
        - title, content, category required
        - if is_published=True → published_at must be set
        - expires_at must be > published_at (if both provided)
        """

        # ---------- Validation ----------

        if not title or not title.strip():
            raise ValueError("Title cannot be empty")

        if not content or not content.strip():
            raise ValueError("Content cannot be empty")

        if not category:
            raise ValueError("Category is required")

        if is_published and not published_at:
            raise ValueError("published_at must be provided when publishing")

        if published_at and expires_at and expires_at <= published_at:
            raise ValueError("expires_at must be greater than published_at")

        # ---------- Create ----------

        bulletin = Bulletin(
            school_id=school_id,
            title=title.strip(),
            content=content.strip(),
            category=category,
            display_order=display_order,
            is_published=is_published,
            published_at=published_at,
            expires_at=expires_at,
            published_by_id=published_by_id,
        )

        return self.repo.create(db, bulletin)

    # ---------------------------------------------------------
    # Retrieval
    # ---------------------------------------------------------

    def get_published(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Bulletin]:
        return self.repo.list_published_bulletins(db, school_id, skip, limit)

    def get_active(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Bulletin]:
        return self.repo.filter_active_bulletins(db, school_id, skip, limit)

    def get_by_category(
        self,
        db: Session,
        school_id: UUID,
        category: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Bulletin]:
        return self.repo.filter_by_category(db, school_id, category, skip, limit)

    def count_published(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        return self.repo.count_published_bulletins(db, school_id)

    # ---------------------------------------------------------
    # Actions
    # ---------------------------------------------------------

    def increment_views(
        self,
        db: Session,
        bulletin_id: UUID
    ) -> Optional[int]:
        return self.repo.increment_views_count(db, bulletin_id)

    # ---------------------------------------------------------
    # Delete
    # ---------------------------------------------------------

    def delete_bulletin(
        self,
        db: Session,
        bulletin_id: UUID
    ) -> None:
        bulletin = self.repo.get(db, bulletin_id)

        if not bulletin:
            raise ValueError("Bulletin not found")

        self.repo.delete(db, bulletin)