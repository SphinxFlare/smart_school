# academic/services/common/ownership_service.py

from uuid import UUID
from sqlalchemy.orm import Session

from academic.repositories.infrastructure.class_repository import ClassRepository
from academic.repositories.infrastructure.section_repository import SectionRepository
from academic.repositories.assessment.exam_repository import ExamRepository
from academic.repositories.assessment.schedule_repository import ExamScheduleRepository
from academic.repositories.Curriculum.assignment_repository import TeacherAssignmentRepository
from academic.repositories.homework.homework import HomeworkRepository


class OwnershipError(Exception):
    pass


class OwnershipService:

    def __init__(self):
        self.class_repo = ClassRepository()
        self.section_repo = SectionRepository()
        self.exam_repo = ExamRepository()
        self.schedule_repo = ExamScheduleRepository()
        self.assignment_repo = TeacherAssignmentRepository()
        self.homework_repo = HomeworkRepository()

    def validate_class(self, db: Session, class_id: UUID, school_id: UUID):
        cls = self.class_repo.get(db, class_id)
        if not cls or cls.school_id != school_id:
            raise OwnershipError("Class does not belong to this school")
        return cls

    def validate_section(self, db: Session, section_id: UUID, school_id: UUID):
        section = self.section_repo.get(db, section_id)
        if not section:
            raise OwnershipError("Section not found")

        self.validate_class(db, section.class_id, school_id)
        return section

    def validate_exam(self, db: Session, exam_id: UUID, school_id: UUID):
        exam = self.exam_repo.get_by_school(db, exam_id, school_id)
        if not exam:
            raise OwnershipError("Exam does not belong to this school")
        return exam

    def validate_schedule(self, db: Session, schedule_id: UUID, school_id: UUID):
        schedule = self.schedule_repo.get(db, schedule_id)
        if not schedule:
            raise OwnershipError("Schedule not found")

        self.validate_exam(db, schedule.exam_id, school_id)
        return schedule

    def validate_teacher_assignment(self, db: Session, assignment_id: UUID, school_id: UUID):
        assignment = self.assignment_repo.get(db, assignment_id)
        if not assignment:
            raise OwnershipError("Teacher assignment not found")

        self.validate_class(db, assignment.class_id, school_id)
        return assignment

    def validate_homework(self, db: Session, homework_id: UUID, school_id: UUID):
        homework = self.homework_repo.get_by_id(db, homework_id)
        if not homework:
            raise OwnershipError("Homework not found")

        self.validate_teacher_assignment(db, homework.teacher_assignment_id, school_id)
        return homework