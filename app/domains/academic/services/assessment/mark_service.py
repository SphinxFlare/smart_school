# academic/services/assessment/mark_service.py

from uuid import UUID
from sqlalchemy.orm import Session

from academic.models.assessment import StudentExamMark
from academic.repositories.assessment.mark_repository import StudentExamMarkRepository
from academic.services.common.validator_service import ValidationError
from academic.services.common.ownership_service import OwnershipService


class MarkService:

    def __init__(self):
        self.repo = StudentExamMarkRepository()
        self.ownership = OwnershipService()

    def assign_mark(self, db: Session, *, school_id: UUID, student_id: UUID, schedule_id: UUID, marks: float):
        schedule = self.ownership.validate_schedule(db, schedule_id, school_id)

        with db.begin():
            mark = self.repo.get_mark_locked(db, student_id, schedule_id)

            if mark:
                mark.marks_obtained = marks
                return mark

            obj = StudentExamMark(
                student_id=student_id,
                exam_schedule_id=schedule.id,
                marks_obtained=marks,
            )
            return self.repo.create(db, obj)