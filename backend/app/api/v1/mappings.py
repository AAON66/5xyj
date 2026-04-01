from __future__ import annotations

from typing import Optional

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

# Error code prefix: MAP_xxx
router = APIRouter(prefix='/mappings', tags=['\u5bfc\u5165\u5bfc\u51fa'])


@router.get('', summary="\u67e5\u8be2\u8868\u5934\u6620\u5c04", description="\u67e5\u8be2\u8868\u5934\u5b57\u6bb5\u6620\u5c04\u5173\u7cfb\uff0c\u652f\u6301\u6309\u6279\u6b21\u548c\u6e90\u6587\u4ef6\u7b5b\u9009\u3002")
def list_header_mappings_endpoint(
    batch_id: Optional[str] = Query(default=None),
    source_file_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    payload = list_header_mappings(db, batch_id=batch_id, source_file_id=source_file_id)
    return success_response(payload.model_dump(mode='json'), message='Header mappings retrieved.')


@router.patch('/{mapping_id}', summary="\u66f4\u65b0\u8868\u5934\u6620\u5c04", description="\u624b\u52a8\u4fee\u6539\u67d0\u4e2a\u8868\u5934\u5b57\u6bb5\u7684\u6807\u51c6\u5b57\u6bb5\u6620\u5c04\u3002")
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
