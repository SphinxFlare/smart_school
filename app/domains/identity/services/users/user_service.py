# identity/services/users/user_service.py


from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from identity.models.accounts import User
from identity.repositories.accounts.user_repository import UserRepository


class UserService:
    """
    Service for User management.

    Responsibilities:
    - Create user
    - Update user details
    - Activate / deactivate
    - Soft delete / restore
    - Change password
    - Update last login
    - Enforce uniqueness (email, phone)

    Constraints:
    - No direct SQL
    - No transaction commit
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = UserRepository()

    # ---------------------------------------------------------------------
    # Create
    # ---------------------------------------------------------------------

    def create_user(
        self,
        school_id: UUID,
        email: str,
        password_hash: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
        date_of_birth: Optional[datetime] = None,
    ) -> User:
        """
        Create a new user.

        Ensures:
        - Email is unique within school
        - Phone (if provided) is unique
        """

        if self.repository.exists_by_email(self.db, school_id, email):
            raise ValueError("Email already exists")

        if phone and self.repository.exists_by_phone(self.db, school_id, phone):
            raise ValueError("Phone already exists")

        user = User(
            school_id=school_id,
            email=email,
            phone=phone,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            is_active=True,
        )

        return self.repository.create(self.db, user)

    # ---------------------------------------------------------------------
    # Update
    # ---------------------------------------------------------------------

    def update_user(
        self,
        school_id: UUID,
        user_id: UUID,
        update_data: dict
    ) -> User:
        """
        Update user fields (safe fields only).
        """

        user = self.repository.get_by_id(self.db, school_id, user_id)

        if not user:
            raise ValueError("User not found")

        # Prevent immutable / restricted fields
        restricted_fields = {
            "id", "school_id", "password_hash",
            "created_at", "deleted_at"
        }

        for key, value in update_data.items():
            if hasattr(user, key) and key not in restricted_fields:
                setattr(user, key, value)

        user.updated_at = datetime.utcnow()

        self.db.flush()
        return user

    # ---------------------------------------------------------------------
    # Activation
    # ---------------------------------------------------------------------

    def activate_user(
        self,
        school_id: UUID,
        user_id: UUID
    ) -> User:
        user = self.repository.get_locked_for_update(self.db, school_id, user_id)

        if not user:
            raise ValueError("User not found")

        user.is_active = True
        self.db.flush()
        return user

    def deactivate_user(
        self,
        school_id: UUID,
        user_id: UUID
    ) -> User:
        user = self.repository.get_locked_for_update(self.db, school_id, user_id)

        if not user:
            raise ValueError("User not found")

        user.is_active = False
        self.db.flush()
        return user

    # ---------------------------------------------------------------------
    # Soft Delete / Restore
    # ---------------------------------------------------------------------

    def delete_user(
        self,
        school_id: UUID,
        user_id: UUID
    ) -> None:
        user = self.repository.get_locked_for_update(self.db, school_id, user_id)

        if not user:
            raise ValueError("User not found")

        user.is_deleted = True
        user.deleted_at = datetime.utcnow()

        self.db.flush()

    def restore_user(
        self,
        school_id: UUID,
        user_id: UUID
    ) -> User:
        user = self.repository.get_by_id(self.db, school_id, user_id)

        if not user:
            raise ValueError("User not found")

        user.is_deleted = False
        user.deleted_at = None

        self.db.flush()
        return user

    # ---------------------------------------------------------------------
    # Password
    # ---------------------------------------------------------------------

    def change_password(
        self,
        school_id: UUID,
        user_id: UUID,
        new_password_hash: str
    ) -> User:
        """
        Change user password (locked).
        """

        user = self.repository.lock_for_password_change(
            self.db,
            school_id,
            user_id
        )

        if not user:
            raise ValueError("User not found")

        user.password_hash = new_password_hash
        user.updated_at = datetime.utcnow()

        self.db.flush()
        return user

    # ---------------------------------------------------------------------
    # Login tracking
    # ---------------------------------------------------------------------

    def update_last_login(
        self,
        school_id: UUID,
        user_id: UUID
    ) -> None:
        user = self.repository.get_by_id(self.db, school_id, user_id)

        if not user:
            return

        user.last_login = datetime.utcnow()
        self.db.flush()

    # ---------------------------------------------------------------------
    # Get
    # ---------------------------------------------------------------------

    def get_user(
        self,
        school_id: UUID,
        user_id: UUID
    ) -> Optional[User]:
        return self.repository.get_by_id(self.db, school_id, user_id)

    def get_by_email(
        self,
        school_id: UUID,
        email: str
    ) -> Optional[User]:
        return self.repository.get_by_email(self.db, school_id, email)

    # ---------------------------------------------------------------------
    # List
    # ---------------------------------------------------------------------

    def list_users(
        self,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        is_deleted: Optional[bool] = False
    ) -> List[User]:

        if is_deleted:
            return self.repository.list_deleted(self.db, school_id, skip, limit)

        if is_active is True:
            return self.repository.list_active(self.db, school_id, skip, limit)

        if is_active is False:
            return self.repository.list_inactive(self.db, school_id, skip, limit)

        return self.repository.list_by_school(self.db, school_id, skip, limit)