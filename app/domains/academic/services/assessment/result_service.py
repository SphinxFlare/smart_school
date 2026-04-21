# academic/services/assessment/result_service.py

from uuid import UUID
from sqlalchemy.orm import Session

from academic.models.assessment import StudentResult
from academic.repositories.assessment.result_repository import StudentResultRepository


class ResultService:

    def __init__(self):
        self.repo = StudentResultRepository()

    def create_result(self, db: Session, *, student_id: UUID, exam_id: UUID, total_marks: float, percentage: float):
        with db.begin():
            obj = StudentResult(
                student_id=student_id,
                exam_id=exam_id,
                total_marks=total_marks,
                percentage=percentage,
            )
            return self.repo.create(db, obj)