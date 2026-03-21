from __future__ import annotations

import json
from datetime import datetime, timezone
from json import JSONDecodeError
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import success_response
from backend.app.dependencies import get_db
from backend.app.models.enums import TemplateType
from backend.app.schemas.imports import ImportBatchDetailRead
from backend.app.services import ExportBlockedError, export_batch, get_batch_export, get_batch_match, get_batch_validation, match_batch, validate_batch
from backend.app.services.import_service import (
    BatchNotFoundError,
    InvalidUploadError,
    create_import_batch,
    get_import_batch,
    list_import_batches,
    parse_import_batch,
    preview_import_batch,
    serialize_import_batch,
)

router = APIRouter(prefix='/imports', tags=['imports'])


@router.post('', status_code=status.HTTP_201_CREATED)
async def create_import_batch_endpoint(
    request: Request,
    files: list[UploadFile] = File(...),
    batch_name: str | None = Form(None),
    regions: str | None = Form(None),
    company_names: str | None = Form(None),
    db: Session = Depends(get_db),
):
    settings = request.app.state.settings
    try:
        batch = await create_import_batch(
            db=db,
            settings=settings,
            files=files,
            batch_name=batch_name,
            regions=_parse_metadata_values(regions, 'regions'),
            company_names=_parse_metadata_values(company_names, 'company_names'),
        )
    except InvalidUploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    payload = serialize_import_batch(batch)
    return success_response(payload.model_dump(mode='json'), message='Import batch created.', status_code=status.HTTP_201_CREATED)


@router.get('')
def list_import_batches_endpoint(db: Session = Depends(get_db)):
    batches = list_import_batches(db)
    return success_response([batch.model_dump(mode='json') for batch in batches], message='Import batches retrieved.')


@router.get('/{batch_id}')
def get_import_batch_endpoint(batch_id: str, db: Session = Depends(get_db)):
    try:
        batch = get_import_batch(db, batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    payload = ImportBatchDetailRead.model_validate(serialize_import_batch(batch))
    return success_response(payload.model_dump(mode='json'), message='Import batch retrieved.')


@router.post('/{batch_id}/parse')
def parse_import_batch_endpoint(batch_id: str, db: Session = Depends(get_db)):
    try:
        payload = parse_import_batch(db, batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Import batch parsed.')


@router.get('/{batch_id}/preview')
def preview_import_batch_endpoint(batch_id: str, db: Session = Depends(get_db)):
    try:
        payload = preview_import_batch(db, batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Import batch preview retrieved.')


@router.post('/{batch_id}/validate')
def validate_batch_endpoint(batch_id: str, db: Session = Depends(get_db)):
    try:
        payload = validate_batch(db, batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Batch validation completed.')


@router.get('/{batch_id}/validation')
def get_batch_validation_endpoint(batch_id: str, db: Session = Depends(get_db)):
    try:
        payload = get_batch_validation(db, batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Batch validation retrieved.')


@router.post('/{batch_id}/match')
def match_batch_endpoint(batch_id: str, db: Session = Depends(get_db)):
    try:
        payload = match_batch(db, batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Batch matching completed.')


@router.get('/{batch_id}/match')
def get_batch_match_endpoint(batch_id: str, db: Session = Depends(get_db)):
    try:
        payload = get_batch_match(db, batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Batch matching retrieved.')


@router.post('/{batch_id}/export')
def export_batch_endpoint(request: Request, batch_id: str, db: Session = Depends(get_db)):
    try:
        payload = export_batch(db, batch_id, request.app.state.settings)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ExportBlockedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Batch export completed.')


@router.get('/{batch_id}/export')
def get_batch_export_endpoint(batch_id: str, db: Session = Depends(get_db)):
    try:
        payload = get_batch_export(db, batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Batch export retrieved.')


@router.get('/{batch_id}/export/{template_type}/download')
def download_batch_export_artifact_endpoint(request: Request, batch_id: str, template_type: str, db: Session = Depends(get_db)):
    try:
        batch = get_import_batch(db, batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    artifact = _resolve_downloadable_artifact(batch, template_type)
    artifact_path = _resolve_downloadable_artifact_path(request.app.state.settings.outputs_path, artifact.file_path)
    return FileResponse(
        path=artifact_path,
        filename=artifact_path.name,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )


def _parse_metadata_values(raw_value: str | None, field_name: str) -> list[str] | None:
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
        raise InvalidUploadError(f"Field '{field_name}' must be a JSON array or a single string.") from exc

    if not isinstance(parsed, list) or not all(item is None or isinstance(item, str) for item in parsed):
        raise InvalidUploadError(f"Field '{field_name}' must be a JSON array of strings.")

    return [item or '' for item in parsed]


def _resolve_downloadable_artifact(batch, raw_template_type: str):
    try:
        template_type = TemplateType(raw_template_type)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown template type: {raw_template_type}.") from exc

    if not batch.export_jobs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No export artifact is available for this batch yet.')

    latest_job = max(
        batch.export_jobs,
        key=lambda item: (item.completed_at or item.created_at or datetime.min.replace(tzinfo=timezone.utc), item.created_at),
    )
    artifact = next((item for item in latest_job.artifacts if item.template_type == template_type), None)
    if artifact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='The requested export artifact was not found.')
    if artifact.status != 'completed' or not artifact.file_path:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='The requested export artifact is not ready for download.')
    return artifact


def _resolve_downloadable_artifact_path(outputs_root: Path, raw_path: str | None) -> Path:
    if not raw_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='The requested export artifact does not have a file path.')

    candidate = Path(raw_path)
    resolved = candidate.resolve() if candidate.is_absolute() else (outputs_root / candidate).resolve()
    allowed_root = outputs_root.resolve()
    if resolved != allowed_root and allowed_root not in resolved.parents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='The requested export artifact path is invalid.')
    if not resolved.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='The requested export artifact file no longer exists.')
    return resolved
