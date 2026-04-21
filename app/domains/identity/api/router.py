# identity/api/router.py

from fastapi import APIRouter
from .users.router import router as users_router
from .roles.router import router as roles_router
from .profiles.student_router import router as student_router
from .profiles.parent_router import router as parent_router
from .profiles.staff_router import router as staff_router
from .profiles.driver_router import router as driver_router
from .aggregates.router import router as identity_agg_router

router = APIRouter(
    prefix="/identity",
    tags=["Identity"],
)

# -------------------------
# Users
# -------------------------
router.include_router(users_router)

# -------------------------
# Roles
# -------------------------
router.include_router(roles_router)

# -------------------------
# Students
# -------------------------
router.include_router(student_router)

# -------------------------
# Parents
# -------------------------
router.include_router(parent_router)

# -------------------------
# Staffs
# -------------------------
router.include_router(staff_router)

# -------------------------
# Drivers
# -------------------------
router.include_router(driver_router)

# -------------------------
# Identity Aggregates
# -------------------------
router.include_router(identity_agg_router)