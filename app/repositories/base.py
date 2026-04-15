# repositories/base.py

from typing import Type, TypeVar, Generic, Optional, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):

    def __init__(self, model: Type[T]):
        self.model = model

    # -----------------------------------------
    # Internal Helper
    # -----------------------------------------

    def _apply_soft_delete_filter(self, stmt):
        """Automatically exclude soft-deleted rows if model supports it."""
        if hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted.is_(False))
        return stmt

    # -----------------------------------------
    # CRUD Methods
    # -----------------------------------------

    def get(self, db: Session, id: UUID) -> Optional[T]:
        stmt = select(self.model).where(self.model.id == id)
        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def create(self, db: Session, obj: T) -> T:
        db.add(obj)
        db.flush()  # Transaction controlled by service layer
        return obj

    def delete(self, db: Session, db_obj: T) -> None:
        """
        Soft delete if model supports it,
        otherwise perform hard delete.
        """
        if hasattr(db_obj, "is_deleted"):
            db_obj.is_deleted = True
        else:
            db.delete(db_obj)

        db.flush()


# ==========================================================
# Multi-Tenant Repository (School Scoped)
# ==========================================================

class SchoolScopedRepository(BaseRepository[T]):
    """
    Tenant-aware repository.
    Only use for models that contain school_id column.
    """

    def get_by_school(
        self,
        db: Session,
        id: UUID,
        school_id: UUID
    ) -> Optional[T]:

        stmt = select(self.model).where(
            self.model.id == id,
            self.model.school_id == school_id
        )

        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def list_by_school(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[T]:

        stmt = (
            select(self.model)
            .where(self.model.school_id == school_id)
            .offset(skip)
            .limit(limit)
        )

        stmt = self._apply_soft_delete_filter(stmt)

        result = db.execute(stmt)
        return list(result.scalars().all())
