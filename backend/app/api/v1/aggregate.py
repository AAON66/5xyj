from __future__ import annotations

import asyncio
import json
from contextlib import suppress
from io import BytesIO
from json import JSONDecodeError

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import StreamingResponse
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
    files: list[UploadFile] = File(default=[]),
    housing_fund_files: list[UploadFile] = File(default=[]),
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
            housing_fund_files=housing_fund_files,
            employee_master_file=employee_master_file,
            batch_name=batch_name,
            regions=_parse_metadata_values(regions),
            company_names=_parse_metadata_values(company_names),
        )
    except (InvalidUploadError, EmployeeImportError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Aggregate run completed.', status_code=status.HTTP_201_CREATED)


@router.post('/stream')
async def run_simple_aggregate_stream_endpoint(
    request: Request,
    files: list[UploadFile] = File(default=[]),
    housing_fund_files: list[UploadFile] = File(default=[]),
    employee_master_file: UploadFile | None = File(default=None),
    batch_name: str | None = Form(default=None),
    regions: str | None = Form(default=None),
    company_names: str | None = Form(default=None),
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
                    batch_name=batch_name,
                    regions=parsed_regions,
                    company_names=parsed_companies,
                    progress_callback=emit_progress,
                )
            except (InvalidUploadError, EmployeeImportError, ValueError) as exc:
                await queue.put({'event': 'error', 'code': 'bad_request', 'message': str(exc)})
            except Exception:
                await queue.put(
                    {
                        'event': 'error',
                        'code': 'internal_server_error',
                        'message': 'An unexpected server error occurred.',
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
