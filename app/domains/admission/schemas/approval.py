# app/domains/admission/schemas/approval.py


from pydantic import BaseModel,ConfigDict
from uuid import UUID
from typing import Optional

from .applications import ApplicationRead
from .enrollments import EnrollmentRead


class ApprovalRequest(BaseModel):
    section_id:UUID
    remark:Optional[str]=None
    model_config=ConfigDict(from_attributes=True)


class ApprovalResponse(BaseModel):
    application:ApplicationRead
    enrollment:Optional[EnrollmentRead]=None
    message:str
    model_config=ConfigDict(from_attributes=True)