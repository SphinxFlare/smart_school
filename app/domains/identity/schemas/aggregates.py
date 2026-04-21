# identity/schemas/aggregates.py


from typing import List, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel

from .user import UserReference
from .parent import ParentReference
from .student import StudentReference
from .staff import StaffReference
from .class_section import ClassSectionReference
from .role import RoleReference


# ---------------------------------------------------------------------
# USER AGGREGATES
# ---------------------------------------------------------------------

class UserAggregate(BaseModel):
    id: UUID
    email: str
    full_name: str
    is_active: bool

    roles: List[RoleReference] = []

    student_profile: Optional[StudentReference] = None
    parent_profile: Optional[ParentReference] = None
    staff_profile: Optional[StaffReference] = None


# ---------------------------------------------------------------------
# PARENT AGGREGATES
# ---------------------------------------------------------------------

class ParentStudentRelation(BaseModel):
    student: StudentReference
    relationship: str
    is_primary: bool


class ParentAggregate(BaseModel):
    id: UUID
    user: UserReference
    occupation: Optional[str] = None

    students: List[ParentStudentRelation] = []


# ---------------------------------------------------------------------
# STUDENT AGGREGATES
# ---------------------------------------------------------------------

class StudentParentRelation(BaseModel):
    parent: ParentReference
    relationship: str
    is_primary: bool


class StudentAggregate(BaseModel):
    id: UUID
    admission_number: str

    user: UserReference
    class_section: Optional[ClassSectionReference] = None

    parents: List[StudentParentRelation] = []


# ---------------------------------------------------------------------
# STAFF AGGREGATES
# ---------------------------------------------------------------------

class StaffAssignmentSummary(BaseModel):
    class_name: str
    section_name: str
    subject_name: str
    is_primary: bool


class StaffAggregate(BaseModel):
    id: UUID
    user: UserReference
    employee_id: str
    position: str
    department: Optional[str] = None

    assignments: List[StaffAssignmentSummary] = []
    total_classes_handled: int = 0