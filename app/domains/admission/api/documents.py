# app/domains/admission/api/documents.py


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from db.dependencies import get_db

from admission.services.admission.document_service import DocumentService

from admission.schemas.documents import (
    DocumentCreate,
    DocumentRead,
    DocumentListItem,
    DocumentVerifyRequest,
)

from types.admissions import DocumentType


router = APIRouter(
    prefix="/documents",
    tags=["Admission Documents"],
)


# -----------------------------------------------------
# List documents by application
# -----------------------------------------------------

@router.get(
    "/application/{application_id}",
    response_model=List[DocumentListItem],
)
def list_documents(
    application_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        service = DocumentService(db=db)

        documents = service.list_documents(
            application_id=application_id,
        )

        return documents

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------
# Get document by id
# -----------------------------------------------------

@router.get(
    "/{document_id}",
    response_model=DocumentRead,
)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        service = DocumentService(db=db)

        document = service.get_document(
            document_id=document_id,
        )

        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found",
            )

        return document

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------
# Add document
# -----------------------------------------------------

@router.post(
    "/",
    response_model=DocumentRead,
)
def add_document(
    document_data: DocumentCreate,
    db: Session = Depends(get_db),
):
    try:
        service = DocumentService(db=db)

        document = service.add_document(
            application_id=document_data.application_id,
            document_type=document_data.document_type,
            file_path=document_data.file_path,
            file_name=document_data.file_name,
        )

        return document

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------
# Verify document
# -----------------------------------------------------

@router.post(
    "/{document_id}/verify",
    response_model=DocumentRead,
)
def verify_document(
    document_id: UUID,
    verify_data: DocumentVerifyRequest,
    db: Session = Depends(get_db),
):
    try:
        service = DocumentService(db=db)

        document = service.verify_document(
            document_id=document_id,
            verified_by_id=verify_data.verified_by_id,
        )

        return document

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------
# Get document by type
# -----------------------------------------------------

@router.get(
    "/application/{application_id}/type/{document_type}",
    response_model=Optional[DocumentRead],
)
def get_document_by_type(
    application_id: UUID,
    document_type: DocumentType,
    db: Session = Depends(get_db),
):
    try:
        service = DocumentService(db=db)

        document = service.get_document_by_type(
            application_id=application_id,
            document_type=document_type,
        )

        return document

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))