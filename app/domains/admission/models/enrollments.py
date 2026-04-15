# admission/models/enrollments.py


from sqlalchemy import (
    Column, String, UUID, ForeignKey, DateTime, 
    Enum as SQLEnum, Index, UniqueConstraint
    )
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from db.base import Base
from types.admissions import EnrollmentType



class StudentEnrollment(Base):
    __tablename__ = "student_enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    application_id = Column(UUID(as_uuid=True), ForeignKey("admission_applications.id"), nullable=True)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id"), nullable=False)
    enrollment_type = Column(SQLEnum(EnrollmentType), nullable=False)
    enrollment_number = Column(String, nullable=False)
    enrollment_date = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    student = relationship("Student", back_populates="enrollments")
    application = relationship(
        "AdmissionApplication",
        back_populates="enrollments"
    )

    __table_args__ = (
        Index("ix_enrollment_student_year", "student_id", "academic_year_id"),
        UniqueConstraint("student_id", "academic_year_id", name="uq_student_once_per_year"),
        UniqueConstraint("school_id", "enrollment_number", name="uq_school_enrollment_number"),
    )