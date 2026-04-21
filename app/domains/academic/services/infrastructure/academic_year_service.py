# academic/services/infrastructure/academic_year_service.py

from uuid import UUID
from sqlalchemy.orm import Session

from academic.models.infrastructure import AcademicYear
from academic.repositories.infrastructure.academic_repository import AcademicYearRepository
from academic.services.common.validator_service import ValidatorService, ValidationError


class AcademicYearService:

    def __init__(self):
        self.repo = AcademicYearRepository()
        self.validator = ValidatorService()

    def create_academic_year(self, db: Session, *, school_id: UUID, name: str, start_date, end_date, is_current: bool = False):
        self.validator.validate_required_string(name, "name")
        self.validator.validate_date_range(start_date, end_date, allow_equal=False)

        existing = self.repo.get_by_name_and_school(db, school_id, name)
        if existing:
            raise ValidationError("Academic year already exists")

        with db.begin():
            if is_current:
                current = self.repo.get_current_by_school(db, school_id)
                if current:
                    current.is_current = False

            obj = AcademicYear(
                school_id=school_id,
                name=name,
                start_date=start_date,
                end_date=end_date,
                is_current=is_current,
            )

            return self.repo.create(db, obj)

    def set_current_year(self, db: Session, *, school_id: UUID, academic_year_id: UUID):
        with db.begin():
            year = self.repo.get(db, academic_year_id)
            if not year or year.school_id != school_id:
                raise ValidationError("Academic year not found")

            current = self.repo.get_current_by_school(db, school_id)
            if current and current.id != year.id:
                current.is_current = False

            year.is_current = True
            return year

    def list_academic_years(self, db: Session, *, school_id: UUID, skip=0, limit=100):
        return self.repo.list_by_school(db, school_id, skip, limit)

    def get_by_id(self, db: Session, *, school_id: UUID, academic_year_id: UUID):
        year = self.repo.get(db, academic_year_id)
        if not year or year.school_id != school_id:
            raise ValidationError("Academic year not found")
        return year

    def delete_academic_year(self, db: Session, *, school_id: UUID, academic_year_id: UUID):
        with db.begin():
            year = self.repo.get(db, academic_year_id)
            if not year or year.school_id != school_id:
                raise ValidationError("Academic year not found")

            if year.is_current:
                raise ValidationError("Cannot delete current academic year")

            year.is_deleted = True
        return True