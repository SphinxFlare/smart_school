# academic/services/curriculum/timetable_service.py


from uuid import UUID
from sqlalchemy.orm import Session

from academic.models.curriculum import ClassTimetable
from academic.repositories.Curriculum.timetable_repository import ClassTimetableRepository
from academic.services.common.validator_service import ValidatorService, ValidationError
from academic.services.common.ownership_service import OwnershipService


class TimetableService:

    def __init__(self):
        self.repo = ClassTimetableRepository()
        self.validator = ValidatorService()
        self.ownership = OwnershipService()

    # ---------------------------------------------------------
    # CREATE / UPDATE SLOT
    # ---------------------------------------------------------
    def upsert_slot(
        self,
        db: Session,
        *,
        school_id: UUID,
        class_id: UUID,
        section_id: UUID,
        academic_year_id: UUID,
        day_of_week: int,
        period_number: int,
        subject_id: UUID,
        teacher_assignment_id: UUID,
        start_time,
        end_time,
        room: str | None = None
    ):
        self.ownership.validate_class(db, class_id, school_id)
        self.ownership.validate_section(db, section_id, school_id)
        self.ownership.validate_teacher_assignment(db, teacher_assignment_id, school_id)

        self.validator.validate_range(day_of_week, 0, 6, "day_of_week")
        self.validator.validate_positive(period_number, "period_number")

        with db.begin():
            slot = self.repo.get_period_slot_locked(
                db,
                class_id,
                section_id,
                day_of_week,
                period_number,
                academic_year_id
            )

            if slot:
                slot.subject_id = subject_id
                slot.teacher_assignment_id = teacher_assignment_id
                slot.start_time = start_time
                slot.end_time = end_time
                slot.room = room
                return slot

            obj = ClassTimetable(
                class_id=class_id,
                section_id=section_id,
                academic_year_id=academic_year_id,
                day_of_week=day_of_week,
                period_number=period_number,
                subject_id=subject_id,
                teacher_assignment_id=teacher_assignment_id,
                start_time=start_time,
                end_time=end_time,
                room=room,
            )
            return self.repo.create(db, obj)

    # ---------------------------------------------------------
    # GET
    # ---------------------------------------------------------
    def get_timetable(self, db: Session, *, class_id: UUID, section_id: UUID, academic_year_id: UUID, skip=0, limit=100):
        return self.repo.list_by_class_section(db, class_id, section_id, academic_year_id, skip, limit)

    def get_teacher_schedule(self, db: Session, *, teacher_assignment_id: UUID, academic_year_id: UUID, skip=0, limit=100):
        return self.repo.list_by_teacher_assignment(db, teacher_assignment_id, academic_year_id, skip, limit)

    # ---------------------------------------------------------
    # DELETE SLOT
    # ---------------------------------------------------------
    def delete_slot(
        self,
        db: Session,
        *,
        class_id: UUID,
        section_id: UUID,
        day_of_week: int,
        period_number: int,
        academic_year_id: UUID
    ):
        with db.begin():
            slot = self.repo.get_period_slot_locked(
                db,
                class_id,
                section_id,
                day_of_week,
                period_number,
                academic_year_id
            )
            if not slot:
                raise ValidationError("Slot not found")

            slot.is_deleted = True

        return True