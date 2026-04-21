# app/domains/admission/api/router.py


from fastapi import APIRouter

from admission.api.applications import router as applications_router
from admission.api.documents import router as documents_router
from admission.api.approval import router as approval_router
from admission.api.enrollments import router as enrollments_router
from admission.api.status_log import router as logs_router


router = APIRouter(
    prefix="/admission",
    tags=["Admission"],
)


# -------------------------
# Applications
# -------------------------

router.include_router(applications_router)


# -------------------------
# Documents
# -------------------------

router.include_router(documents_router)


# -------------------------
# Approval workflow
# -------------------------

router.include_router(approval_router)


# -------------------------
# Enrollments
# -------------------------

router.include_router(enrollments_router)


# -------------------------
# Logs
# -------------------------

router.include_router(logs_router)