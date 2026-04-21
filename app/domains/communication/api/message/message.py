# communication/api/message/message.py

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from sqlalchemy.orm import Session

from app.deps.auth import get_current_user
from app.deps.common import get_db

from communication.schemas.message import (
    MessageCreate,
    MessageResponse,
)

from communication.services.message.message_service import MessageService
from communication.workflows.message.send_message import SendMessageWorkflow


router = APIRouter(prefix="/messages", tags=["Messages"])

message_service = MessageService()
workflow = SendMessageWorkflow()


# ---------------------------------------------------------
# Send Message
# ---------------------------------------------------------

@router.post("/", response_model=MessageResponse)
def send_message(
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    message = workflow.execute(
        db=db,
        sender_id=current_user.id,  # ignore payload.sender_id
        body=payload.body,
        subject=payload.subject,
        user_ids=payload.recipient_ids,
        context_type=payload.context_type,
        context_id=payload.context_id,
        is_two_way=payload.is_two_way,
        allow_replies=payload.allow_replies,
        priority=payload.priority,
        attachments=[a.model_dump() for a in payload.attachments],
        is_draft=payload.is_draft,
    )

    return message


# ---------------------------------------------------------
# Get Sent Messages
# ---------------------------------------------------------

@router.get("/sent", response_model=List[MessageResponse])
def get_sent_messages(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    skip: int = 0,
    limit: int = Query(20, le=100),
):
    return message_service.get_sent_messages(
        db=db,
        sender_id=current_user.id,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------
# Get Drafts
# ---------------------------------------------------------

@router.get("/drafts", response_model=List[MessageResponse])
def get_drafts(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    skip: int = 0,
    limit: int = Query(20, le=100),
):
    return message_service.get_drafts(
        db=db,
        sender_id=current_user.id,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------
# Get Conversation Thread
# ---------------------------------------------------------

@router.get("/thread/{context_type}/{context_id}", response_model=List[MessageResponse])
def get_conversation_thread(
    context_type: str,
    context_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    skip: int = 0,
    limit: int = Query(50, le=100),
):
    return message_service.get_conversation_thread(
        db=db,
        context_type=context_type,
        context_id=context_id,
        skip=skip,
        limit=limit,
    )