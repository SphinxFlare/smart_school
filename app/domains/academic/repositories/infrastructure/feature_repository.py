# repositories/infrastructure/feature_repository.py


from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select

from academic.models.infrastructure import SchoolFeature
from repositories.base import SchoolScopedRepository


# =============================================================================
# SCHOOL FEATURE REPOSITORY
# =============================================================================

class SchoolFeatureRepository(SchoolScopedRepository[SchoolFeature]):
    """
    Repository for SchoolFeature persistence operations.
    
    Extends SchoolScopedRepository to enforce tenant isolation (school_id).
    Note: This model does not have soft-delete fields.
    
    Responsibilities:
    - Check feature enablement status for a school.
    - List all features for a school.
    - Support feature toggle persistence.
    """

    def __init__(self):
        super().__init__(SchoolFeature)

    def get_by_school_and_feature(
        self,
        db: Session,
        school_id: UUID,
        feature_key
    ) -> Optional[SchoolFeature]:
        """
        Retrieve a specific feature configuration for a school.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            feature_key: FeatureKey enum value.
            
        Returns:
            SchoolFeature object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.feature_key == feature_key
        )

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def list_enabled_by_school(
        self,
        db: Session,
        school_id: UUID
    ) -> List[SchoolFeature]:
        """
        List all enabled features for a school.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            
        Returns:
            List of enabled SchoolFeature ORM objects.
        """
        stmt = select(self.model).where(
            self.model.school_id == school_id,
            self.model.is_enabled.is_(True)
        )

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_all_by_school(
        self,
        db: Session,
        school_id: UUID
    ) -> List[SchoolFeature]:
        """
        List all feature configurations for a school (enabled and disabled).
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            
        Returns:
            List of all SchoolFeature ORM objects for the school.
        """
        stmt = select(self.model).where(self.model.school_id == school_id)

        # No soft-delete filter (model does not support it)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def is_feature_enabled(
        self,
        db: Session,
        school_id: UUID,
        feature_key
    ) -> bool:
        """
        Check if a specific feature is enabled for a school.
        
        Returns False if feature record does not exist or is disabled.
        
        Args:
            db: Database session.
            school_id: Tenant identifier (required).
            feature_key: FeatureKey enum value.
            
        Returns:
            Boolean indicating feature enablement status.
        """
        feature = self.get_by_school_and_feature(db, school_id, feature_key)
        return feature is not None and feature.is_enabled