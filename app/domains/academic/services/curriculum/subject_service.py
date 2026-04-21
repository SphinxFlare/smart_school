# academic/services/curriculum/subject_service.py


from uuid import UUID
from sqlalchemy.orm import Session

from academic.models.curriculum import Subject
from academic.repositories.Curriculum.subject_repository import SubjectRepository
from academic.services.common.validator_service import ValidatorService, ValidationError


class SubjectService:

    def __init__(self):
        self.repo = SubjectRepository()
        self.validator = ValidatorService()

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------
    def create_subject(
        self,
        db: Session,
        *,
        school_id: UUID,
        name: str,
        code: str,
        description: str | None = None
    ):
        self.validator.validate_required_string(name, "name")
        self.validator.validate_required_string(code, "code")

        existing = self.repo.get_by_code(db, school_id, code)
        if existing:
            raise ValidationError("Subject code already exists")

        with db.begin():
            obj = Subject(
                school_id=school_id,
                name=name,
                code=code,
                description=description,
            )
            return self.repo.create(db, obj)

    # ---------------------------------------------------------
    # GET
    # ---------------------------------------------------------
    def get_by_id(self, db: Session, *, school_id: UUID, subject_id: UUID):
        subject = self.repo.get_by_school(db, subject_id, school_id)
        if not subject:
            raise ValidationError("Subject not found")
        return subject

    def list_subjects(self, db: Session, *, school_id: UUID, is_active=None, skip=0, limit=100):
        return self.repo.list_by_school(db, school_id, is_active, skip, limit)

    def list_active(self, db: Session, *, school_id: UUID, skip=0, limit=100):
        return self.repo.list_active_by_school(db, school_id, skip, limit)

    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------
    def update_subject(
        self,
        db: Session,
        *,
        school_id: UUID,
        subject_id: UUID,
        name: str | None = None,
        code: str | None = None,
        description: str | None = None,
        is_active: bool | None = None
    ):
        with db.begin():
            subject = self.repo.get_by_school(db, subject_id, school_id)
            if not subject:
                raise ValidationError("Subject not found")

            if code:
                existing = self.repo.get_by_code(db, school_id, code)
                if existing and existing.id != subject_id:
                    raise ValidationError("Duplicate subject code")
                subject.code = code

            if name:
                self.validator.validate_required_string(name)
                subject.name = name

            if description is not None:
                subject.description = description

            if is_active is not None:
                subject.is_active = is_active

        return subject

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------
    def delete_subject(self, db: Session, *, school_id: UUID, subject_id: UUID):
        with db.begin():
            subject = self.repo.get_by_school(db, subject_id, school_id)
            if not subject:
                raise ValidationError("Subject not found")

            subject.is_deleted = True

        return True