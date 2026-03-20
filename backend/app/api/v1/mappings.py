from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import success_response
from backend.app.dependencies import get_db
from backend.app.schemas.mappings import HeaderMappingUpdateRequest
from backend.app.services.mapping_service import (
    HeaderMappingNotFoundError,
    InvalidCanonicalFieldError,
    list_header_mappings,
    update_header_mapping,
)

router = APIRouter(prefix='/mappings', tags=['mappings'])


@router.get('')
def list_header_mappings_endpoint(
    batch_id: str | None = Query(default=None),
    source_file_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    payload = list_header_mappings(db, batch_id=batch_id, source_file_id=source_file_id)
    return success_response(payload.model_dump(mode='json'), message='Header mappings retrieved.')


@router.patch('/{mapping_id}')
def update_header_mapping_endpoint(
    mapping_id: str,
    body: HeaderMappingUpdateRequest,
    db: Session = Depends(get_db),
):
    try:
        payload = update_header_mapping(db, mapping_id, body.canonical_field)
    except HeaderMappingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidCanonicalFieldError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return success_response(payload.model_dump(mode='json'), message='Header mapping updated.')
