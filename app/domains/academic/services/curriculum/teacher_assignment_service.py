# academic/services/curriculum/teacher_assignment_service.py


from uuid import UUID
from sqlalchemy.orm import Session

from academic.models.curriculum import TeacherAssignment
from academic.repositories.Curriculum.assignment_repository import TeacherAssignmentRepository
from academic.services.common.validator_service import ValidationError
from academic.services.common.ownership_service import OwnershipService


class TeacherAssignmentService:

    def __init__(self):
        self.repo = TeacherAssignmentRepository()
        self.ownership = OwnershipService()

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------
    def create_assignment(
        self,
        db: Session,
        *,
        school_id: UUID,
        staff_member_id: UUID,
        class_id: UUID,
        section_id: UUID,
        subject_id: UUID,
        academic_year_id: UUID,
        is_primary: bool = True
    ):
        # ownership validations
        self.ownership.validate_class(db, class_id, school_id)
        self.ownership.validate_section(db, section_id, school_id)

        existing = self.repo.get_assignment(
            db,
            staff_member_id,
            class_id,
            section_id,
            subject_id,
            academic_year_id
        )
        if existing:
            raise ValidationError("Assignment already exists")

        with db.begin():
            obj = TeacherAssignment(
                staff_member_id=staff_member_id,
                class_id=class_id,
                section_id=section_id,
                subject_id=subject_id,
                academic_year_id=academic_year_id,
                is_primary=is_primary,
            )
            return self.repo.create(db, obj)

    # ---------------------------------------------------------
    # GET
    # ---------------------------------------------------------
    def list_by_staff(self, db: Session, *, staff_member_id: UUID, academic_year_id: UUID, skip=0, limit=100):
        return self.repo.list_by_staff(db, staff_member_id, academic_year_id, skip, limit)

    def list_by_class_section(self, db: Session, *, class_id: UUID, section_id: UUID, academic_year_id: UUID, skip=0, limit=100):
        return self.repo.list_by_class_section(db, class_id, section_id, academic_year_id, skip, limit)

    def list_by_year(self, db: Session, *, academic_year_id: UUID, skip=0, limit=100):
        return self.repo.list_by_academic_year(db, academic_year_id, skip, limit)

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------
    def delete_assignment(self, db: Session, *, assignment_id: UUID):
        with db.begin():
            assignment = self.repo.get(db, assignment_id)
            if not assignment:
                raise ValidationError("Assignment not found")

            assignment.is_deleted = True

        return True