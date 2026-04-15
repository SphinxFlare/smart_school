# identity/repositories/accounts/user_role_repository.py


from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, func, update, and_

from repositories.base import SchoolScopedRepository
from identity.models.accounts import UserRole, User, Role


class UserRoleRepository(SchoolScopedRepository[UserRole]):
    """
    Repository for UserRole model operations.
    Extends SchoolScopedRepository - ALL queries MUST include school_id.
    Enforces hard tenant isolation via explicit joins with User and Role.
    Ensures user.school_id and role.school_id match provided school_id.
    NOTE: UserRole model does NOT have is_deleted, so no soft-delete filtering.
    Zero authorization decisions, zero permission evaluation logic.
    """

    def __init__(self):
        super().__init__(UserRole)

    # -----------------------------------------
    # Retrieval by ID
    # -----------------------------------------

    def get_by_id(
        self,
        db: Session,
        school_id: UUID,
        user_role_id: UUID
    ) -> Optional[UserRole]:
        """
        Retrieve user role assignment by ID scoped to school.
        Joins with User to verify tenant isolation.
        """
        user_alias = aliased(User)
        stmt = (
            select(self.model)
            .join(user_alias, self.model.user_id == user_alias.id)
            .where(
                self.model.id == user_role_id,
                user_alias.school_id == school_id
            )
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------------------------
    # Listing Methods
    # -----------------------------------------

    def list_by_user(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserRole]:
        """
        List role assignments for a user within school tenant.
        Joins with User to verify tenant isolation.
        Deterministic ordering: assigned_at DESC, id DESC.
        """
        user_alias = aliased(User)
        stmt = (
            select(self.model)
            .join(user_alias, self.model.user_id == user_alias.id)
            .where(
                self.model.user_id == user_id,
                user_alias.school_id == school_id
            )
            .order_by(
                self.model.assigned_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_role(
        self,
        db: Session,
        school_id: UUID,
        role_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserRole]:
        """
        List user assignments for a role within school tenant.
        Joins with Role to verify tenant isolation.
        Deterministic ordering: assigned_at DESC, id DESC.
        """
        role_alias = aliased(Role)
        stmt = (
            select(self.model)
            .join(role_alias, self.model.role_id == role_alias.id)
            .where(
                self.model.role_id == role_id,
                role_alias.school_id == school_id
            )
            .order_by(
                self.model.assigned_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_active_assignments(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserRole]:
        """
        List active role assignments for a user within school tenant.
        Joins with User to verify tenant isolation.
        Deterministic ordering: assigned_at DESC, id DESC.
        """
        user_alias = aliased(User)
        stmt = (
            select(self.model)
            .join(user_alias, self.model.user_id == user_alias.id)
            .where(
                self.model.user_id == user_id,
                user_alias.school_id == school_id,
                self.model.is_active.is_(True)
            )
            .order_by(
                self.model.assigned_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_inactive_assignments(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserRole]:
        """
        List inactive role assignments for a user within school tenant.
        Joins with User to verify tenant isolation.
        Deterministic ordering: assigned_at DESC, id DESC.
        """
        user_alias = aliased(User)
        stmt = (
            select(self.model)
            .join(user_alias, self.model.user_id == user_alias.id)
            .where(
                self.model.user_id == user_id,
                user_alias.school_id == school_id,
                self.model.is_active.is_(False)
            )
            .order_by(
                self.model.assigned_at.desc(),
                self.model.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_school_wide(
        self,
        db: Session,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserRole]:
        """
        List all role assignments within school tenant.
        Joins with User to verify tenant isolation.
        Deterministic ordering: assigned_at DESC, id DESC.
        """
        user_alias = aliased(User)
        stmt = (
            select(self.model)
            .join(user_alias, self.model.user_id == user_alias.id)
            .where(user_alias.school_id == school_id)
            .order_by(
                self.model.assigned_at.desc(),
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
        user_role_id: UUID
    ) -> Optional[UserRole]:
        """
        Lock user role assignment for update.
        Joins with User to verify tenant isolation.
        """
        user_alias = aliased(User)
        stmt = (
            select(self.model)
            .join(user_alias, self.model.user_id == user_alias.id)
            .where(
                self.model.id == user_role_id,
                user_alias.school_id == school_id
            )
            .with_for_update()
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def lock_by_user_and_role_for_update(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID,
        role_id: UUID
    ) -> Optional[UserRole]:
        """
        Lock user role assignment by user and role for update.
        Joins with User and Role to verify tenant isolation.
        """
        user_alias = aliased(User)
        role_alias = aliased(Role)
        stmt = (
            select(self.model)
            .join(user_alias, self.model.user_id == user_alias.id)
            .join(role_alias, self.model.role_id == role_alias.id)
            .where(
                self.model.user_id == user_id,
                self.model.role_id == role_id,
                user_alias.school_id == school_id,
                role_alias.school_id == school_id
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
        user_role_id: UUID
    ) -> bool:
        """
        Efficient existence check for user role by ID.
        Joins with User to verify tenant isolation.
        """
        user_alias = aliased(User)
        stmt = (
            select(self.model.id)
            .join(user_alias, self.model.user_id == user_alias.id)
            .where(
                self.model.id == user_role_id,
                user_alias.school_id == school_id
            )
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_assignment(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID,
        role_id: UUID,
        active_only: bool = False
    ) -> bool:
        """
        Existence check for user-role assignment within school.
        Joins with User and Role to verify tenant isolation.
        Optional active_only filter.
        """
        user_alias = aliased(User)
        role_alias = aliased(Role)
        stmt = select(func.count(self.model.id)).join(
            user_alias, self.model.user_id == user_alias.id
        ).join(
            role_alias, self.model.role_id == role_alias.id
        ).where(
            self.model.user_id == user_id,
            self.model.role_id == role_id,
            user_alias.school_id == school_id,
            role_alias.school_id == school_id
        )
        
        if active_only:
            stmt = stmt.where(self.model.is_active.is_(True))
        
        result = db.execute(stmt)
        count = result.scalar() or 0
        return count > 0

    def exists_active_assignment(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID,
        role_id: UUID
    ) -> bool:
        """
        Efficient existence check for active user-role assignment.
        Joins with User and Role to verify tenant isolation.
        """
        return self.exists_assignment(db, school_id, user_id, role_id, active_only=True)

    # -----------------------------------------
    # Aggregations (Null-Safe)
    # -----------------------------------------

    def count_by_user(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID,
        active_only: bool = False
    ) -> int:
        """
        Count role assignments for a user within school.
        Joins with User to verify tenant isolation.
        Null-safe aggregation.
        """
        user_alias = aliased(User)
        stmt = select(func.count(self.model.id)).join(
            user_alias, self.model.user_id == user_alias.id
        ).where(
            self.model.user_id == user_id,
            user_alias.school_id == school_id
        )
        
        if active_only:
            stmt = stmt.where(self.model.is_active.is_(True))
        
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_by_role(
        self,
        db: Session,
        school_id: UUID,
        role_id: UUID,
        active_only: bool = False
    ) -> int:
        """
        Count user assignments for a role within school.
        Joins with Role to verify tenant isolation.
        Null-safe aggregation.
        """
        role_alias = aliased(Role)
        stmt = select(func.count(self.model.id)).join(
            role_alias, self.model.role_id == role_alias.id
        ).where(
            self.model.role_id == role_id,
            role_alias.school_id == school_id
        )
        
        if active_only:
            stmt = stmt.where(self.model.is_active.is_(True))
        
        result = db.execute(stmt)
        return result.scalar() or 0

    def count_active_school_wide(
        self,
        db: Session,
        school_id: UUID
    ) -> int:
        """
        Count active role assignments across school.
        Joins with User to verify tenant isolation.
        Null-safe aggregation.
        """
        user_alias = aliased(User)
        stmt = (
            select(func.count(self.model.id))
            .join(user_alias, self.model.user_id == user_alias.id)
            .where(
                user_alias.school_id == school_id,
                self.model.is_active.is_(True)
            )
        )
        result = db.execute(stmt)
        return result.scalar() or 0

    # -----------------------------------------
    # Assignment Operations
    # -----------------------------------------

    def assign_role(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID,
        role_id: UUID
    ) -> UserRole:
        """
        Assign role to user.
        Verifies tenant isolation via User and Role joins.
        Creates new assignment or reactivates existing one.
        """
        # Check if assignment exists
        existing = self.lock_by_user_and_role_for_update(
            db, school_id, user_id, role_id
        )

        if existing:
            existing.is_active = True
            db.flush()
            return existing
        else:
            # Create new assignment
            user_role = UserRole(
                user_id=user_id,
                role_id=role_id,
                is_active=True
            )
            db.add(user_role)
            db.flush()
            return user_role

    def revoke_role(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID,
        role_id: UUID
    ) -> bool:
        """
        Revoke role from user (sets is_active=False).
        Verifies tenant isolation via User and Role joins.
        Returns True if successful.
        """
        user_role = self.lock_by_user_and_role_for_update(
            db, school_id, user_id, role_id
        )

        if user_role and user_role.is_active:
            user_role.is_active = False
            db.flush()
            return True
        return False

    # -----------------------------------------
    # Bulk Operations (Atomic, Empty Guards)
    # -----------------------------------------

    def bulk_activate_assignments(
        self,
        db: Session,
        school_id: UUID,
        user_role_ids: List[UUID]
    ) -> int:
        """
        Bulk activate role assignments.
        Atomic update statement with tenant verification via subquery.
        Empty-list guard included.
        Returns count of updated rows.
        """
        if not user_role_ids:
            return 0

        # subquery to enforce tenant isolation
        subquery = (
            select(UserRole.id)
            .join(User, UserRole.user_id == User.id)
            .where(
                UserRole.id.in_(user_role_ids),
                User.school_id == school_id
            )
        )

        stmt = (
            update(self.model)
            .where(self.model.id.in_(subquery))
            .values(is_active=True)
        )

        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0


    def bulk_deactivate_assignments(
        self,
        db: Session,
        school_id: UUID,
        user_role_ids: List[UUID]
    ) -> int:
        """
        Bulk deactivate role assignments.
        Atomic update statement with tenant verification via subquery.
        Empty-list guard included.
        Returns count of updated rows.
        """
        if not user_role_ids:
            return 0

        subquery = (
            select(UserRole.id)
            .join(User, UserRole.user_id == User.id)
            .where(
                UserRole.id.in_(user_role_ids),
                User.school_id == school_id
            )
        )

        stmt = (
            update(self.model)
            .where(self.model.id.in_(subquery))
            .values(is_active=False)
        )

        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_deactivate_by_user(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID
    ) -> int:
        """
        Bulk deactivate all role assignments for a user.
        Atomic update statement with tenant verification.
        Returns count of updated rows.
        """
        subquery = (
            select(UserRole.id)
            .join(User, UserRole.user_id == User.id)
            .where(
                UserRole.user_id == user_id,
                User.school_id == school_id,
                UserRole.is_active.is_(True)
            )
        )

        stmt = (
            update(self.model)
            .where(self.model.id.in_(subquery))
            .values(is_active=False)
        )

        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0

    def bulk_deactivate_by_role(
        self,
        db: Session,
        school_id: UUID,
        role_id: UUID
    ) -> int:
        """
        Bulk deactivate all user assignments for a role.
        Atomic update statement with tenant verification.
        Returns count of updated rows.
        """
        subquery = (
            select(UserRole.id)
            .join(Role, UserRole.role_id == Role.id)
            .where(
                UserRole.role_id == role_id,
                Role.school_id == school_id,
                UserRole.is_active.is_(True)
            )
        )

        stmt = (
            update(self.model)
            .where(self.model.id.in_(subquery))
            .values(is_active=False)
        )

        result = db.execute(stmt)
        db.flush()
        return result.rowcount or 0