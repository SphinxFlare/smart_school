# communication/api/message/recipient.py

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Body

from sqlalchemy.orm import Session

from app.deps.auth import get_current_user
from app.deps.common import get_db

from communication.services.message.recipient_service import RecipientService
from communication.models.messaging import MessageRecipient


router = APIRouter(prefix="/recipients", tags=["Message Recipients"])

service = RecipientService()


# ---------------------------------------------------------
# Inbox
# ---------------------------------------------------------

@router.get("/inbox", response_model=List[MessageRecipient])
def get_inbox(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    skip: int = 0,
    limit: int = Query(20, le=100),
):
    return service.get_inbox(
        db=db,
        recipient_id=current_user.id,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------
# Unread Messages
# ---------------------------------------------------------

@router.get("/unread", response_model=List[MessageRecipient])
def get_unread(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    skip: int = 0,
    limit: int = Query(20, le=100),
):
    return service.get_unread_messages(
        db=db,
        recipient_id=current_user.id,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------
# Starred Messages
# ---------------------------------------------------------

@router.get("/starred", response_model=List[MessageRecipient])
def get_starred(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    skip: int = 0,
    limit: int = Query(20, le=100),
):
    return service.get_starred_messages(
        db=db,
        recipient_id=current_user.id,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------
# Unread Count
# ---------------------------------------------------------

@router.get("/unread/count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    count = service.count_unread(
        db=db,
        recipient_id=current_user.id,
    )

    return {"unread_count": count}


# ---------------------------------------------------------
# Mark Single as Read
# ---------------------------------------------------------

@router.post("/read/{message_id}")
def mark_as_read(
    message_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    success = service.mark_as_read(
        db=db,
        recipient_id=current_user.id,
        message_id=message_id,
    )

    return {"success": success}


# ---------------------------------------------------------
# Bulk Mark as Read
# ---------------------------------------------------------

@router.post("/read/bulk")
def bulk_mark_as_read(
    message_ids: List[UUID] = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    updated = service.bulk_mark_as_read(
        db=db,
        recipient_id=current_user.id,
        message_ids=message_ids,
    )

    return {"updated_count": updated}