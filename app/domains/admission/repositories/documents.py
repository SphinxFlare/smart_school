# admission/repositories/documents.py

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select

from admission.models.applications import AdmissionDocument, DocumentType
from repositories.base import BaseRepository


class AdmissionDocumentRepository(BaseRepository[AdmissionDocument]):
    """
    Repository for AdmissionDocument persistence operations.
    
    Extends BaseRepository as this model does not contain school_id 
    (tenant isolation enforced via application_id upstream) 
    and does not support soft-delete (is_deleted).
    
    Responsibilities:
    - Encapsulate document retrieval patterns tied to applications.
    - Support filtering by verification state and document type.
    - Return ORM objects for service-layer manipulation.
    
    Non-Responsibilities:
    - Tenant isolation (enforced upstream by validating application_id ownership).
    - Business logic (verification rules, required document checks).
    - Transaction management (commit/rollback).
    - Soft-delete filtering (model does not support it).
    """

    def __init__(self):
        super().__init__(AdmissionDocument)

    # ---------------------------------------------------------------------
    # Custom Query Methods
    # ---------------------------------------------------------------------

    def list_by_application(
        self,
        db: Session,
        application_id: UUID
    ) -> List[AdmissionDocument]:
        """
        Retrieve all documents associated with a specific application.
        
        Ordered by created_at ascending for predictable display 
        (e.g., chronological upload order).
        
        Args:
            db: Database session.
            application_id: The admission application UUID.
            
        Returns:
            List of AdmissionDocument ORM objects.
        """
        stmt = select(self.model).where(
            self.model.application_id == application_id
        )

        stmt = stmt.order_by(self.model.created_at.asc())

        # No soft-delete filter applied (model does not support it)
        # No tenant filter applied (enforced upstream via application_id)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_verification_status(
        self,
        db: Session,
        application_id: UUID,
        is_verified: bool
    ) -> List[AdmissionDocument]:
        """
        Retrieve documents for an application filtered by verification state.
        
        Useful for admin queues (e.g., show only pending verifications).
        
        Args:
            db: Database session.
            application_id: The admission application UUID.
            is_verified: Boolean filter (True for verified, False for pending).
            
        Returns:
            List of AdmissionDocument ORM objects.
        """
        stmt = select(self.model).where(
            self.model.application_id == application_id,
            self.model.is_verified == is_verified
        )

        stmt = stmt.order_by(self.model.created_at.asc())

        result = db.execute(stmt)
        return list(result.scalars().all())

    def list_by_document_type(
        self,
        db: Session,
        application_id: UUID,
        document_type: DocumentType
    ) -> List[AdmissionDocument]:
        """
        Retrieve documents of a specific type for an application.
        
        Args:
            db: Database session.
            application_id: The admission application UUID.
            document_type: The DocumentType enum value.
            
        Returns:
            List of AdmissionDocument ORM objects.
        """
        stmt = select(self.model).where(
            self.model.application_id == application_id,
            self.model.document_type == document_type
        )

        stmt = stmt.order_by(self.model.created_at.asc())

        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_by_application_and_type(
        self,
        db: Session,
        application_id: UUID,
        document_type: DocumentType
    ) -> Optional[AdmissionDocument]:
        """
        Retrieve a single document of a specific type for an application.
        
        Useful for enforcing one-document-per-type policies at the service layer
        or checking existence before upload.
        
        Args:
            db: Database session.
            application_id: The admission application UUID.
            document_type: The DocumentType enum value.
            
        Returns:
            AdmissionDocument ORM object if found, else None.
        """
        stmt = select(self.model).where(
            self.model.application_id == application_id,
            self.model.document_type == document_type
        )

        # Typically we expect one active document per type, 
        # but returning the first found if multiple exist historically.
        stmt = stmt.order_by(self.model.created_at.desc()).limit(1)

        result = db.execute(stmt)
        return result.scalar_one_or_none()