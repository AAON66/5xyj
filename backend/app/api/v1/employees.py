from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import success_response
from backend.app.core.auth import AuthUser
from backend.app.dependencies import get_db, require_authenticated_user
from backend.app.utils.masking import mask_id_number
from backend.app.schemas.employees import (
    EmployeeMasterCreateInput,
    EmployeeMasterStatusInput,
    EmployeeMasterUpdateInput,
    EmployeeSelfServiceQueryInput,
)
from backend.app.services.employee_service import (
    EmployeeDeleteBlockedError,
    EmployeeMasterAuditNotFoundError,
    EmployeeMasterConflictError,
    EmployeeImportError,
    EmployeeMasterNotFoundError,
    EmployeeSelfServiceNotFoundError,
    create_employee_master,
    delete_employee_master_audit,
    delete_employee_master,
    import_employee_master_file,
    list_employee_master_audits,
    list_employee_masters,
    lookup_employee_self_service,
    update_employee_master,
    update_employee_master_status,
)

router = APIRouter(prefix='/employees', tags=['employees'])


@router.get('')
def list_employee_masters_endpoint(
    query: Optional[str] = Query(default=None),
    active_only: bool = Query(default=False),
    limit: Optional[int] = Query(default=None, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_authenticated_user),
):
    payload = list_employee_masters(db, query=query, active_only=active_only, limit=limit, offset=offset)
    data = payload.model_dump(mode='json')
    # Employee role sees masked ID numbers (per D-09); admin/HR see full (per D-11)
    if user.role == "employee":
        for item in data.get("items", []):
            if "id_number" in item:
                item["id_number"] = mask_id_number(item["id_number"])
    return success_response(data, message='Employee master records retrieved.')


@router.post('', status_code=status.HTTP_201_CREATED)
def create_employee_master_endpoint(
    payload: EmployeeMasterCreateInput = Body(...),
    db: Session = Depends(get_db),
    _user=Depends(require_authenticated_user),
):
    try:
        result = create_employee_master(db, payload)
    except EmployeeMasterConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return success_response(result.model_dump(mode='json'), message='Employee master record created.', status_code=status.HTTP_201_CREATED)


@router.post('/import', status_code=status.HTTP_201_CREATED)
async def import_employee_masters_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _user=Depends(require_authenticated_user),
):
    try:
        payload = await import_employee_master_file(db, file)
    except EmployeeImportError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Employee master file imported.', status_code=status.HTTP_201_CREATED)


@router.post('/self-service/query')
def employee_self_service_query_endpoint(
    payload: EmployeeSelfServiceQueryInput = Body(...),
    db: Session = Depends(get_db),
):
    try:
        result = lookup_employee_self_service(db, payload)
    except EmployeeSelfServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return success_response(result.model_dump(mode='json'), message='Employee self-service result retrieved.')


@router.patch('/{employee_id}')
def update_employee_master_endpoint(
    employee_id: str,
    payload: EmployeeMasterUpdateInput = Body(...),
    db: Session = Depends(get_db),
    _user=Depends(require_authenticated_user),
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
    _user=Depends(require_authenticated_user),
):
    try:
        result = update_employee_master_status(db, employee_id, payload)
    except EmployeeMasterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return success_response(result.model_dump(mode='json'), message='Employee master status updated.')


@router.delete('/{employee_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_employee_master_endpoint(
    employee_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_authenticated_user),
) -> Response:
    try:
        delete_employee_master(db, employee_id)
    except EmployeeMasterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EmployeeDeleteBlockedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get('/{employee_id}/audits')
def list_employee_master_audits_endpoint(
    employee_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_authenticated_user),
):
    try:
        payload = list_employee_master_audits(db, employee_id)
    except EmployeeMasterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return success_response(payload.model_dump(mode='json'), message='Employee master audits retrieved.')


@router.delete('/{employee_id}/audits/{audit_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_employee_master_audit_endpoint(
    employee_id: str,
    audit_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_authenticated_user),
) -> Response:
    try:
        delete_employee_master_audit(db, employee_id, audit_id)
    except EmployeeMasterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EmployeeMasterAuditNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
