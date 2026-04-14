from __future__ import annotations

from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import success_response
from backend.app.dependencies import get_db
from backend.app.schemas.compare import CompareExportRequest
from backend.app.services.compare_service import build_compare_export_workbook, compare_batches, compare_periods
from backend.app.services.import_service import BatchNotFoundError

# Error code prefix: CMP_xxx
router = APIRouter(prefix='/compare', tags=['\u793e\u4fdd\u67e5\u8be2'])


@router.get('', summary="\u5bf9\u6bd4\u4e24\u4e2a\u6279\u6b21", description="\u6bd4\u8f83\u4e24\u4e2a\u5bfc\u5165\u6279\u6b21\u7684\u6570\u636e\u5dee\u5f02\uff0c\u8fd4\u56de\u65b0\u589e\u3001\u5220\u9664\u548c\u53d8\u66f4\u8bb0\u5f55\u3002")
def compare_batches_endpoint(left_batch_id: str, right_batch_id: str, db: Session = Depends(get_db)):
    try:
        payload = compare_batches(db, left_batch_id, right_batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Batch comparison retrieved.')


@router.post('/export', summary="\u5bfc\u51fa\u5bf9\u6bd4\u7ed3\u679c", description="\u5c06\u6279\u6b21\u5bf9\u6bd4\u7ed3\u679c\u5bfc\u51fa\u4e3a Excel \u6587\u4ef6\u3002")
def export_batch_comparison_endpoint(request_body: CompareExportRequest):
    file_bytes, file_name = build_compare_export_workbook(request_body)
    quoted_file_name = quote(file_name)
    headers = {'Content-Disposition': f'attachment; filename="compare.xlsx"; filename*=UTF-8\'\'{quoted_file_name}'}
    return StreamingResponse(
        iter([file_bytes]),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers=headers,
    )


@router.get(
    '/periods',
    summary="跨账期对比",
    description="对比两个账期的社保数据差异，返回新增、删除和变更记录。支持按地区和公司筛选。",
)
def compare_periods_endpoint(
    left_period: str = Query(..., description="左侧账期"),
    right_period: str = Query(..., description="右侧账期"),
    region: Optional[str] = Query(None, description="地区筛选"),
    company_name: Optional[str] = Query(None, description="公司筛选"),
    search_text: Optional[str] = Query(None, description="关键词搜索"),
    diff_only: bool = Query(False, description="仅返回存在差异的记录"),
    page: int = Query(0, ge=0, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页条数"),
    db: Session = Depends(get_db),
):
    payload = compare_periods(
        db,
        left_period,
        right_period,
        region=region,
        company_name=company_name,
        search_text=search_text,
        diff_only=diff_only,
        page=page,
        page_size=page_size,
    )
    return success_response(payload.model_dump(mode='json'), message='Period comparison retrieved.')
