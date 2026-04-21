# academic/services/assessment/rank_service.py

from sqlalchemy.orm import Session

from academic.repositories.assessment.rank_repository import StudentRankRepository


class RankService:

    def __init__(self):
        self.repo = StudentRankRepository()

    def list_ranks(self, db: Session, *, exam_id, class_id):
        return self.repo.list_by_exam_and_class(db, exam_id, class_id)