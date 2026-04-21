# app/domains/admission/schemas/status_log.py


from pydantic import BaseModel,ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

from types.admissions import ApplicationStatus


class StatusLogBase(BaseModel):
    application_id:UUID
    from_status:ApplicationStatus
    to_status:ApplicationStatus
    changed_by_id:UUID
    remark:Optional[str]=None
    model_config=ConfigDict(from_attributes=True)


class StatusLogRead(StatusLogBase):
    id:UUID
    changed_at:datetime
    model_config=ConfigDict(from_attributes=True)


class StatusLogListItem(BaseModel):
    id:UUID
    from_status:ApplicationStatus
    to_status:ApplicationStatus
    changed_by_id:UUID
    changed_at:datetime
    remark:Optional[str]=None
    model_config=ConfigDict(from_attributes=True)


class StatusLogLatestResponse(BaseModel):
    id:UUID
    from_status:ApplicationStatus
    to_status:ApplicationStatus
    changed_at:datetime
    changed_by_id:UUID
    remark:Optional[str]=None
    model_config=ConfigDict(from_attributes=True)