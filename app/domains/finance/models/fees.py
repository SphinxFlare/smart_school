# finance/models/fees.py

from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, Numeric, Text, Boolean, Integer, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import JSONB
from db.base import Base
from datetime import datetime
import uuid
from types.types import FeeType # Assuming your Enums are here



class FeeCategory(Base):
    """
    User-extensible fee types with custom type support
    """
    __tablename__ = "fee_categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    type = Column(SQLEnum(FeeType), nullable=False)
    custom_type = Column(JSONB)  # {"type": "field_trip", "label": "Field Trip Fee"}
    name = Column(String, nullable=False)
    description = Column(Text)
    is_school_defined = Column(Boolean, default=True)  # False = user-defined
    is_active = Column(Boolean, default=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    
    __table_args__ = (
        Index('ix_fee_categories_school_id', 'school_id'),
        Index('ix_fee_categories_type', 'type'),
    )


class FeeStructure(Base):
    """
    Fee template per class/section for academic year
    """
    __tablename__ = "fee_structures"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("fee_categories.id"), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id"))
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False)
    amount = Column(Numeric, nullable=False)
    due_date = Column(DateTime, nullable=False)
    late_fee_amount = Column(Numeric, default=0.0)
    late_fee_after_days = Column(Integer, default=0)  # Days after due date
    description = Column(Text)
    is_published = Column(Boolean, default=False)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    
    __table_args__ = (
        Index('ix_fee_structures_academic_year', 'academic_year_id'),
        Index('ix_fee_structures_class_section', 'class_id', 'section_id'),
    )