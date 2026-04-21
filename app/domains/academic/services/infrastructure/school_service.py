# academic/services/infrastructure/school_service.py

from sqlalchemy.orm import Session

from academic.models.infrastructure import School
from academic.repositories.infrastructure.school_repository import SchoolRepository
from academic.services.common.validator_service import ValidatorService, ValidationError


class SchoolService:

    def __init__(self):
        self.repo = SchoolRepository()
        self.validator = ValidatorService()

    def get_by_id(self, db: Session, *, school_id):
        school = self.repo.get(db, school_id)
        if not school:
            raise ValidationError("School not found")
        return school

    def get_by_code(self, db: Session, *, code: str):
        self.validator.validate_required_string(code)
        school = self.repo.get_by_code(db, code)
        if not school:
            raise ValidationError("School not found")
        return school

    def list_active(self, db: Session, *, skip=0, limit=100):
        return self.repo.list_active(db, skip, limit)

    def create_school(self, db: Session, *, name: str, code: str, address=None, contact_email=None, contact_phone=None):
        self.validator.validate_required_string(name)
        self.validator.validate_required_string(code)

        existing = self.repo.get_by_code(db, code)
        if existing:
            raise ValidationError("School code exists")

        with db.begin():
            obj = School(
                name=name,
                code=code,
                address=address,
                contact_email=contact_email,
                contact_phone=contact_phone,
            )
            return self.repo.create(db, obj)

    def update_school(self, db: Session, *, school_id, **kwargs):
        with db.begin():
            school = self.repo.get(db, school_id)
            if not school:
                raise ValidationError("School not found")

            for key, value in kwargs.items():
                if value is not None:
                    setattr(school, key, value)

        return school

    def delete_school(self, db: Session, *, school_id):
        with db.begin():
            school = self.repo.get(db, school_id)
            if not school:
                raise ValidationError("School not found")

            school.is_deleted = True
        return True