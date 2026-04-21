# academic/services/assessment/exam_service.py

from uuid import UUID
from sqlalchemy.orm import Session

from academic.models.assessment import Exam
from academic.repositories.assessment.exam_repository import ExamRepository
from academic.services.common.validator_service import ValidatorService, ValidationError


class ExamService:

    def __init__(self):
        self.repo = ExamRepository()
        self.validator = ValidatorService()

    def create_exam(self, db: Session, *, school_id: UUID, name: str, start_date, end_date):
        self.validator.validate_required_string(name)
        self.validator.validate_date_range(start_date, end_date, allow_equal=False)

        with db.begin():
            obj = Exam(
                school_id=school_id,
                name=name,
                start_date=start_date,
                end_date=end_date,
            )
            return self.repo.create(db, obj)

    def get_by_id(self, db: Session, *, school_id: UUID, exam_id: UUID):
        exam = self.repo.get_by_school(db, exam_id, school_id)
        if not exam:
            raise ValidationError("Exam not found")
        return exam

    def delete_exam(self, db: Session, *, school_id: UUID, exam_id: UUID):
        with db.begin():
            exam = self.repo.get_by_school(db, exam_id, school_id)
            if not exam:
                raise ValidationError("Exam not found")
            exam.is_deleted = True
        return True