# communication/api/message/reply.py

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from sqlalchemy.orm import Session

from app.deps.auth import get_current_user
from app.deps.common import get_db

from communication.schemas.message import (
    MessageReplyCreate,
    MessageReplyResponse,
)

from communication.services.message.reply_service import ReplyService


router = APIRouter(prefix="/replies", tags=["Message Replies"])

service = ReplyService()


# ---------------------------------------------------------
# Create Reply
# ---------------------------------------------------------

@router.post("/", response_model=MessageReplyResponse)
def create_reply(
    payload: MessageReplyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    reply = service.create_reply(
        db=db,
        message_id=payload.message_id,
        sender_id=current_user.id,  # ignore payload.sender_id
        body=payload.body,
        parent_reply_id=payload.parent_reply_id,
        attachments=[a.model_dump() for a in payload.attachments],
    )

    return reply


# ---------------------------------------------------------
# List Replies (Top-level)
# ---------------------------------------------------------

@router.get("/{message_id}", response_model=List[MessageReplyResponse])
def list_replies(
    message_id: UUID,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = Query(50, le=100),
):
    return service.list_replies(
        db=db,
        message_id=message_id,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------
# List Child Replies (Threading)
# ---------------------------------------------------------

@router.get("/child/{parent_reply_id}", response_model=List[MessageReplyResponse])
def list_child_replies(
    parent_reply_id: UUID,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = Query(50, le=100),
):
    return service.list_child_replies(
        db=db,
        parent_reply_id=parent_reply_id,
        skip=skip,
        limit=limit,
    )