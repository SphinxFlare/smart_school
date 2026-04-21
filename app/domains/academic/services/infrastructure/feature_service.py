# academic/services/infrastructure/feature_service.py

from uuid import UUID
from sqlalchemy.orm import Session

from academic.models.infrastructure import SchoolFeature
from academic.repositories.infrastructure.feature_repository import SchoolFeatureRepository
from academic.services.common.validator_service import ValidatorService


class FeatureService:

    def __init__(self):
        self.repo = SchoolFeatureRepository()
        self.validator = ValidatorService()

    def set_feature(self, db: Session, *, school_id: UUID, feature_key, is_enabled: bool):
        with db.begin():
            feature = self.repo.get_by_school_and_feature(db, school_id, feature_key)

            if feature:
                feature.is_enabled = is_enabled
                return feature

            obj = SchoolFeature(
                school_id=school_id,
                feature_key=feature_key,
                is_enabled=is_enabled,
            )
            return self.repo.create(db, obj)

    def is_enabled(self, db: Session, *, school_id: UUID, feature_key) -> bool:
        return self.repo.is_feature_enabled(db, school_id, feature_key)

    def list_enabled(self, db: Session, *, school_id: UUID):
        return self.repo.list_enabled_by_school(db, school_id)

    def list_all(self, db: Session, *, school_id: UUID):
        return self.repo.list_all_by_school(db, school_id)