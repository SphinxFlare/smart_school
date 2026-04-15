# identity/schemas/__init__.py

# Add to existing __all__ list
from .parent import ParentBase, ParentCreate, ParentUpdate, ParentResponse, ParentReference
from .staff import StaffBase, StaffCreate, StaffUpdate, StaffResponse, StaffReference
from .class_section import (
    ClassBase, ClassCreate, ClassUpdate, ClassResponse, ClassReference,
    SectionBase, SectionCreate, SectionUpdate, SectionResponse, SectionReference,
    ClassSectionReference
)
from .role import RoleBase, RoleCreate, RoleUpdate, RoleResponse, RoleReference, UserRoleAssignment
from .school import (
    SchoolBase, SchoolCreate, SchoolUpdate, SchoolResponse, SchoolReference,
    SchoolStats, SchoolSettings
)

# Add to __all__:
"ParentBase", "ParentCreate", "ParentUpdate", "ParentResponse", "ParentReference",
"StaffBase", "StaffCreate", "StaffUpdate", "StaffResponse", "StaffReference",
"ClassBase", "ClassCreate", "ClassUpdate", "ClassResponse", "ClassReference",
"SectionBase", "SectionCreate", "SectionUpdate", "SectionResponse", "SectionReference",
"ClassSectionReference",
"RoleBase", "RoleCreate", "RoleUpdate", "RoleResponse", "RoleReference", "UserRoleAssignment",
"SchoolBase", "SchoolCreate", "SchoolUpdate", "SchoolResponse", "SchoolReference",
"SchoolStats", "SchoolSettings"