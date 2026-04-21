# app/api/router.py

from fastapi import APIRouter

from domains.admission.api.router import router as admission_router
from domains.identity.api.router import router as identity_router
from domains.academic.api.router import router as academic_router 
from domains.communication.api.router import router as communication_router  


router = APIRouter()

# -------------------------
# Domains
# -------------------------
router.include_router(admission_router)
router.include_router(identity_router)
router.include_router(academic_router)  
router.include_router(communication_router )