# academic/services/assessment/submission_service.py

from uuid import UUID
from sqlalchemy.orm import Session

from academic.models.assessment import HomeworkSubmission
from academic.repositories.homework.homework_submissions import HomeworkSubmissionRepository
from academic.services.common.ownership_service import OwnershipService
from academic.services.common.validator_service import ValidationError


class SubmissionService:

    def __init__(self):
        self.repo = HomeworkSubmissionRepository()
        self.ownership = OwnershipService()

    def submit_homework(self, db: Session, *, school_id: UUID, homework_id: UUID, student_id: UUID):
        self.ownership.validate_homework(db, homework_id, school_id)

        if self.repo.exists_by_homework_and_student(db, homework_id, student_id):
            raise ValidationError("Already submitted")

        with db.begin():
            obj = HomeworkSubmission(
                homework_id=homework_id,
                student_id=student_id,
            )
            return self.repo.create(db, obj)

    def list_submissions(self, db: Session, *, homework_id: UUID, skip=0, limit=100):
        return self.repo.list_by_homework(db, homework_id, skip, limit)