# domains/academic/curriculam.py


from sqlalchemy import (
    Column,
    String,
    UUID,
    ForeignKey,
    DateTime,
    Boolean,
    Integer,
    Text,
    UniqueConstraint,
    Time,
    Index,
)
from datetime import datetime
import uuid
from db.base import Base


# ==============================
# SUBJECT
# ==============================

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)

    name = Column(String, nullable=False)
    code = Column(String, nullable=False)

    description = Column(Text)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)

    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_school_subject_code"),
        Index("ix_subject_school_id", "school_id"),
    )


# ==============================
# CLASS TIMETABLE
# ==============================

class ClassTimetable(Base):
    __tablename__ = "class_timetables"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id"), nullable=False)

    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False)

    day_of_week = Column(Integer, nullable=False)  # 0 = Monday
    period_number = Column(Integer, nullable=False)

    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    teacher_assignment_id = Column(UUID(as_uuid=True), ForeignKey("teacher_assignments.id"), nullable=False)

    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    room = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)

    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)

    __table_args__ = (
        UniqueConstraint(
            "class_id",
            "section_id",
            "day_of_week",
            "period_number",
            "academic_year_id",
            name="uq_class_section_day_period",
        ),
        Index("ix_timetable_class_section", "class_id", "section_id"),
    )


class TeacherAssignment(Base):
    __tablename__ = "teacher_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    staff_member_id = Column(UUID(as_uuid=True), ForeignKey("staff_members.id"), nullable=False)  # Cross-domain FK
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)  # Cross-domain
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id"), nullable=False)  # Cross-domain
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False)  # Cross-domain
    is_primary = Column(Boolean, default=True)  # Main teacher for subject/class
    created_at = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    __table_args__ = (
                UniqueConstraint(
                    "staff_member_id",
                    "class_id",
                    "section_id",
                    "subject_id",
                    "academic_year_id",
                    name="uq_teacher_assignment_unique"
                )
            )