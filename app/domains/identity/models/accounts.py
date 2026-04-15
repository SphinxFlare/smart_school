# identity/models/accounts.py

from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, Boolean, Integer, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from types.types import UserRoleType
from db.base import Base 



class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(DateTime)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    
    # Relationships (within domain)
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    student_profile = relationship("Student", uselist=False, back_populates="user")
    parent_profile = relationship("Parent", uselist=False, back_populates="user")
    staff_profile = relationship("StaffMember", uselist=False, back_populates="user")

    __table_args__ = (
    UniqueConstraint("school_id", "email", name="uq_user_school_email"),
    UniqueConstraint("school_id", "phone", name="uq_user_school_phone"),
    )


class Role(Base):
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True)
    name = Column(SQLEnum(UserRoleType), nullable=False)
    description = Column(String)
    permissions = Column(String)  # JSON string of permissions
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("school_id", "name", name="uq_role_school_name"),
    )



class UserRole(Base):
    __tablename__ = "user_roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", foreign_keys=[user_id], back_populates="roles")
    