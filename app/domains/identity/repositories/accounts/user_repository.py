# identity/repositories/accounts/user_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from repositories.base import SchoolScopedRepository
from identity.models.accounts import User


class UserRepository(SchoolScopedRepository[User]):
    """
    Repository for User model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    Soft-delete aware (User model has is_deleted).
    Zero authentication logic, zero password hashing, zero token handling.
    """

    def __init__(self):
        super().__init__(User)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID
    ) -> Optional[User]:
        """
        Retrieve user by ID scoped to school.
        Prevents horizontal privilege escalation.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == user_id,
                self.model.school_id == school_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Composite Uniqueness Lookups
    # -----------------------------------------

    def get_by_email(
        self,
        db: Session,
        school_id: UUID,
        email: str
    ) -> Optional[User]:
        """
        Retrieve user by email scoped to school.
        Respects unique constraint (school_id, email).
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.email == email
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_phone(
        self,
        db: Session,
        school_id: UUID,
        phone: str
    ) -> Optional[User]:
        """
        Retrieve user by phone scoped to school.
        Respects unique constraint (school_id, phone).
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.phone == phone
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Listing Methods
    # -----------------------------------------

    def list_by_school(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        List all users within school tenant.
        Deterministic ordering: created_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(self.model.school_id == school_id)
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

    def list_active_users(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        List active users within school tenant.
        Deterministic ordering: created_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.is_active.is_(True)
            )
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

    def list_inactive_users(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        List inactive users within school tenant.
        Deterministic ordering: created_at DESC, id DESC.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.is_active.is_(False)
            )
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

    def list_deleted_users(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        List soft-deleted users within school tenant.
        Does NOT apply soft-delete filter (explicitly includes deleted).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
            .order_by(
                self.model.deleted_at.desc(),
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
        school_id: UUID,
        user_id: UUID
    ) -> Optional[User]:
        """
        Lock user for update (authentication-sensitive operations).
        Scoped to school_id for tenant safety.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == user_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_for_password_change(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID
    ) -> Optional[User]:
        """
        Lock user for password change operation.
        Maximum concurrency safety for authentication-sensitive update.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == user_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_for_activation(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID
    ) -> Optional[User]:
        """
        Lock user for activation/deactivation operation.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == user_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Existence Checks
    # -----------------------------------------

    def exists_by_id(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Efficient existence check for user by ID.
        Soft-delete filtered.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == user_id,
                self.model.school_id == school_id
            )
            .limit(1)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_email(
        self,
        db: Session,
        school_id: UUID,
        email: str,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for email within school.
        Respects unique constraint (school_id, email).
        Optional exclude_id for update operations.
        Soft-delete filtered.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.school_id == school_id,
            self.model.email == email
        )
        
        if exclude_id is not None:
            stmt = stmt.where(self.model.id != exclude_id)
        
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        count = result.scalar() or 0
        return count > 0

    def exists_phone(
        self,
        db: Session,
        school_id: UUID,
        phone: str,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for phone within school.
        Respects unique constraint (school_id, phone).
        Optional exclude_id for update operations.
        Soft-delete filtered.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.school_id == school_id,
            self.model.phone == phone
        )
        
        if exclude_id:
            stmt = stmt.where(self.model.id != exclude_id)
        
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        count = result.scalar() or 0
        return count > 0

    # -----------------------------------------
    # Aggregations (Null-Safe)
    # -----------------------------------------

    def count_active(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count active users within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.is_active.is_(True)
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_inactive(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count inactive users within school.
        Null-safe aggregation.
        Soft-delete filtered.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.is_active.is_(False)
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_deleted(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count soft-deleted users within school.
        Null-safe aggregation.
        Does NOT apply soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_total(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count total users (including deleted) within school.
        Null-safe aggregation.
        Does NOT apply soft-delete filter.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.school_id == school_id)
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # Soft Delete Operations
    # -----------------------------------------

    def soft_delete(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Soft delete user record.
        Scoped to school_id for tenant safety.
        Returns True if successful.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.id == user_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            user.is_deleted = True
            user.deleted_at = now
            db.flush()
            return True
        return False

    def restore(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Restore soft-deleted user record.
        Scoped to school_id.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == user_id,
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            user.is_deleted = False
            user.deleted_at = None
            db.flush()
            return True
        return False

    # -----------------------------------------
    # Bulk Operations (Atomic, Whitelisted)
    # -----------------------------------------

    def bulk_activate(
        self,
        db: Session,
        school_id: UUID,
        user_ids: List[UUID]
    ) -> int:
        """
        Bulk activate users.
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not user_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(user_ids),
                self.model.is_deleted.is_(False)
            )
            .values(is_active=True)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_deactivate(
        self,
        db: Session,
        school_id: UUID,
        user_ids: List[UUID]
    ) -> int:
        """
        Bulk deactivate users.
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not user_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(user_ids),
                self.model.is_deleted.is_(False)
            )
            .values(is_active=False)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_last_login(
        self,
        db: Session,
        school_id: UUID,
        user_ids: List[UUID],
        last_login: datetime
    ) -> int:
        """
        Bulk update last_login timestamp.
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Excludes soft-deleted records explicitly.
        Returns count of updated rows.
        """
        if not user_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(user_ids),
                self.model.is_deleted.is_(False)
            )
            .values(last_login=last_login)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0