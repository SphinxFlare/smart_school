# academic/services/infrastructure/section_service.py

from uuid import UUID
from sqlalchemy.orm import Session

from academic.models.infrastructure import Section
from academic.repositories.infrastructure.section_repository import SectionRepository
from academic.services.common.validator_service import ValidatorService, ValidationError
from academic.services.common.ownership_service import OwnershipService


class SectionService:

    def __init__(self):
        self.repo = SectionRepository()
        self.validator = ValidatorService()
        self.ownership = OwnershipService()

    def create_section(self, db: Session, *, school_id: UUID, class_id: UUID, name: str, capacity=None):
        self.ownership.validate_class(db, class_id, school_id)
        self.validator.validate_required_string(name)

        if capacity is not None:
            self.validator.validate_positive(capacity, "capacity")

        existing = self.repo.get_by_name_and_class(db, class_id, name)
        if existing:
            raise ValidationError("Section already exists")

        with db.begin():
            obj = Section(class_id=class_id, name=name, capacity=capacity)
            return self.repo.create(db, obj)

    def get_by_id(self, db: Session, *, school_id: UUID, section_id: UUID):
        section = self.repo.get(db, section_id)
        if not section:
            raise ValidationError("Section not found")

        self.ownership.validate_class(db, section.class_id, school_id)
        return section

    def list_by_class(self, db: Session, *, school_id: UUID, class_id: UUID, skip=0, limit=100):
        self.ownership.validate_class(db, class_id, school_id)
        return self.repo.list_by_class(db, class_id, skip, limit)

    def update_section(self, db: Session, *, school_id: UUID, section_id: UUID, name=None, capacity=None):
        with db.begin():
            section = self.repo.get(db, section_id)
            if not section:
                raise ValidationError("Section not found")

            self.ownership.validate_class(db, section.class_id, school_id)

            if name:
                self.validator.validate_required_string(name)
                existing = self.repo.get_by_name_and_class(db, section.class_id, name)
                if existing and existing.id != section_id:
                    raise ValidationError("Duplicate section")
                section.name = name

            if capacity is not None:
                self.validator.validate_positive(capacity, "capacity")
                section.capacity = capacity

        return section

    def delete_section(self, db: Session, *, school_id: UUID, section_id: UUID):
        with db.begin():
            section = self.repo.get(db, section_id)
            if not section:
                raise ValidationError("Section not found")

            self.ownership.validate_class(db, section.class_id, school_id)
            section.is_deleted = True

        return True