# domains/academic/assessment.py

from sqlalchemy import (
    Column,
    String,
    UUID,
    ForeignKey,
    DateTime,
    Boolean,
    Integer,
    Enum as SQLEnum,
    Text,
    UniqueConstraint,
    Numeric,
    Time,
    Index,
    Float,
    CheckConstraint,
)
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import JSONB
from types.types import ExamType
from types.results import GradeLetter, ResultStatus, RankType, SubmissionStatus
from db.base import Base


# ==============================
# EXAM
# ==============================

class Exam(Base):
    __tablename__ = "exams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False)

    name = Column(String, nullable=False)
    type = Column(SQLEnum(ExamType), nullable=False)

    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    description = Column(Text)

    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)

    __table_args__ = (
        Index("ix_exam_school_year", "school_id", "academic_year_id"),
    )


# ==============================
# EXAM SCHEDULE
# ==============================

class ExamSchedule(Base):
    __tablename__ = "exam_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False)

    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id"), nullable=False)

    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)

    date = Column(DateTime, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    room = Column(String)
    invigilator_id = Column(UUID(as_uuid=True), ForeignKey("staff_members.id"))

    is_published = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)

    __table_args__ = (
        UniqueConstraint(
            "exam_id",
            "class_id",
            "section_id",
            "subject_id",
            name="uq_exam_class_section_subject",
        ),
        Index("ix_exam_schedule_exam", "exam_id"),
    )


# ==============================
# GRADE SCALE
# ==============================

class GradeScale(Base):
    __tablename__ = "grade_scales"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)

    min_percentage = Column(Numeric(5, 2), nullable=False)
    max_percentage = Column(Numeric(5, 2), nullable=False)

    grade_letter = Column(SQLEnum(GradeLetter), nullable=False)
    grade_point = Column(Numeric(3, 2), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "grade_letter",
            name="uq_school_grade_letter",
        ),
        Index("ix_grade_scale_school", "school_id"),
    )


# ==============================
# STUDENT EXAM MARK
# ==============================

class StudentExamMark(Base):
    __tablename__ = "student_exam_marks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    exam_schedule_id = Column(UUID(as_uuid=True), ForeignKey("exam_schedules.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)

    max_marks = Column(Numeric(5, 2), nullable=False)
    marks_obtained = Column(Numeric(5, 2), nullable=False)

    percentage = Column(Numeric(5, 2))
    grade_letter = Column(SQLEnum(GradeLetter))
    grade_point = Column(Numeric(3, 2))

    is_absent = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "exam_schedule_id",
            "student_id",
            name="uq_schedule_student",
        ),
        CheckConstraint(
            "marks_obtained <= max_marks",
            name="ck_marks_not_exceed_max",
        ),
        Index("ix_exam_mark_student", "student_id"),
    )


# ==============================
# STUDENT EXAM RESULT (AGGREGATE)
# ==============================

class StudentExamResult(Base):
    __tablename__ = "student_exam_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)

    total_marks = Column(Numeric(6, 2))
    obtained_marks = Column(Numeric(6, 2))
    percentage = Column(Numeric(5, 2))
    cgpa = Column(Numeric(3, 2))

    result_status = Column(SQLEnum(ResultStatus), nullable=False)

    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "exam_id",
            "student_id",
            name="uq_exam_student_result",
        ),
        Index("ix_exam_result_exam", "exam_id"),
    )


# ==============================
# STUDENT EXAM RANK
# ==============================

class StudentExamRank(Base):
    __tablename__ = "student_exam_ranks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)

    rank_type = Column(SQLEnum(RankType), nullable=False)
    rank_position = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "exam_id",
            "student_id",
            "rank_type",
            name="uq_exam_student_rank_type",
        ),
        Index("ix_exam_rank_exam", "exam_id"),
    )


class Homework(Base):
    __tablename__ = "homework"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    teacher_assignment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("teacher_assignments.id", ondelete="CASCADE"),
        nullable=False
    )

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    assigned_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)

    # Use Numeric instead of Float to avoid precision issues
    max_marks = Column(Numeric(5, 2))

    # Default empty list to avoid null JSON problems
    attachments = Column(JSONB, default=list, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    is_deleted = Column(Boolean, default=False, nullable=False)

    # ------------------------------------------------------------------
    # Index Strategy (Aligned with Repository Layer)
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("ix_homework_teacher_assignment", "teacher_assignment_id"),
        Index("ix_homework_assigned_date", "assigned_date"),
        Index("ix_homework_due_date", "due_date"),
        Index("ix_homework_is_deleted", "is_deleted"),
    )


class HomeworkSubmission(Base):
    __tablename__ = "homework_submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    homework_id = Column(
        UUID(as_uuid=True),
        ForeignKey("homework.id", ondelete="CASCADE"),
        nullable=False
    )

    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False
    )

    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Strong typing instead of raw strings
    status = Column(
        SQLEnum(SubmissionStatus, name="submission_status"),
        nullable=False
    )

    file_path = Column(String)
    remarks = Column(Text)

    # Numeric prevents precision drift in averages
    marks_awarded = Column(Numeric(5, 2))

    graded_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )

    graded_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # ------------------------------------------------------------------
    # Constraints & Index Strategy
    # ------------------------------------------------------------------
    __table_args__ = (
        # Prevent duplicate submissions per student per homework
        UniqueConstraint(
            "homework_id",
            "student_id",
            name="uq_submission_homework_student"
        ),

        Index("ix_submission_homework", "homework_id"),
        Index("ix_submission_student", "student_id"),
        Index("ix_submission_status", "status"),
        Index("ix_submission_submitted_at", "submitted_at"),
        Index("ix_submission_graded_by", "graded_by_id"),
        Index("ix_submission_graded_at", "graded_at"),
    )