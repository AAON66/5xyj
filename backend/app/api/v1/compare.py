from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import success_response
from backend.app.dependencies import get_db
from backend.app.schemas.compare import CompareExportRequest
from backend.app.services.compare_service import build_compare_export_workbook, compare_batches
from backend.app.services.import_service import BatchNotFoundError

router = APIRouter(prefix='/compare', tags=['compare'])


@router.get('')
def compare_batches_endpoint(left_batch_id: str, right_batch_id: str, db: Session = Depends(get_db)):
    try:
        payload = compare_batches(db, left_batch_id, right_batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Batch comparison retrieved.')


@router.post('/export')
def export_batch_comparison_endpoint(request_body: CompareExportRequest):
    file_bytes, file_name = build_compare_export_workbook(request_body)
    quoted_file_name = quote(file_name)
    headers = {'Content-Disposition': f'attachment; filename="compare.xlsx"; filename*=UTF-8\'\'{quoted_file_name}'}
    return StreamingResponse(
        iter([file_bytes]),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers=headers,
    )
