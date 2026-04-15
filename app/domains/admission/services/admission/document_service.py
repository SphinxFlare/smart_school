# admission/services/admission/document_service.py

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from admission.models.applications import AdmissionDocument
from admission.repositories.documents import AdmissionDocumentRepository
from types.admissions import DocumentType


class DocumentService:
    """
    Service for managing Admission Document operations.
    
    Responsibilities:
    - Adding documents to an application.
    - Retrieving documents (list, single, filtered).
    - Managing verification state (verify/revoke).
    - Deleting documents.
    
    Constraints:
    - No business logic regarding application approval status.
    - No transaction management (commit/rollback delegated to caller).
    - No direct SQL (uses Repository).
    - Tenant isolation enforced upstream (via application_id validation).
    - Dependencies point downward (does not call ApplicationService).
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = AdmissionDocumentRepository()

    def add_document(
        self,
        application_id: UUID,
        document_type: DocumentType,
        file_path: str,
        file_name: str
    ) -> AdmissionDocument:
        """
        Register a new document for an application.
        
        Args:
            application_id: The UUID of the parent admission application.
            document_type: The type of document (e.g., BIRTH_CERTIFICATE).
            file_path: Storage path of the uploaded file.
            file_name: Original name of the uploaded file.
            
        Returns:
            The created AdmissionDocument ORM object.
            
        Note:
            Does not enforce uniqueness of document types. 
            Caller should check existing documents if 'one-per-type' 
            policy is required.
        """
        document = AdmissionDocument(
            application_id=application_id,
            document_type=document_type,
            file_path=file_path,
            file_name=file_name,
            is_verified=False,
            created_at=datetime.utcnow()
        )

        return self.repository.create(self.db, document)

    def get_document(
        self,
        document_id: UUID
    ) -> Optional[AdmissionDocument]:
        """
        Retrieve a specific document by ID.
        
        Args:
            document_id: The UUID of the document.
            
        Returns:
            AdmissionDocument object if found, else None.
        """
        return self.repository.get(self.db, document_id)

    def list_documents(
        self,
        application_id: UUID
    ) -> List[AdmissionDocument]:
        """
        Retrieve all documents for a specific application.
        
        Args:
            application_id: The UUID of the admission application.
            
        Returns:
            List of AdmissionDocument objects ordered by creation date.
        """
        return self.repository.list_by_application(
            db=self.db,
            application_id=application_id
        )

    def get_document_by_type(
        self,
        application_id: UUID,
        document_type: DocumentType
    ) -> Optional[AdmissionDocument]:
        """
        Retrieve a specific document type for an application.
        
        Useful for checking if a required document already exists.
        
        Args:
            application_id: The UUID of the admission application.
            document_type: The DocumentType enum value.
            
        Returns:
            AdmissionDocument object if found, else None.
        """
        return self.repository.get_by_application_and_type(
            db=self.db,
            application_id=application_id,
            document_type=document_type
        )

    def verify_document(
        self,
        document_id: UUID,
        verified_by_id: UUID
    ) -> AdmissionDocument:
        """
        Mark a document as verified.
        
        Args:
            document_id: The UUID of the document to verify.
            verified_by_id: The UUID of the admin/user performing verification.
            
        Returns:
            The updated AdmissionDocument ORM object.
            
        Raises:
            ValueError: If document not found.
        """
        document = self.get_document(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        document.is_verified = True
        document.verified_by_id = verified_by_id
        document.verified_at = datetime.utcnow()

        # Flush to persist changes within caller's transaction
        self.db.flush()
        return document

    def delete_document(
        self,
        document_id: UUID
    ) -> None:
        """
        Deleting admission documents is not allowed by default
        because documents are part of the audit/verification flow.
        Override only if business rules explicitly allow it.
        """
        raise NotImplementedError(
            "Document deletion is not allowed in admission workflow"
        )