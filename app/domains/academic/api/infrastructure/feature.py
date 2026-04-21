# academic/api/infrastructure/feature.py

from fastapi import APIRouter, Depends
from uuid import UUID
from pydantic import BaseModel

from academic.api.deps import get_context
from app.deps.roles import require_roles

from academic.services.infrastructure.feature_service import FeatureService


router = APIRouter(prefix="/academic/features", tags=["Features"])
service = FeatureService()


class FeatureToggle(BaseModel):
    feature_key: str
    is_enabled: bool


@router.post("/toggle")
def toggle_feature(payload: FeatureToggle, ctx=Depends(get_context), user=Depends(require_roles(["ADMIN"]))):
    db, _, school_id = ctx

    obj = service.set_feature(
        db,
        school_id=school_id,
        feature_key=payload.feature_key,
        is_enabled=payload.is_enabled
    )

    return {"feature_key": obj.feature_key, "is_enabled": obj.is_enabled}


@router.get("/")
def list_features(ctx=Depends(get_context)):
    db, _, school_id = ctx
    return service.list_all(db, school_id=school_id)