# academic/services/assessment/schedule_service.py

from uuid import UUID
from sqlalchemy.orm import Session

from academic.models.assessment import ExamSchedule
from academic.repositories.assessment.schedule_repository import ExamScheduleRepository
from academic.services.common.validator_service import ValidationError
from academic.services.common.ownership_service import OwnershipService


class ScheduleService:

    def __init__(self):
        self.repo = ExamScheduleRepository()
        self.ownership = OwnershipService()

    def create_schedule(self, db: Session, *, school_id: UUID, exam_id: UUID, class_id: UUID, subject_id: UUID, exam_date):
        self.ownership.validate_exam(db, exam_id, school_id)
        self.ownership.validate_class(db, class_id, school_id)

        with db.begin():
            obj = ExamSchedule(
                exam_id=exam_id,
                class_id=class_id,
                subject_id=subject_id,
                exam_date=exam_date,
            )
            return self.repo.create(db, obj)

    def get_by_id(self, db: Session, *, school_id: UUID, schedule_id: UUID):
        schedule = self.repo.get(db, schedule_id)
        if not schedule:
            raise ValidationError("Schedule not found")

        self.ownership.validate_exam(db, schedule.exam_id, school_id)
        return schedule