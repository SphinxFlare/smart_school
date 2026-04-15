# identity/models/profiles.py

from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, Boolean, Integer, Enum as SQLEnum, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from types.types import UserRoleType
from types.transport import DriverStatus
from db.base import Base 


class Student(Base):
    __tablename__ = "students"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True)

    admission_number = Column(String, nullable=False)

    date_of_birth = Column(DateTime, nullable=False)
    
    emergency_contact_name = Column(String)
    emergency_contact_phone = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    user = relationship("User", back_populates="student_profile")
    parents = relationship("StudentParent", back_populates="student", cascade="all, delete-orphan")
    enrollments = relationship("StudentEnrollment", back_populates="student", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("school_id", "admission_number", name="uq_student_school_adm_no"),
    )


class Parent(Base):
    __tablename__ = "parents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True)
    occupation = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="parent_profile")
    students = relationship("StudentParent", back_populates="parent", cascade="all, delete-orphan")


class StudentParent(Base):
    __tablename__ = "student_parents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("parents.id"), nullable=False)
    relationship = Column(String, nullable=False)  # "father", "mother", "guardian"
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
    UniqueConstraint("student_id", "parent_id", name="uq_student_parent_pair"),
)



class Driver(Base):
    __tablename__ = "drivers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    staff_member_id = Column(UUID(as_uuid=True), ForeignKey("staff_members.id"), unique=True, nullable=False)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True)
    license_number = Column(String, nullable=False)
    license_type = Column(String, nullable=False)  # keep flexible for regional types
    license_expiry = Column(DateTime, nullable=False)

    status = Column(SQLEnum(DriverStatus), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
    UniqueConstraint("school_id", "license_number", name="uq_driver_school_license"),
)



class StaffMember(Base):
    __tablename__ = "staff_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True)
    employee_id = Column(String, nullable=False)
    position = Column(String, nullable=False)
    department = Column(String)
    date_of_joining = Column(DateTime, nullable=False)
    qualifications = Column(JSONB)  # JSON array
    created_at = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="staff_profile")

    __table_args__ = (
    UniqueConstraint("school_id", "employee_id", name="uq_staff_school_emp_id"),
)