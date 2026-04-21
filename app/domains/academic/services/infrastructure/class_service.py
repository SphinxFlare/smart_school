# academic/services/infrastructure/class_service.py

from uuid import UUID
from sqlalchemy.orm import Session

from academic.models.infrastructure import Class
from academic.repositories.infrastructure.class_repository import ClassRepository
from academic.repositories.infrastructure.academic_repository import AcademicYearRepository
from academic.services.common.validator_service import ValidatorService, ValidationError


class ClassService:

    def __init__(self):
        self.repo = ClassRepository()
        self.year_repo = AcademicYearRepository()
        self.validator = ValidatorService()

    def create_class(self, db: Session, *, school_id: UUID, name: str, level: int, academic_year_id: UUID):
        self.validator.validate_required_string(name)
        self.validator.validate_positive(level, "level")

        year = self.year_repo.get(db, academic_year_id)
        if not year or year.school_id != school_id:
            raise ValidationError("Academic year not found")

        existing = self.repo.get_by_name_and_school(db, school_id, name, academic_year_id)
        if existing:
            raise ValidationError("Class already exists")

        with db.begin():
            obj = Class(
                school_id=school_id,
                name=name,
                level=level,
                academic_year_id=academic_year_id,
            )
            return self.repo.create(db, obj)

    def get_by_id(self, db: Session, *, school_id: UUID, class_id: UUID):
        cls = self.repo.get(db, class_id)
        if not cls or cls.school_id != school_id:
            raise ValidationError("Class not found")
        return cls

    def list_by_school(self, db: Session, *, school_id: UUID, skip=0, limit=100):
        return self.repo.list_by_school(db, school_id, skip, limit)

    def list_by_year(self, db: Session, *, school_id: UUID, academic_year_id: UUID, skip=0, limit=100):
        return self.repo.list_by_school_and_year(db, school_id, academic_year_id, skip, limit)

    def update_class(self, db: Session, *, school_id: UUID, class_id: UUID, name=None, level=None):
        with db.begin():
            cls = self.repo.get(db, class_id)
            if not cls or cls.school_id != school_id:
                raise ValidationError("Class not found")

            if name:
                self.validator.validate_required_string(name)
                existing = self.repo.get_by_name_and_school(db, school_id, name, cls.academic_year_id)
                if existing and existing.id != class_id:
                    raise ValidationError("Duplicate class name")
                cls.name = name

            if level is not None:
                self.validator.validate_positive(level, "level")
                cls.level = level

        return cls

    def delete_class(self, db: Session, *, school_id: UUID, class_id: UUID):
        with db.begin():
            cls = self.repo.get(db, class_id)
            if not cls or cls.school_id != school_id:
                raise ValidationError("Class not found")

            cls.is_deleted = True
        return True