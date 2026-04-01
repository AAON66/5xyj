from __future__ import annotations

from typing import Optional

import json
from datetime import datetime, timezone
from json import JSONDecodeError
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from backend.app.api.v1.responses import success_response
from backend.app.core.auth import AuthUser
from backend.app.dependencies import get_db, require_authenticated_user
from backend.app.models.import_batch import ImportBatch
from backend.app.models.user import User
from backend.app.models.enums import TemplateType
from backend.app.schemas.imports import ImportBatchDetailRead
from backend.app.services import ExportBlockedError, export_batch, get_batch_export, get_batch_match, get_batch_validation, match_batch, validate_batch
from backend.app.services.import_service import (
    BatchNotFoundError,
    bulk_delete_import_batches,
    delete_import_batch,
    InvalidUploadError,
    SourceFileNotFoundError,
    UploadTooLargeError,
    create_import_batch,
    get_import_batch,
    list_import_batches,
    parse_import_batch,
    preview_import_batch,
    serialize_import_batch,
)
from backend.app.schemas.imports import DeleteImportBatchesInput

# Error code prefix: IMP_xxx
router = APIRouter(prefix='/imports', tags=['\u5bfc\u5165\u5bfc\u51fa'])


@router.post('', status_code=status.HTTP_201_CREATED, summary="\u521b\u5efa\u5bfc\u5165\u6279\u6b21", description="\u4e0a\u4f20 Excel \u6587\u4ef6\u521b\u5efa\u65b0\u7684\u5bfc\u5165\u6279\u6b21\u3002")
async def create_import_batch_endpoint(
    request: Request,
    files: list[UploadFile] = File(...),
    batch_name: Optional[str] = Form(None),
    regions: Optional[str] = Form(None),
    company_names: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    auth_user: AuthUser = Depends(require_authenticated_user),
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
    except UploadTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)) from exc
    except InvalidUploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    # Populate created_by from authenticated user
    user_id = db.query(User.id).filter(User.username == auth_user.username).scalar()
    if user_id:
        batch.created_by = user_id
        db.commit()
        db.refresh(batch)

    payload = serialize_import_batch(batch)
    return success_response(payload.model_dump(mode='json'), message='Import batch created.', status_code=status.HTTP_201_CREATED)


@router.get('', summary="\u67e5\u8be2\u5bfc\u5165\u6279\u6b21\u5217\u8868", description="\u8fd4\u56de\u6240\u6709\u5bfc\u5165\u6279\u6b21\uff0c\u6309\u521b\u5efa\u65f6\u95f4\u5012\u5e8f\u6392\u5217\u3002")
def list_import_batches_endpoint(db: Session = Depends(get_db)):
    batches = list_import_batches(db)
    # Enrich with created_by_name using joinedload to avoid N+1
    batch_models = (
        db.query(ImportBatch)
        .options(joinedload(ImportBatch.creator))
        .order_by(ImportBatch.created_at.desc())
        .all()
    )
    creator_map = {
        b.id: b.creator.display_name if b.creator else None
        for b in batch_models
    }
    result = []
    for batch in batches:
        data = batch.model_dump(mode='json')
        data['created_by_name'] = creator_map.get(data['id'])
        result.append(data)
    return success_response(result, message='Import batches retrieved.')


