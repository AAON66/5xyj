from __future__ import annotations

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import success_response
from backend.app.dependencies import get_db
from backend.app.schemas.employees import EmployeeMasterStatusInput, EmployeeMasterUpdateInput
from backend.app.services.employee_service import (
    EmployeeDeleteBlockedError,
    EmployeeImportError,
    EmployeeMasterNotFoundError,
    delete_employee_master,
    import_employee_master_file,
    list_employee_master_audits,
    list_employee_masters,
    update_employee_master,
    update_employee_master_status,
)

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


@router.patch('/{employee_id}')
def update_employee_master_endpoint(
    employee_id: str,
    payload: EmployeeMasterUpdateInput = Body(...),
    db: Session = Depends(get_db),
):
    try:
        result = update_employee_master(db, employee_id, payload)
    except EmployeeMasterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return success_response(result.model_dump(mode='json'), message='Employee master record updated.')


@router.post('/{employee_id}/status')
def update_employee_master_status_endpoint(
    employee_id: str,
    payload: EmployeeMasterStatusInput = Body(...),
    db: Session = Depends(get_db),
):
    try:
        result = update_employee_master_status(db, employee_id, payload)
    except EmployeeMasterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return success_response(result.model_dump(mode='json'), message='Employee master status updated.')


@router.delete('/{employee_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_employee_master_endpoint(employee_id: str, db: Session = Depends(get_db)) -> Response:
    try:
        delete_employee_master(db, employee_id)
    except EmployeeMasterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EmployeeDeleteBlockedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get('/{employee_id}/audits')
def list_employee_master_audits_endpoint(employee_id: str, db: Session = Depends(get_db)):
    try:
        payload = list_employee_master_audits(db, employee_id)
    except EmployeeMasterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return success_response(payload.model_dump(mode='json'), message='Employee master audits retrieved.')
