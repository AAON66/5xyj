from __future__ import annotations

import json
from json import JSONDecodeError

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import success_response
from backend.app.dependencies import get_db
from backend.app.services.aggregate_service import run_simple_aggregate
from backend.app.services.employee_service import EmployeeImportError
from backend.app.services.import_service import InvalidUploadError

router = APIRouter(prefix='/aggregate', tags=['aggregate'])


@router.post('', status_code=status.HTTP_201_CREATED)
async def run_simple_aggregate_endpoint(
    request: Request,
    files: list[UploadFile] = File(...),
    employee_master_file: UploadFile | None = File(default=None),
    batch_name: str | None = Form(default=None),
    regions: str | None = Form(default=None),
    company_names: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    try:
        payload = await run_simple_aggregate(
            db,
            request.app.state.settings,
            files=files,
            employee_master_file=employee_master_file,
            batch_name=batch_name,
            regions=_parse_metadata_values(regions),
            company_names=_parse_metadata_values(company_names),
        )
    except (InvalidUploadError, EmployeeImportError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Aggregate run completed.', status_code=status.HTTP_201_CREATED)


def _parse_metadata_values(raw_value: str | None) -> list[str] | None:
    if raw_value is None:
        return None
    stripped = raw_value.strip()
    if not stripped:
        return None
    if not stripped.startswith('['):
        return [stripped]
    try:
        parsed = json.loads(stripped)
    except JSONDecodeError as exc:
        raise InvalidUploadError('Metadata fields must be a JSON array or a single string.') from exc
    if not isinstance(parsed, list) or not all(item is None or isinstance(item, str) for item in parsed):
        raise InvalidUploadError('Metadata fields must be a JSON array of strings.')
    return [item or '' for item in parsed]
