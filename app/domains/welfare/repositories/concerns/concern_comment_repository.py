# welfare/repositories/complaints/concern_comment_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update, delete

from repositories.base import BaseRepository
from welfare.models.complaints import ConcernComment


class ConcernCommentRepository(BaseRepository[ConcernComment]):
    """
    Repository for ConcernComment model operations.
    Extends BaseRepository - model does NOT contain school_id.
    Tenant isolation enforced through concern_id scoping at service layer.
    Soft-delete aware (ConcernComment model has is_deleted).
    Zero business logic, zero validation, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(ConcernComment)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        comment_id: UUID
    ) -> Optional[ConcernComment]:
        """
        Retrieve comment by ID.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(self.model.id == comment_id)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_id_concern_scoped(
        self,
        db: Session,
        comment_id: UUID,
        concern_id: UUID
    ) -> Optional[ConcernComment]:
        """
        Retrieve comment by ID scoped to concern.
        Prevents unauthorized access across concerns.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == comment_id,
                self.model.concern_id == concern_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Listing Methods
    # -----------------------------------------

    def list_by_concern(
        self,
        db: Session,
        concern_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ConcernComment]:
        """
        List comments for a concern.
        Deterministic ordering: created_at ASC, id ASC (thread order).
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(self.model.concern_id == concern_id)
            .order_by(
                self.model.created_at.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_concern_ordered(
        self,
        db: Session,
        concern_id: UUID
    ) -> List[ConcernComment]:
        """
        List all comments for a concern ordered by thread.
        No pagination - returns all comments for concern processing.
        Deterministic ordering: created_at ASC, id ASC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(self.model.concern_id == concern_id)
            .order_by(
                self.model.created_at.asc(),
                self.model.id.asc()
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_user(
        self,
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ConcernComment]:
        """
        List comments by a user across all concerns.
        Deterministic ordering: created_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(
                self.model.created_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_internal_comments(
        self,
        db: Session,
        concern_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ConcernComment]:
        """
        List internal comments (staff-only) for a concern.
        Deterministic ordering: created_at ASC, id ASC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.concern_id == concern_id,
                self.model.is_internal.is_(True)
            )
            .order_by(
                self.model.created_at.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_public_comments(
        self,
        db: Session,
        concern_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ConcernComment]:
        """
        List public comments (visible to parents) for a concern.
        Deterministic ordering: created_at ASC, id ASC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.concern_id == concern_id,
                self.model.is_internal.is_(False)
            )
            .order_by(
                self.model.created_at.asc(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_deleted(
        self,
        db: Session,
        concern_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ConcernComment]:
        """
        List soft-deleted comments.
        Does NOT apply soft-delete filter (explicitly includes deleted).
        Deterministic ordering: created_at DESC, id DESC.
        """
        stmt = select(self.model).where(
            self.model.is_deleted.is_(True)
        )
        
        if concern_id:
            stmt = stmt.where(self.model.concern_id == concern_id)
        
        stmt = (
            stmt.order_by(
                self.model.created_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Row Locking
    # -----------------------------------------

    def lock_for_update(
        self,
        db: Session,
        comment_id: UUID
    ) -> Optional[ConcernComment]:
        """
        Lock comment for update.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(self.model.id == comment_id)
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_for_update_concern_scoped(
        self,
        db: Session,
        comment_id: UUID,
        concern_id: UUID
    ) -> Optional[ConcernComment]:
        """
        Lock comment for update scoped to concern.
        Maximum concurrency safety for sensitive mutation.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == comment_id,
                self.model.concern_id == concern_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_all_by_concern_for_update(
        self,
        db: Session,
        concern_id: UUID
    ) -> List[ConcernComment]:
        """
        Lock all comments for a concern.
        Used for batch operations.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(self.model.concern_id == concern_id)
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Existence Checks
    # -----------------------------------------

    def exists_by_id(
        self,
        db: Session,
        comment_id: UUID
    ) -> bool:
        """
        Efficient existence check for comment by ID.
        Soft-delete filtered.
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(self.model.id == comment_id)
            .limit(1)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_by_id_concern_scoped(
        self,
        db: Session,
        comment_id: UUID,
        concern_id: UUID
    ) -> bool:
        """
        Efficient existence check for comment by ID scoped to concern.
        Soft-delete filtered.
        Uses select(id).limit(1) pattern.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == comment_id,
                self.model.concern_id == concern_id
            )
            .limit(1)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    # -----------------------------------------
    # Aggregations (Null-Safe)
    # -----------------------------------------

    def count_by_concern(
        self,
        db: Session,
        concern_id: UUID
    ) -> int:
        """
        Count comments for a concern.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.concern_id == concern_id)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_user(
        self,
        db: Session,
        user_id: UUID
    ) -> int:
        """
        Count comments by a user across all concerns.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.user_id == user_id)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_internal_comments(
        self,
        db: Session,
        concern_id: UUID
    ) -> int:
        """
        Count internal comments for a concern.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.concern_id == concern_id,
                self.model.is_internal.is_(True)
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_public_comments(
        self,
        db: Session,
        concern_id: UUID
    ) -> int:
        """
        Count public comments for a concern.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.concern_id == concern_id,
                self.model.is_internal.is_(False)
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_deleted(
        self,
        db: Session,
        concern_id: Optional[UUID] = None
    ) -> int:
        """
        Count soft-deleted comments.
        Null-safe aggregation.
        Does NOT apply soft-delete filter.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.is_deleted.is_(True)
        )
        
        if concern_id:
            stmt = stmt.where(self.model.concern_id == concern_id)
        
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # Soft Delete Operations
    # -----------------------------------------

    def soft_delete(
        self,
        db: Session,
        comment_id: UUID
    ) -> bool:
        """
        Soft delete comment record.
        Returns True if successful.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(self.model.id == comment_id)
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        comment = result.scalar_one_or_none()

        if comment:
            comment.is_deleted = True
            comment.deleted_at = now
            db.flush()
            return True
        return False

    def soft_delete_concern_scoped(
        self,
        db: Session,
        comment_id: UUID,
        concern_id: UUID
    ) -> bool:
        """
        Soft delete comment record scoped to concern.
        Returns True if successful.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.id == comment_id,
                self.model.concern_id == concern_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        comment = result.scalar_one_or_none()

        if comment:
            comment.is_deleted = True
            comment.deleted_at = now
            db.flush()
            return True
        return False

    def restore(
        self,
        db: Session,
        comment_id: UUID
    ) -> bool:
        """
        Restore soft-deleted comment record.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == comment_id,
                self.model.is_deleted.is_(True)
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        comment = result.scalar_one_or_none()

        if comment:
            comment.is_deleted = False
            comment.deleted_at = None
            db.flush()
            return True
        return False

    # -----------------------------------------
    # Bulk Operations (Atomic, Empty Guards)
    # -----------------------------------------

    def bulk_update_by_concern(
        self,
        db: Session,
        concern_id: UUID,
        updates: Dict[str, Any]
    ) -> int:
        """
        Bulk update comments for a concern.
        Atomic update statement scoped by concern_id.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not updates:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.concern_id == concern_id,
                self.model.is_deleted.is_(False)
            )
            .values(**updates)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_by_user(
        self,
        db: Session,
        user_id: UUID,
        updates: Dict[str, Any]
    ) -> int:
        """
        Bulk update comments by a user.
        Atomic update statement scoped by user_id.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not updates:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.is_deleted.is_(False)
            )
            .values(**updates)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_soft_delete_by_concern(
        self,
        db: Session,
        concern_id: UUID
    ) -> int:
        """
        Bulk soft delete all comments for a concern.
        Atomic update statement scoped by concern_id.
        Returns count of updated rows.
        """
        now = datetime.utcnow()
        stmt = (
            update(self.model)
            .where(
                self.model.concern_id == concern_id,
                self.model.is_deleted.is_(False)
            )
            .values(is_deleted=True, deleted_at=now)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_restore_by_concern(
        self,
        db: Session,
        concern_id: UUID
    ) -> int:
        """
        Bulk restore all soft-deleted comments for a concern.
        Atomic update statement scoped by concern_id.
        Returns count of updated rows.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.concern_id == concern_id,
                self.model.is_deleted.is_(True)
            )
            .values(is_deleted=False, deleted_at=None)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_delete_by_concern(
        self,
        db: Session,
        concern_id: UUID
    ) -> int:
        """
        Bulk delete all comments for a concern.
        Atomic delete statement scoped by concern_id.
        Returns count of deleted rows.
        NO soft-delete filter (hard delete).
        """
        stmt = (
            delete(self.model)
            .where(self.model.concern_id == concern_id)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0