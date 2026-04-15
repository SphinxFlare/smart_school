# finance/repositories/fees/fee_category_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import JSONB

from repositories.base import SchoolScopedRepository
from finance.models.fees import FeeCategory


# ==========================================================
# Fee Category Repository
# ==========================================================

class FeeCategoryRepository(SchoolScopedRepository[FeeCategory]):
    """
    Repository for FeeCategory model operations.
    School-scoped persistence layer with soft-delete safety.
    NO business logic, validation, or financial calculations.
    """

    def __init__(self):
        super().__init__(FeeCategory)

    # -----------------------------------------
    # Active Category Listing
    # -----------------------------------------

    def list_active_categories(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeeCategory]:
        """
        List active categories (is_active=True) per school.
        Excludes soft-deleted records automatically.
        Deterministic ordering: created_at DESC, id DESC.
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

    def list_all_categories(
        self,
        db: Session,
        school_id: UUID,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeeCategory]:
        """
        List all categories per school (optionally include inactive).
        Excludes soft-deleted records automatically.
        Deterministic ordering: created_at DESC, id DESC.
        """
        stmt = select(self.model).where(self.model.school_id == school_id)
        
        if not include_inactive:
            stmt = stmt.where(self.model.is_active.is_(True))
        
        stmt = (
            stmt.order_by(
                self.model.created_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Type Filtering
    # -----------------------------------------

    def filter_by_type(
        self,
        db: Session,
        school_id: UUID,
        fee_type: Any,  # FeeType enum value
        skip: int = 0,
        limit: int = 100
    ) -> List[FeeCategory]:
        """
        Filter categories by enum type.
        Uses index on type column.
        NO enum semantics validation (service layer responsibility).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.type == fee_type
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

    def filter_by_is_school_defined(
        self,
        db: Session,
        school_id: UUID,
        is_school_defined: bool,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeeCategory]:
        """
        Filter categories by is_school_defined flag.
        Deterministic ordering: created_at DESC, id DESC.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.is_school_defined.is_(is_school_defined)
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

    # -----------------------------------------
    # Uniqueness & Existence Checks
    # -----------------------------------------

    def get_by_school_and_name(
        self,
        db: Session,
        school_id: UUID,
        name: str
    ) -> Optional[FeeCategory]:
        """
        Retrieve category by composite uniqueness intent (school + name).
        NO business validation enforced here (service layer responsibility).
        Case-sensitive matching unless database collation dictates otherwise.
        Soft-delete safe lookup.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.name == name
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def exists_by_school_and_name(
        self,
        db: Session,
        school_id: UUID,
        name: str,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for duplicate category names within a school.
        Used for uniqueness validation in service layer.
        Optional exclude_id for update operations.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.school_id == school_id,
            self.model.name == name
        )
        
        if exclude_id:
            stmt = stmt.where(self.model.id != exclude_id)
        
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        count = result.scalar() or 0
        return count > 0

    def get_by_id_school_scoped(
        self,
        db: Session,
        school_id: UUID,
        category_id: UUID
    ) -> Optional[FeeCategory]:
        """
        Soft-delete safe lookup by id scoped to school.
        Prevents horizontal privilege escalation across tenants.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == category_id,
                self.model.school_id == school_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # JSONB Custom Type Filtering
    # -----------------------------------------

    def filter_by_custom_type(
        self,
        db: Session,
        school_id: UUID,
        custom_type_filter: Dict[str, Any],
        skip: int = 0,
        limit: int = 100
    ) -> List[FeeCategory]:
        """
        Filter categories by custom_type JSONB containment.
        Uses @> operator for JSONB containment without casting.
        NO validation logic embedded (service layer responsibility).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.custom_type.cast(JSONB).contains(custom_type_filter)
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

    # -----------------------------------------
    # Count Operations (Null-Safe)
    # -----------------------------------------

    def count_active(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count active categories with null-safe aggregation.
        Excludes soft-deleted records.
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

    def count_by_type(
        self,
        db: Session,
        school_id: UUID,
        fee_type: Any
    ) -> int:
        """
        Count categories by type with null-safe aggregation.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.type == fee_type
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # Soft Delete Operations
    # -----------------------------------------

    def soft_delete(
        self,
        db: Session,
        school_id: UUID,
        category_id: UUID
    ) -> bool:
        """
        Soft delete category (toggle is_deleted, set deleted_at).
        NO hard deletes. NO "cannot delete if used" validation.
        Returns True if successful, False if not found.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.id == category_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        category = result.scalar_one_or_none()

        if category:
            category.is_deleted = True
            category.deleted_at = now
            db.flush()
            return True
        return False

    def restore(
        self,
        db: Session,
        school_id: UUID,
        category_id: UUID
    ) -> bool:
        """
        Restore soft-deleted category.
        Returns True if successful, False if not found.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == category_id,
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        category = result.scalar_one_or_none()

        if category:
            category.is_deleted = False
            category.deleted_at = None
            db.flush()
            return True
        return False
