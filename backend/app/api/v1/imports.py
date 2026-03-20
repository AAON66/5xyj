from __future__ import annotations

import json
from json import JSONDecodeError

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import success_response
from backend.app.dependencies import get_db
from backend.app.schemas.imports import ImportBatchDetailRead
from backend.app.services.import_service import (
    BatchNotFoundError,
    InvalidUploadError,
    create_import_batch,
    get_import_batch,
    list_import_batches,
    serialize_import_batch,
)

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("", status_code=status.HTTP_201_CREATED)
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
            regions=_parse_metadata_values(regions, "regions"),
            company_names=_parse_metadata_values(company_names, "company_names"),
        )
    except InvalidUploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    payload = serialize_import_batch(batch)
    return success_response(payload.model_dump(mode="json"), message="Import batch created.", status_code=status.HTTP_201_CREATED)


@router.get("")
def list_import_batches_endpoint(db: Session = Depends(get_db)):
    batches = list_import_batches(db)
    return success_response([batch.model_dump(mode="json") for batch in batches], message="Import batches retrieved.")


@router.get("/{batch_id}")
def get_import_batch_endpoint(batch_id: str, db: Session = Depends(get_db)):
    try:
        batch = get_import_batch(db, batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    payload = ImportBatchDetailRead.model_validate(serialize_import_batch(batch))
    return success_response(payload.model_dump(mode="json"), message="Import batch retrieved.")


def _parse_metadata_values(raw_value: str | None, field_name: str) -> list[str] | None:
    if raw_value is None:
        return None

    stripped = raw_value.strip()
    if not stripped:
        return None

    if not stripped.startswith("["):
        return [stripped]

    try:
        parsed = json.loads(stripped)
    except JSONDecodeError as exc:
        raise InvalidUploadError(f"Field '{field_name}' must be a JSON array or a single string.") from exc

    if not isinstance(parsed, list) or not all(item is None or isinstance(item, str) for item in parsed):
        raise InvalidUploadError(f"Field '{field_name}' must be a JSON array of strings.")

    return [item or "" for item in parsed]