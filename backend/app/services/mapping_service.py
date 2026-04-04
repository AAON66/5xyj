from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session, joinedload

from backend.app.mappings import CANONICAL_FIELDS
from backend.app.models import HeaderMapping, SourceFile
from backend.app.models.enums import MappingSource
from backend.app.schemas.mappings import HeaderMappingListRead, HeaderMappingRead
from backend.app.services.audit_service import log_audit


class HeaderMappingNotFoundError(Exception):
    pass


class InvalidCanonicalFieldError(Exception):
    pass


def list_header_mappings(
    db: Session,
    *,
    batch_id: Optional[str] = None,
    source_file_id: Optional[str] = None,
    mapping_source: Optional[str] = None,
    confidence_min: Optional[float] = None,
    confidence_max: Optional[float] = None,
) -> HeaderMappingListRead:
    query = (
        db.query(HeaderMapping)
        .options(joinedload(HeaderMapping.source_file).joinedload(SourceFile.batch))
        .join(HeaderMapping.source_file)
    )
    if batch_id:
        query = query.filter(SourceFile.batch_id == batch_id)
    if source_file_id:
        query = query.filter(SourceFile.id == source_file_id)
    if mapping_source:
        query = query.filter(HeaderMapping.mapping_source == mapping_source)
    if confidence_min is not None:
        query = query.filter(HeaderMapping.confidence >= confidence_min)
    if confidence_max is not None:
        query = query.filter(HeaderMapping.confidence <= confidence_max)

    mappings = query.order_by(HeaderMapping.created_at.asc(), HeaderMapping.raw_header_signature.asc()).all()
    return HeaderMappingListRead(
        items=[_to_schema(mapping) for mapping in mappings],
        available_canonical_fields=sorted(CANONICAL_FIELDS),
    )


def update_header_mapping(
    db: Session,
    mapping_id: str,
    canonical_field: Optional[str],
    actor_username: str = "system",
    actor_role: str = "admin",
) -> HeaderMappingRead:
    if canonical_field is not None and canonical_field not in CANONICAL_FIELDS:
        raise InvalidCanonicalFieldError(f"Canonical field '{canonical_field}' is not supported.")

    mapping = (
        db.query(HeaderMapping)
        .options(joinedload(HeaderMapping.source_file).joinedload(SourceFile.batch))
        .filter(HeaderMapping.id == mapping_id)
        .first()
    )
    if mapping is None:
        raise HeaderMappingNotFoundError(f"Header mapping '{mapping_id}' was not found.")

    old_canonical_field = mapping.canonical_field

    mapping.canonical_field = canonical_field
    mapping.mapping_source = MappingSource.MANUAL
    mapping.manually_overridden = True
    mapping.confidence = 1.0 if canonical_field else None

    candidate_fields = list(mapping.candidate_fields or [])
    if canonical_field and canonical_field not in candidate_fields:
        candidate_fields.insert(0, canonical_field)
    mapping.candidate_fields = candidate_fields

    db.commit()
    db.refresh(mapping)

    log_audit(
        db,
        action="mapping_override",
        actor_username=actor_username,
        actor_role=actor_role,
        detail={
            "mapping_id": mapping_id,
            "raw_header": mapping.raw_header,
            "old_canonical_field": old_canonical_field,
            "new_canonical_field": canonical_field,
        },
        resource_type="header_mapping",
        resource_id=mapping_id,
    )

    return _to_schema(mapping)


def _to_schema(mapping: HeaderMapping) -> HeaderMappingRead:
    source_file = mapping.source_file
    batch = source_file.batch
    return HeaderMappingRead(
        id=mapping.id,
        batch_id=batch.id,
        batch_name=batch.batch_name,
        source_file_id=source_file.id,
        source_file_name=source_file.file_name,
        raw_header=mapping.raw_header,
        raw_header_signature=mapping.raw_header_signature,
        canonical_field=mapping.canonical_field,
        mapping_source=mapping.mapping_source.value if hasattr(mapping.mapping_source, 'value') else str(mapping.mapping_source),
        confidence=mapping.confidence,
        candidate_fields=list(mapping.candidate_fields or []),
        manually_overridden=mapping.manually_overridden,
    )
