from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import success_response
from backend.app.core.auth import AuthUser
from backend.app.dependencies import get_db, require_authenticated_user
from backend.app.models import EmployeeMaster
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

# Error code prefix: EMP_xxx
router = APIRouter(prefix='/employees', tags=['\u5458\u5de5\u7ba1\u7406'])


@router.get('', summary="\u67e5\u8be2\u5458\u5de5\u4e3b\u6570\u636e\u5217\u8868", description="\u5206\u9875\u67e5\u8be2\u5458\u5de5\u4e3b\u6570\u636e\uff0c\u652f\u6301\u6309\u59d3\u540d\u3001\u5730\u533a\u3001\u516c\u53f8\u7b5b\u9009\u3002")
def list_employee_masters_endpoint(
    query: Optional[str] = Query(default=None),
    region: Optional[str] = Query(default=None),
    company_name: Optional[str] = Query(default=None),
    active_only: bool = Query(default=False),
    limit: Optional[int] = Query(default=None, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_authenticated_user),
):
    payload = list_employee_masters(db, query=query, region=region, company_name=company_name, active_only=active_only, limit=limit, offset=offset)
    data = payload.model_dump(mode='json')
    # Employee role sees masked ID numbers (per D-09); admin/HR see full (per D-11)
    if user.role == "employee":
        for item in data.get("items", []):
            if "id_number" in item:
                item["id_number"] = mask_id_number(item["id_number"])
    return success_response(data, message='Employee master records retrieved.')


@router.post('', status_code=status.HTTP_201_CREATED, summary="\u521b\u5efa\u5458\u5de5\u4e3b\u6570\u636e", description="\u65b0\u589e\u4e00\u6761\u5458\u5de5\u4e3b\u6570\u636e\u8bb0\u5f55\u3002")
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


@router.post('/import', status_code=status.HTTP_201_CREATED, summary="\u5bfc\u5165\u5458\u5de5\u4e3b\u6570\u636e", description="\u901a\u8fc7 Excel \u6587\u4ef6\u6279\u91cf\u5bfc\u5165\u5458\u5de5\u4e3b\u6570\u636e\u3002")
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


SUPPORTED_REGIONS = ["广州", "杭州", "厦门", "深圳", "武汉", "长沙"]


@router.get('/regions', summary="\u83b7\u53d6\u652f\u6301\u7684\u5730\u533a\u5217\u8868", description="\u8fd4\u56de\u7cfb\u7edf\u5f53\u524d\u652f\u6301\u89e3\u6790\u7684\u5730\u533a\u5217\u8868\u3002")
def list_regions_endpoint():
    return success_response(SUPPORTED_REGIONS)


@router.get('/companies', summary="\u83b7\u53d6\u516c\u53f8\u5217\u8868", description="\u8fd4\u56de\u5458\u5de5\u4e3b\u6570\u636e\u4e2d\u5df2\u5f55\u5165\u7684\u516c\u53f8\u540d\u79f0\u5217\u8868\u3002")
def list_companies_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_authenticated_user),
):
    rows = db.query(EmployeeMaster.company_name).filter(
        EmployeeMaster.company_name.isnot(None)
    ).distinct().order_by(EmployeeMaster.company_name.asc()).all()
    companies = [row[0] for row in rows]
    return success_response(companies)


@router.post('/self-service/query', summary="\u5458\u5de5\u81ea\u52a9\u67e5\u8be2", description="\u5458\u5de5\u901a\u8fc7\u5de5\u53f7\u3001\u8eab\u4efd\u8bc1\u53f7\u548c\u59d3\u540d\u67e5\u8be2\u4e2a\u4eba\u793e\u4fdd\u4fe1\u606f\u3002")
def employee_self_service_query_endpoint(
    payload: EmployeeSelfServiceQueryInput = Body(...),
    db: Session = Depends(get_db),
    _user=Depends(require_authenticated_user),
):
    try:
        result = lookup_employee_self_service(db, payload)
    except EmployeeSelfServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return success_response(result.model_dump(mode='json'), message='Employee self-service result retrieved.')


@router.patch('/{employee_id}', summary="\u66f4\u65b0\u5458\u5de5\u4e3b\u6570\u636e", description="\u90e8\u5206\u66f4\u65b0\u6307\u5b9a\u5458\u5de5\u7684\u4e3b\u6570\u636e\u5b57\u6bb5\u3002")
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


@router.post('/{employee_id}/status', summary="\u66f4\u65b0\u5458\u5de5\u72b6\u6001", description="\u542f\u7528\u6216\u7981\u7528\u6307\u5b9a\u5458\u5de5\u3002")
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


@router.delete('/{employee_id}', status_code=status.HTTP_204_NO_CONTENT, summary="\u5220\u9664\u5458\u5de5\u4e3b\u6570\u636e", description="\u5220\u9664\u6307\u5b9a\u5458\u5de5\u7684\u4e3b\u6570\u636e\u8bb0\u5f55\u3002")
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


@router.get('/{employee_id}/audits', summary="\u67e5\u8be2\u5458\u5de5\u53d8\u66f4\u5386\u53f2", description="\u83b7\u53d6\u6307\u5b9a\u5458\u5de5\u7684\u4e3b\u6570\u636e\u53d8\u66f4\u5386\u53f2\u3002")
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


@router.delete('/{employee_id}/audits/{audit_id}', status_code=status.HTTP_204_NO_CONTENT, summary="\u5220\u9664\u5458\u5de5\u53d8\u66f4\u8bb0\u5f55", description="\u5220\u9664\u6307\u5b9a\u5458\u5de5\u7684\u67d0\u6761\u53d8\u66f4\u5386\u53f2\u8bb0\u5f55\u3002")
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