@router.get('/{batch_id}', summary="\u83b7\u53d6\u6279\u6b21\u8be6\u60c5", description="\u83b7\u53d6\u6307\u5b9a\u5bfc\u5165\u6279\u6b21\u7684\u8be6\u7ec6\u4fe1\u606f\u3002")
def get_import_batch_endpoint(batch_id: str, db: Session = Depends(get_db)):
    try:
        batch = get_import_batch(db, batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    payload = ImportBatchDetailRead.model_validate(serialize_import_batch(batch))
    return success_response(payload.model_dump(mode='json'), message='Import batch retrieved.')


@router.delete('/{batch_id}', status_code=status.HTTP_204_NO_CONTENT, summary="\u5220\u9664\u5bfc\u5165\u6279\u6b21", description="\u5220\u9664\u6307\u5b9a\u5bfc\u5165\u6279\u6b21\u53ca\u5176\u6240\u6709\u5173\u8054\u6570\u636e\u3002")
def delete_import_batch_endpoint(
    request: Request,
    batch_id: str,
    db: Session = Depends(get_db),
) -> Response:
    try:
        delete_import_batch(db, request.app.state.settings, batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post('/bulk-delete', summary="\u6279\u91cf\u5220\u9664\u5bfc\u5165\u6279\u6b21", description="\u6279\u91cf\u5220\u9664\u591a\u4e2a\u5bfc\u5165\u6279\u6b21\u3002")
def bulk_delete_import_batches_endpoint(
    request: Request,
    payload: DeleteImportBatchesInput,
    db: Session = Depends(get_db),
):
    result = bulk_delete_import_batches(db, request.app.state.settings, payload.batch_ids)
    return success_response(result.model_dump(mode='json'), message='Import batches deleted.')


@router.post('/{batch_id}/parse', summary="\u89e3\u6790\u6279\u6b21\u6587\u4ef6", description="\u89e3\u6790\u6279\u6b21\u4e2d\u7684\u6240\u6709\u6e90\u6587\u4ef6\uff0c\u8bc6\u522b\u8868\u5934\u5e76\u5f52\u4e00\u5316\u5b57\u6bb5\u3002")
def parse_import_batch_endpoint(batch_id: str, db: Session = Depends(get_db)):
    try:
        payload = parse_import_batch(db, batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Import batch parsed.')


@router.get('/{batch_id}/preview', summary="\u9884\u89c8\u6279\u6b21\u6570\u636e", description="\u9884\u89c8\u6279\u6b21\u89e3\u6790\u540e\u7684\u6570\u636e\uff0c\u53ef\u6307\u5b9a\u6e90\u6587\u4ef6\u3002")
def preview_import_batch_endpoint(batch_id: str, source_file_id: Optional[str] = None, db: Session = Depends(get_db)):
    try:
        payload = preview_import_batch(db, batch_id, source_file_id=source_file_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SourceFileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Import batch preview retrieved.')


@router.post('/{batch_id}/validate', summary="\u6821\u9a8c\u6279\u6b21\u6570\u636e", description="\u5bf9\u6279\u6b21\u6570\u636e\u6267\u884c\u6821\u9a8c\uff0c\u68c0\u67e5\u7f3a\u5931\u3001\u5f02\u5e38\u3001\u91cd\u590d\u7b49\u95ee\u9898\u3002")
def validate_batch_endpoint(batch_id: str, db: Session = Depends(get_db)):
    try:
        payload = validate_batch(db, batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Batch validation completed.')


@router.get('/{batch_id}/validation', summary="\u83b7\u53d6\u6821\u9a8c\u7ed3\u679c", description="\u83b7\u53d6\u6279\u6b21\u6700\u8fd1\u4e00\u6b21\u6821\u9a8c\u7684\u7ed3\u679c\u3002")
def get_batch_validation_endpoint(batch_id: str, db: Session = Depends(get_db)):
    try:
        payload = get_batch_validation(db, batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Batch validation retrieved.')


@router.post('/{batch_id}/match', summary="\u6267\u884c\u5de5\u53f7\u5339\u914d", description="\u5bf9\u6279\u6b21\u6570\u636e\u6267\u884c\u5458\u5de5\u5de5\u53f7\u5339\u914d\u3002")
def match_batch_endpoint(batch_id: str, db: Session = Depends(get_db)):
    try:
        payload = match_batch(db, batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Batch matching completed.')


@router.get('/{batch_id}/match', summary="\u83b7\u53d6\u5339\u914d\u7ed3\u679c", description="\u83b7\u53d6\u6279\u6b21\u6700\u8fd1\u4e00\u6b21\u5de5\u53f7\u5339\u914d\u7684\u7ed3\u679c\u3002")
def get_batch_match_endpoint(batch_id: str, db: Session = Depends(get_db)):
    try:
        payload = get_batch_match(db, batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Batch matching retrieved.')


@router.post('/{batch_id}/export', summary="\u6267\u884c\u6279\u6b21\u5bfc\u51fa", description="\u5bfc\u51fa\u6279\u6b21\u6570\u636e\u4e3a\u53cc\u6a21\u677f Excel \u6587\u4ef6\u3002")
def export_batch_endpoint(request: Request, batch_id: str, db: Session = Depends(get_db)):
    try:
        payload = export_batch(db, batch_id, request.app.state.settings)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ExportBlockedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Batch export completed.')


@router.get('/{batch_id}/export', summary="\u83b7\u53d6\u5bfc\u51fa\u7ed3\u679c", description="\u83b7\u53d6\u6279\u6b21\u6700\u8fd1\u4e00\u6b21\u5bfc\u51fa\u7684\u72b6\u6001\u548c\u4ea7\u7269\u4fe1\u606f\u3002")
def get_batch_export_endpoint(batch_id: str, db: Session = Depends(get_db)):
    try:
        payload = get_batch_export(db, batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Batch export retrieved.')


@router.get('/{batch_id}/export/{template_type}/download', summary="\u4e0b\u8f7d\u5bfc\u51fa\u6587\u4ef6", description="\u4e0b\u8f7d\u6307\u5b9a\u6a21\u677f\u7c7b\u578b\u7684\u5bfc\u51fa Excel \u6587\u4ef6\u3002")
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


def _parse_metadata_values(raw_value: Optional[str], field_name: str) -> Optional[list[str]]:
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


def _resolve_downloadable_artifact_path(outputs_root: Path, raw_path: Optional[str]) -> Path:
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
