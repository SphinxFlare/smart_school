# admission/models/applications.py

from sqlalchemy import (
    Column, String, UUID, ForeignKey, DateTime, Boolean,
    Text, Integer, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from db.base import Base
from types.admissions import ApplicationStatus, DocumentType, EnrollmentType


class AdmissionApplication(Base):
    __tablename__ = "admission_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False)

    # Student Snapshot
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    gender = Column(String, nullable=False)
    
    # Applying To
    applying_class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)

    # Previous school
    previous_school_name = Column(String)
    previous_school_last_class = Column(String)

    status = Column(SQLEnum(ApplicationStatus), nullable=False, default=ApplicationStatus.DRAFT)

    submitted_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    documents = relationship(
        "AdmissionDocument",
        back_populates="application",
        cascade="all, delete-orphan"
    )

    status_logs = relationship(
        "ApplicationStatusLog",
        back_populates="application",
        cascade="all, delete-orphan"
    )

    enrollments = relationship(
        "StudentEnrollment",
        back_populates="application"
    )

    student = relationship("Student")

    __table_args__ = (
        Index("ix_app_school_year_status", "school_id", "academic_year_id", "status"),
    )


class ApplicationStatusLog(Base):
    __tablename__ = "application_status_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    application_id = Column(UUID(as_uuid=True), ForeignKey("admission_applications.id"), nullable=False)

    from_status = Column(SQLEnum(ApplicationStatus), nullable=False)
    to_status = Column(SQLEnum(ApplicationStatus), nullable=False)

    changed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    remark = Column(Text)

    changed_at = Column(DateTime, default=datetime.utcnow)

    application = relationship(
        "AdmissionApplication",
        back_populates="status_logs"
    )

    __table_args__ = (
        Index("ix_status_logs_application", "application_id"),
    )


class AdmissionDocument(Base):
    __tablename__ = "admission_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    application_id = Column(UUID(as_uuid=True), ForeignKey("admission_applications.id"), nullable=False)

    document_type = Column(SQLEnum(DocumentType), nullable=False)

    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)

    is_verified = Column(Boolean, default=False)
    verified_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    verified_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship(
        "AdmissionApplication",
        back_populates="documents"
    )

    __table_args__ = (
        Index("ix_documents_application", "application_id"),
    )
