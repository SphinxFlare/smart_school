# app/domains/admission/schemas/documents.py


from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

from types.admissions import DocumentType


# =====================================================
# Base
# =====================================================

class DocumentBase(BaseModel):
    """
    Common fields for admission documents.
    """

    document_type: DocumentType
    file_path: str
    file_name: str

    model_config = ConfigDict(from_attributes=True)


# =====================================================
# Create
# =====================================================

class DocumentCreate(DocumentBase):
    """
    Request schema for uploading a document.
    """

    application_id: UUID


# =====================================================
# Read
# =====================================================

class DocumentRead(DocumentBase):
    """
    Full document response.
    """

    id: UUID

    application_id: UUID

    is_verified: bool

    verified_by_id: Optional[UUID] = None
    verified_at: Optional[datetime] = None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =====================================================
# List item
# =====================================================

class DocumentListItem(BaseModel):
    """
    Lightweight schema for list endpoints.
    """

    id: UUID

    document_type: DocumentType

    file_name: str

    is_verified: bool

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =====================================================
# Verify request
# =====================================================

class DocumentVerifyRequest(BaseModel):
    """
    Request schema for verifying document.
    """

    verified_by_id: UUID

    model_config = ConfigDict(from_attributes=True)