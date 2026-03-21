from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import success_response
from backend.app.dependencies import get_db
from backend.app.services.employee_service import EmployeeImportError, import_employee_master_file, list_employee_masters

router = APIRouter(prefix='/employees', tags=['employees'])


@router.get('')
def list_employee_masters_endpoint(
    query: str | None = Query(default=None),
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    payload = list_employee_masters(db, query=query, active_only=active_only)
    return success_response(payload.model_dump(mode='json'), message='Employee master records retrieved.')


@router.post('/import', status_code=status.HTTP_201_CREATED)
async def import_employee_masters_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        payload = await import_employee_master_file(db, file)
    except EmployeeImportError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Employee master file imported.', status_code=status.HTTP_201_CREATED)
