# communication/services/common/audience_filter.py

from typing import List, Optional
from uuid import UUID

from communication.models.broadcast import Announcement


class AudienceFilter:
    """
    Filters announcements based on user context.

    Responsibilities:
    - Apply role, class, section visibility rules
    - Pure in-memory filtering (no DB access)

    Rules:
    - None or empty target fields → no restriction
    - All conditions must pass (AND logic)
    """

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def filter_announcements(
        self,
        announcements: List[Announcement],
        *,
        user_role: Optional[str] = None,
        class_id: Optional[UUID] = None,
        section_id: Optional[UUID] = None,
    ) -> List[Announcement]:

        result: List[Announcement] = []

        for ann in announcements:
            if not self._passes_role(ann, user_role):
                continue

            if not self._passes_class(ann, class_id):
                continue

            if not self._passes_section(ann, section_id):
                continue

            result.append(ann)

        return result

    # ---------------------------------------------------------
    # Role Check
    # ---------------------------------------------------------

    def _passes_role(
        self,
        ann: Announcement,
        user_role: Optional[str]
    ) -> bool:

        if not ann.target_roles:
            return True  # no restriction

        if not user_role:
            return False

        return user_role in ann.target_roles

    # ---------------------------------------------------------
    # Class Check
    # ---------------------------------------------------------

    def _passes_class(
        self,
        ann: Announcement,
        class_id: Optional[UUID]
    ) -> bool:

        if not ann.target_classes:
            return True  # no restriction

        if not class_id:
            return False

        return str(class_id) in ann.target_classes

    # ---------------------------------------------------------
    # Section Check
    # ---------------------------------------------------------

    def _passes_section(
        self,
        ann: Announcement,
        section_id: Optional[UUID]
    ) -> bool:

        if not ann.target_sections:
            return True  # no restriction

        if not section_id:
            return False

        return str(section_id) in ann.target_sections