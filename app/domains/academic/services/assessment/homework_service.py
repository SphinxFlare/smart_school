# academic/services/assessment/homework_service.py

from uuid import UUID
from sqlalchemy.orm import Session

from academic.models.assessment import Homework
from academic.repositories.homework.homework import HomeworkRepository
from academic.services.common.ownership_service import OwnershipService


class HomeworkService:

    def __init__(self):
        self.repo = HomeworkRepository()
        self.ownership = OwnershipService()

    def create_homework(self, db: Session, *, school_id: UUID, teacher_assignment_id: UUID, title: str, due_date):
        self.ownership.validate_teacher_assignment(db, teacher_assignment_id, school_id)

        with db.begin():
            obj = Homework(
                teacher_assignment_id=teacher_assignment_id,
                title=title,
                due_date=due_date,
            )
            return self.repo.create(db, obj)

    def get_by_id(self, db: Session, *, school_id: UUID, homework_id: UUID):
        hw = self.ownership.validate_homework(db, homework_id, school_id)
        return hw