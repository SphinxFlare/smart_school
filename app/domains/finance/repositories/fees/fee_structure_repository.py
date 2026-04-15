# finance/repositories/fees/fee_structure_repository.py


from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from repositories.base import SchoolScopedRepository
from finance.models.fees import FeeStructure


# ==========================================================
# Fee Structure Repository
# ==========================================================

class FeeStructureRepository(SchoolScopedRepository[FeeStructure]):
    """
    Repository for FeeStructure model operations.
    School-scoped persistence layer with soft-delete safety.
    NO business logic, calculations, or student fee generation.
    Strictly a template persistence layer.
    """

    def __init__(self):
        super().__init__(FeeStructure)

    # -----------------------------------------
    # Deterministic Listing by Academic Year
    # -----------------------------------------

    def list_by_academic_year(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeeStructure]:
        """
        List fee structures by academic year.
        Deterministic ordering: academic_year_id, class_id, section_id, id.
        Uses index on academic_year_id.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.academic_year_id == academic_year_id
            )
            .order_by(
                self.model.academic_year_id.asc(),
                self.model.class_id.asc(),
                self.model.section_id.asc().nulls_last(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_class(
        self,
        db: Session,
        school_id: UUID,
        class_id: UUID,
        section_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeeStructure]:
        """
        List fee structures by class with optional section filter.
        Uses composite index on (class_id, section_id).
        Deterministic ordering: academic_year_id, class_id, section_id, id.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.class_id == class_id
        )
        
        if section_id is not None:
            stmt = stmt.where(self.model.section_id == section_id)
        
        stmt = (
            stmt.order_by(
                self.model.academic_year_id.asc(),
                self.model.class_id.asc(),
                self.model.section_id.asc().nulls_last(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Composite Scope Retrieval
    # -----------------------------------------

    def get_by_composite_scope(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID,
        class_id: UUID,
        section_id: Optional[UUID] = None
    ) -> Optional[FeeStructure]:
        """
        Retrieve fee structure by composite scope.
        school_id + academic_year_id + class_id + optional section_id.
        For section_id=None, matches records where section_id IS NULL.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.academic_year_id == academic_year_id,
            self.model.class_id == class_id
        )
        
        if section_id is not None:
            stmt = stmt.where(self.model.section_id == section_id)
        else:
            stmt = stmt.where(self.model.section_id.is_(None))
        
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_id_school_scoped(
        self,
        db: Session,
        school_id: UUID,
        structure_id: UUID
    ) -> Optional[FeeStructure]:
        """
        Retrieve fee structure by id scoped to school.
        Prevents horizontal privilege escalation across tenants.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == structure_id,
                self.model.school_id == school_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Category Filtering
    # -----------------------------------------

    def filter_by_category(
        self,
        db: Session,
        school_id: UUID,
        category_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeeStructure]:
        """
        Filter fee structures by category.
        Deterministic ordering: academic_year_id, class_id, section_id, id.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.category_id == category_id
            )
            .order_by(
                self.model.academic_year_id.asc(),
                self.model.class_id.asc(),
                self.model.section_id.asc().nulls_last(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Publication Status Filtering
    # -----------------------------------------

    def filter_by_is_published(
        self,
        db: Session,
        school_id: UUID,
        is_published: bool,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeeStructure]:
        """
        Filter fee structures by publication status.
        Deterministic ordering: academic_year_id, class_id, section_id, id.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.is_published.is_(is_published)
            )
            .order_by(
                self.model.academic_year_id.asc(),
                self.model.class_id.asc(),
                self.model.section_id.asc().nulls_last(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_published_structures(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeeStructure]:
        """
        List published fee structures (is_published=True).
        Optional academic_year_id filter.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.is_published.is_(True)
        )
        
        if academic_year_id is not None:
            stmt = stmt.where(self.model.academic_year_id == academic_year_id)
        
        stmt = (
            stmt.order_by(
                self.model.academic_year_id.asc(),
                self.model.class_id.asc(),
                self.model.section_id.asc().nulls_last(),
                self.model.id.asc()
            )
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------
    # Row-Level Locking for Updates
    # -----------------------------------------

    def lock_for_update(
        self,
        db: Session,
        school_id: UUID,
        structure_id: UUID
    ) -> Optional[FeeStructure]:
        """
        Lock fee structure for update to prevent concurrent modification conflicts.
        Used for updates or publish toggling.
        Returns locked row or None if not found.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == structure_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_by_composite_scope_for_update(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID,
        class_id: UUID,
        section_id: Optional[UUID] = None
    ) -> Optional[FeeStructure]:
        """
        Lock fee structure by composite scope for update.
        Prevents concurrent modifications to same class/section/year combination.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.academic_year_id == academic_year_id,
            self.model.class_id == class_id
        )
        
        if section_id is not None:
            stmt = stmt.where(self.model.section_id == section_id)
        else:
            stmt = stmt.where(self.model.section_id.is_(None))
        
        stmt = stmt.with_for_update()
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Count Operations (Null-Safe)
    # -----------------------------------------

    def count_by_academic_year(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID
    ) -> int:
        """
        Count fee structures by academic year with null-safe aggregation.
        Excludes soft-deleted records.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.academic_year_id == academic_year_id
            )
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_published(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: Optional[UUID] = None
    ) -> int:
        """
        Count published fee structures with null-safe aggregation.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.is_published.is_(True)
            )
        )
        
        if academic_year_id is not None:
            stmt = stmt.where(self.model.academic_year_id == academic_year_id)
        
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_class(
        self,
        db: Session,
        school_id: UUID,
        class_id: UUID,
        section_id: Optional[UUID] = None
    ) -> int:
        """
        Count fee structures by class with null-safe aggregation.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.class_id == class_id
            )
        )
        
        if section_id is not None:
            stmt = stmt.where(self.model.section_id == section_id)
        
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
        structure_id: UUID
    ) -> bool:
        """
        Soft delete fee structure (toggle is_deleted, set deleted_at).
        NO hard deletes. NO cascading business operations.
        Returns True if successful, False if not found.
        """
        now = datetime.utcnow()
        stmt = (
            select(self.model)
            .where(
                self.model.id == structure_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        structure = result.scalar_one_or_none()

        if structure:
            structure.is_deleted = True
            structure.deleted_at = now
            db.flush()
            return True
        return False

    def restore(
        self,
        db: Session,
        school_id: UUID,
        structure_id: UUID
    ) -> bool:
        """
        Restore soft-deleted fee structure.
        Returns True if successful, False if not found.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == structure_id,
                self.model.school_id == school_id,
                self.model.is_deleted.is_(True)
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        structure = result.scalar_one_or_none()

        if structure:
            structure.is_deleted = False
            structure.deleted_at = None
            db.flush()
            return True
        return False

    # -----------------------------------------
    # Publication Toggle (Row-Locked)
    # -----------------------------------------

    def toggle_publication(
        self,
        db: Session,
        school_id: UUID,
        structure_id: UUID,
        publish: bool
    ) -> Optional[FeeStructure]:
        """
        Toggle publication status with row locking.
        Idempotent and concurrency-safe.
        NO validation of publication rules (service layer responsibility).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == structure_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = db.execute(stmt)
        structure = result.scalar_one_or_none()

        if structure:
            structure.is_published = publish
            db.flush()
            return structure
        return None

    # -----------------------------------------
    # Bulk Operations (Index-Aware)
    # -----------------------------------------

    def bulk_update_due_dates(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID,
        new_due_date: datetime
    ) -> int:
        """
        Bulk update due dates for fee structures in an academic year.
        Returns count of updated rows.
        Index-friendly filtering on academic_year_id.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.academic_year_id == academic_year_id,
                self.model.is_deleted.is_(False)
            )
            .values(due_date=new_due_date)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_toggle_publication(
        self,
        db: Session,
        school_id: UUID,
        structure_ids: List[UUID],
        publish: bool
    ) -> int:
        """
        Bulk toggle publication status for multiple structures.
        Returns count of updated rows.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(structure_ids),
                self.model.is_deleted.is_(False)
            )
            .values(is_published=publish)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0