# app/domains/admission/api/status_log.py


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from db.dependencies import get_db

from admission.services.admission.status_log_service import StatusLogService

from admission.schemas.status_log import (
    StatusLogRead,
    StatusLogListItem,
    StatusLogLatestResponse,
)


router = APIRouter(
    prefix="/logs",
    tags=["Admission Status Logs"],
)


# -----------------------------------------------------
# Get full history
# -----------------------------------------------------

@router.get(
    "/application/{application_id}",
    response_model=List[StatusLogListItem],
)
def get_history(
    application_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        service = StatusLogService(db=db)

        logs = service.get_history(
            application_id=application_id,
        )

        return logs

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------
# Get latest log
# -----------------------------------------------------

@router.get(
    "/application/{application_id}/latest",
    response_model=Optional[StatusLogLatestResponse],
)
def get_latest_log(
    application_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        service = StatusLogService(db=db)

        log = service.get_latest_log(
            application_id=application_id,
        )

        return log

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))