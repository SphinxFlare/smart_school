# communication/services/common/recipient_resolver.py

from typing import List, Optional, Set
from uuid import UUID

from sqlalchemy.orm import Session


class RecipientResolver:
    """
    Resolves various targeting inputs into a final list of user_ids.

    Current Scope:
    - Supports direct user_ids only (dedupe + normalization)

    Future Expansion:
    - roles → users (identity domain)
    - class_ids → students → parents (academic domain)
    - section_ids → similar mapping

    Design Rules:
    - No DB writes
    - No ownership logic
    - No side effects
    - Pure resolution layer
    """

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def resolve(
        self,
        db: Session,
        *,
        user_ids: Optional[List[UUID]] = None,
        roles: Optional[List[str]] = None,
        class_ids: Optional[List[UUID]] = None,
        section_ids: Optional[List[UUID]] = None,
    ) -> List[UUID]:
        """
        Resolve all targeting inputs into final user_ids.

        Current behavior:
        - Only user_ids are resolved
        - Other inputs are placeholders for future integration
        """

        resolved: Set[UUID] = set()

        # -----------------------------------------------------
        # Direct Users
        # -----------------------------------------------------

        if user_ids:
            resolved.update(self._normalize_user_ids(user_ids))

        # -----------------------------------------------------
        # Future: Role-based resolution
        # -----------------------------------------------------
        if roles:
            # Placeholder for identity domain integration
            # Example:
            # users = identity_repo.get_users_by_roles(...)
            # resolved.update(users)
            pass

        # -----------------------------------------------------
        # Future: Class-based resolution
        # -----------------------------------------------------
        if class_ids:
            # Placeholder for academic domain integration
            # Example:
            # students = student_repo.get_by_class_ids(...)
            # parents = map_students_to_parents(students)
            # resolved.update(parents)
            pass

        # -----------------------------------------------------
        # Future: Section-based resolution
        # -----------------------------------------------------
        if section_ids:
            # Placeholder similar to class_ids
            pass

        return list(resolved)

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def _normalize_user_ids(self, user_ids: List[UUID]) -> Set[UUID]:
        """
        Normalize and deduplicate user_ids.

        Handles:
        - duplicates
        - None values
        """

        return {uid for uid in user_ids if uid is not None}