# app/domains/admission/schemas/enrollments.py


from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

from types.admissions import EnrollmentType


class EnrollmentBase(BaseModel):
    student_id:UUID
    academic_year_id:UUID
    class_id:UUID
    section_id:UUID
    enrollment_type:EnrollmentType
    enrollment_number:str
    model_config=ConfigDict(from_attributes=True)


class EnrollmentRead(EnrollmentBase):
    id:UUID
    school_id:UUID
    application_id:Optional[UUID]=None
    enrollment_date:datetime
    created_by_id:UUID
    model_config=ConfigDict(from_attributes=True)


class EnrollmentListItem(BaseModel):
    id:UUID
    student_id:UUID
    academic_year_id:UUID
    enrollment_number:str
    enrollment_date:datetime
    model_config=ConfigDict(from_attributes=True)


class EnrollmentByNumberResponse(BaseModel):
    id:UUID
    student_id:UUID
    enrollment_number:str
    academic_year_id:UUID
    class_id:UUID
    section_id:UUID
    enrollment_date:datetime
    model_config=ConfigDict(from_attributes=True)