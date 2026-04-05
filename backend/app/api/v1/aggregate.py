from __future__ import annotations

from typing import Optional

import asyncio
import json
import logging
from contextlib import suppress
from io import BytesIO
from json import JSONDecodeError

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import success_response
from backend.app.core.auth import AuthUser
from backend.app.dependencies import get_db, require_authenticated_user
from backend.app.services.aggregate_service import run_simple_aggregate
from backend.app.services.audit_service import log_audit
from backend.app.utils.request_helpers import get_client_ip
from backend.app.services.employee_service import EmployeeImportError
from backend.app.services.import_service import InvalidUploadError, UploadTooLargeError

# Error code prefix: AGG_xxx
router = APIRouter(prefix='/aggregate', tags=['\u793e\u4fdd\u67e5\u8be2'])
logger = logging.getLogger(__name__)


@router.post('', status_code=status.HTTP_201_CREATED, summary="\u6267\u884c\u5feb\u901f\u878d\u5408", description="\u4e0a\u4f20\u591a\u5730\u533a\u793e\u4fdd/\u516c\u79ef\u91d1 Excel \u6587\u4ef6\uff0c\u6267\u884c\u89e3\u6790\u3001\u5f52\u4e00\u5316\u3001\u5de5\u53f7\u5339\u914d\u548c\u5bfc\u51fa\u3002")
async def run_simple_aggregate_endpoint(
    request: Request,
    files: list[UploadFile] = File(default=[]),
    housing_fund_files: list[UploadFile] = File(default=[]),
    employee_master_file: Optional[UploadFile] = File(default=None),
    employee_master_mode: Optional[str] = Form(default=None),
    batch_name: Optional[str] = Form(default=None),
    regions: Optional[str] = Form(default=None),
    company_names: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_authenticated_user),
):
    try:
        payload = await run_simple_aggregate(
            db,
            request.app.state.settings,
            files=files,
            housing_fund_files=housing_fund_files,
            employee_master_file=employee_master_file,
            employee_master_mode=employee_master_mode,
            batch_name=batch_name,
            regions=_parse_metadata_values(regions),
            company_names=_parse_metadata_values(company_names),
        )
    except UploadTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)) from exc
    except (InvalidUploadError, EmployeeImportError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    log_audit(db, action="aggregate", actor_username=user.username,
              actor_role=user.role, ip_address=get_client_ip(request),
              resource_type="batch", resource_id=batch_name or "unnamed",
              detail={"file_count": len(files), "batch_name": batch_name or ""},
              success=True)

    return success_response(payload.model_dump(mode='json'), message='Aggregate run completed.', status_code=status.HTTP_201_CREATED)


@router.post('/stream', summary="\u6d41\u5f0f\u878d\u5408\uff08NDJSON\uff09", description="\u4e0e\u666e\u901a\u878d\u5408\u76f8\u540c\uff0c\u4f46\u901a\u8fc7 NDJSON \u6d41\u5b9e\u65f6\u8fd4\u56de\u8fdb\u5ea6\u4fe1\u606f\u3002")
async def run_simple_aggregate_stream_endpoint(
    request: Request,
    files: list[UploadFile] = File(default=[]),
    housing_fund_files: list[UploadFile] = File(default=[]),
    employee_master_file: Optional[UploadFile] = File(default=None),
    employee_master_mode: Optional[str] = Form(default=None),
    batch_name: Optional[str] = Form(default=None),
    regions: Optional[str] = Form(default=None),
    company_names: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
):
    parsed_regions = _parse_metadata_values(regions)
    parsed_companies = _parse_metadata_values(company_names)
    file_payloads = [
        {
            'filename': upload.filename or 'upload.xlsx',
            'content_type': upload.content_type,
            'content': await upload.read(),
        }
        for upload in files
    ]
    housing_payloads = [
        {
            'filename': upload.filename or 'housing-fund.xlsx',
            'content_type': upload.content_type,
            'content': await upload.read(),
        }
        for upload in housing_fund_files
    ]
    employee_payload = None
    if employee_master_file is not None:
        employee_payload = {
            'filename': employee_master_file.filename or 'employee-master',
            'content_type': employee_master_file.content_type,
            'content': await employee_master_file.read(),
        }

    async def event_stream():
        queue: asyncio.Queue[dict[str, object] | None] = asyncio.Queue()

        def emit_progress(payload: dict[str, object]) -> None:
            queue.put_nowait({'event': 'progress', **payload})

        async def run_task() -> None:
            runtime_files = [
                UploadFile(filename=item['filename'], file=BytesIO(item['content']))
                for item in file_payloads
            ]
            runtime_housing = [
                UploadFile(filename=item['filename'], file=BytesIO(item['content']))
                for item in housing_payloads
            ]
            runtime_employee = None
            if employee_payload is not None:
                runtime_employee = UploadFile(
                    filename=employee_payload['filename'],
                    file=BytesIO(employee_payload['content']),
                )

            try:
                payload = await run_simple_aggregate(
                    db,
                    request.app.state.settings,
                    files=runtime_files,
                    housing_fund_files=runtime_housing,
                    employee_master_file=runtime_employee,
                    employee_master_mode=employee_master_mode,
                    batch_name=batch_name,
                    regions=parsed_regions,
                    company_names=parsed_companies,
                    progress_callback=emit_progress,
                )
            except UploadTooLargeError as exc:
                await queue.put({'event': 'error', 'code': 'payload_too_large', 'message': str(exc)})
            except (InvalidUploadError, EmployeeImportError, ValueError) as exc:
                await queue.put({'event': 'error', 'code': 'bad_request', 'message': str(exc)})
            except Exception as exc:
                logger.exception('Aggregate stream failed unexpectedly.')
                await queue.put(
                    {
                        'event': 'error',
                        'code': 'internal_server_error',
                        'message': str(exc) or 'An unexpected server error occurred.',
                    }
                )
            else:
                await queue.put({'event': 'result', 'data': payload.model_dump(mode='json')})
            finally:
                await queue.put(None)

        task = asyncio.create_task(run_task())
        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                yield json.dumps(item, ensure_ascii=False) + '\n'
        finally:
            if not task.done():
                task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    return StreamingResponse(event_stream(), media_type='application/x-ndjson')


def _parse_metadata_values(raw_value: Optional[str]) -> Optional[list[str]]:
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
