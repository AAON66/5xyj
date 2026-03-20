from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import success_response
from backend.app.dependencies import get_db
from backend.app.services.dashboard_service import get_dashboard_overview

router = APIRouter(prefix='/dashboard', tags=['dashboard'])


@router.get('/overview')
def dashboard_overview_endpoint(db: Session = Depends(get_db)):
    payload = get_dashboard_overview(db)
    return success_response(payload.model_dump(mode='json'), message='Dashboard overview retrieved.')
