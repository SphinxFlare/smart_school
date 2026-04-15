# identity/repositories/accounts/role_repository.py 


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from repositories.base import SchoolScopedRepository
from identity.models.accounts import Role


class RoleRepository(SchoolScopedRepository[Role]):
    """
    Repository for Role model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation at database level.
    NOTE: Role model does NOT have is_deleted, so no soft-delete filtering.
    Zero permission evaluation logic, zero authorization decisions.
    """

    def __init__(self):
        super().__init__(Role)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        school_id: UUID,
        role_id: UUID
    ) -> Optional[Role]:
        """
        Retrieve role by ID scoped to school.
        Prevents horizontal privilege escalation.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == role_id,
                self.model.school_id == school_id
            )
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Composite Uniqueness Lookups
    # -----------------------------------------

    def get_by_name(
        self,
        db: Session,
        school_id: UUID,
        name: Any  # UserRoleType enum
    ) -> Optional[Role]:
        """
        Retrieve role by name scoped to school.
        Respects unique constraint (school_id, name).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.name == name
            )
        )
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
    ) -> List[Role]:
        """
        List all roles within school tenant.
        Deterministic ordering: created_at DESC, id DESC.
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
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_names(
        self,
        db: Session,
        school_id: UUID,
        names: List[Any],  # List of UserRoleType enums
        skip: int = 0,
        limit: int = 100
    ) -> List[Role]:
        """
        List roles by specific names within school tenant.
        Empty-list guard included.
        Deterministic ordering: created_at DESC, id DESC.
        """
        if not names:
            return []

        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.name.in_(names)
            )
            .order_by(
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
        school_id: UUID,
        role_id: UUID
    ) -> Optional[Role]:
        """
        Lock role for update.
        Scoped to school_id for tenant safety.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == role_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_by_name_for_update(
        self,
        db: Session,
        school_id: UUID,
        name: Any  # UserRoleType enum
    ) -> Optional[Role]:
        """
        Lock role by name for update.
        Tenant-safe locking.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.name == name
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Existence Checks
    # -----------------------------------------

    def exists_by_id(
        self,
        db: Session,
        school_id: UUID,
        role_id: UUID
    ) -> bool:
        """
        Efficient existence check for role by ID.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.id == role_id,
                self.model.school_id == school_id
            )
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_name(
        self,
        db: Session,
        school_id: UUID,
        name: Any,  # UserRoleType enum
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Existence check for role name within school.
        Respects unique constraint (school_id, name).
        Optional exclude_id for update operations.
        """
        stmt = select(func.count(self.model.id)).where(
            self.model.school_id == school_id,
            self.model.name == name
        )
        
        if exclude_id is not None:
            stmt = stmt.where(self.model.id != exclude_id)
        
        result = db.execute(stmt)
        count = result.scalar() or 0
        return count > 0

    # -----------------------------------------
    # Aggregations (Null-Safe)
    # -----------------------------------------

    def count_by_school(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count roles within school.
        Null-safe aggregation.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.school_id == school_id)
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_name(
        self,
        db: Session,
        school_id: UUID,
        name: Any  # UserRoleType enum
    ) -> int:
        """
        Count roles by name within school.
        Null-safe aggregation.
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.school_id == school_id,
                self.model.name == name
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # Update Operations (Whitelisted Fields)
    # -----------------------------------------

    def update_role(
        self,
        db: Session,
        school_id: UUID,
        role_id: UUID,
        description: Optional[str] = None,
        permissions: Optional[str] = None
    ) -> Optional[Role]:
        """
        Update role with whitelisted mutable fields only.
        Prevents mutation of identifiers, school_id, or name enum.
        Returns updated role or None if not found.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.id == role_id,
                self.model.school_id == school_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        role = result.scalar_one_or_none()

        if role:
            if description is not None:
                role.description = description
            if permissions is not None:
                role.permissions = permissions
            db.flush()
            return role
        return None

    # -----------------------------------------
    # Bulk Operations (Atomic)
    # -----------------------------------------

    def bulk_update_permissions(
        self,
        db: Session,
        school_id: UUID,
        role_ids: List[UUID],
        permissions: str
    ) -> int:
        """
        Bulk update permissions for multiple roles.
        Atomic update statement scoped by school_id.
        Empty-list guard included.
        Whitelists only 'permissions' field.
        Returns count of updated rows.
        """
        if not role_ids:
            return 0

        stmt = (
            update(self.model)
            .where(
                self.model.school_id == school_id,
                self.model.id.in_(role_ids)
            )
            .values(permissions=permissions)
        )
        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_update_descriptions(
        self,
        db: Session,
        school_id: UUID,
        role_updates: List[Dict[str, Any]]
    ) -> int:
        """
        Bulk update descriptions for multiple roles.
        role_updates: List of {'id': UUID, 'description': str}
        Atomic update statements scoped by school_id.
        Empty-list guard included.
        Returns count of updated rows.
        """
        if not role_updates:
            return 0

        updated_count = 0
        for update_data in role_updates:
            role_id = update_data.get('id')
            description = update_data.get('description')
            
            if role_id is not None and description is not None:
                stmt = (
                    update(self.model)
                    .where(
                        self.model.school_id == school_id,
                        self.model.id == role_id
                    )
                    .values(description=description)
                )
                result = db.execute(stmt)
                updated_count += result.rowcount or 0

        db.flush()
        return updated_count