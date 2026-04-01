from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import success_response
from backend.app.dependencies import get_db
from backend.app.services.dashboard_service import get_dashboard_overview, get_data_quality_overview

# Error code prefix: DASH_xxx
router = APIRouter(prefix='/dashboard', tags=['\u793e\u4fdd\u67e5\u8be2'])


@router.get('/overview', summary="\u83b7\u53d6\u770b\u677f\u6982\u89c8", description="\u8fd4\u56de\u7cfb\u7edf\u6570\u636e\u6982\u89c8\uff0c\u5305\u62ec\u5bfc\u5165\u6279\u6b21\u6570\u3001\u8bb0\u5f55\u6570\u3001\u5458\u5de5\u6570\u7b49\u3002")
def dashboard_overview_endpoint(db: Session = Depends(get_db)):
    payload = get_dashboard_overview(db)
    return success_response(payload.model_dump(mode='json'), message='Dashboard overview retrieved.')


@router.get('/quality', summary="\u83b7\u53d6\u6570\u636e\u8d28\u91cf\u6982\u89c8", description="\u8fd4\u56de\u6570\u636e\u8d28\u91cf\u6307\u6807\uff0c\u5305\u62ec\u5f02\u5e38\u7387\u3001\u7f3a\u5931\u7387\u3001\u91cd\u590d\u7387\u7b49\u3002")
def dashboard_quality_endpoint(db: Session = Depends(get_db)):
    payload = get_data_quality_overview(db)
    return success_response(payload.model_dump(mode='json'), message='Data quality overview retrieved.')
