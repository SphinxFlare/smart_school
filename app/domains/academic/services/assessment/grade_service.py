# academic/services/assessment/grade_service.py

from uuid import UUID
from sqlalchemy.orm import Session

from academic.repositories.assessment.grade_repository import GradeScaleRepository


class GradeService:

    def __init__(self):
        self.repo = GradeScaleRepository()

    def get_grade_by_percentage(self, db: Session, *, school_id: UUID, percentage: float):
        return self.repo.get_by_percentage(db, school_id, percentage)

    # def list_grades(self, db: Session, *, school_id: UUID, skip=0, limit=100):
    #     return self.repo.list_by_school(db, school_id, skip, limit)