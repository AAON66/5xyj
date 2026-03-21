from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.models import HeaderMapping, ImportBatch, SourceFile
from backend.app.models.enums import BatchStatus, MappingSource, SourceFileKind
from backend.app.parsers import HeaderExtraction, extract_header_structure
from backend.app.schemas.imports import (
    FilteredRowPreviewRead,
    HeaderMappingPreviewRead,
    ImportBatchDetailRead,
    ImportBatchPreviewRead,
    ImportBatchSummaryRead,
    NormalizedPreviewRecordRead,
    SourceFilePreviewRead,
    SourceFileRead,
)
from backend.app.services.header_normalizer import HeaderMappingDecision, HeaderNormalizationResult, normalize_header_extraction
from backend.app.services.housing_fund_service import analyze_housing_fund_workbook
from backend.app.services.normalization_service import StandardizationResult, standardize_workbook

ALLOWED_EXTENSIONS = {'.xlsx', '.xls'}
ALLOWED_SOURCE_KINDS = {item.value for item in SourceFileKind}


class ImportServiceError(Exception):
    pass


class InvalidUploadError(ImportServiceError):
    pass


class BatchNotFoundError(ImportServiceError):
    pass


@dataclass
class StoredUpload:
    original_name: str
    storage_path: Path
    file_size: int
    file_hash: str


@dataclass
class AnalyzedSourceFile:
    normalization: HeaderNormalizationResult
    standardized: StandardizationResult


async def create_import_batch(
    db: Session,
    settings: Settings,
    files: list[UploadFile],
    batch_name: str | None = None,
    regions: list[str] | None = None,
    company_names: list[str] | None = None,
    file_kinds: list[str] | None = None,
) -> ImportBatch:
    if not files:
        raise InvalidUploadError('At least one Excel file is required.')

    runtime_regions = _normalize_metadata_list(regions, len(files), 'regions')
    runtime_companies = _normalize_metadata_list(company_names, len(files), 'company_names')
    runtime_file_kinds = _normalize_file_kinds(file_kinds, len(files))

    batch = ImportBatch(batch_name=(batch_name or _build_batch_name()).strip(), status=BatchStatus.UPLOADED)
    db.add(batch)
    db.flush()

    batch_dir = settings.upload_path / batch.id
    batch_dir.mkdir(parents=True, exist_ok=True)

    stored_paths: list[Path] = []
    try:
        for index, upload in enumerate(files):
            stored = await _store_upload(batch_dir, upload)
            stored_paths.append(stored.storage_path)
            source_file = SourceFile(
                batch_id=batch.id,
                file_name=stored.original_name,
                file_path=str(stored.storage_path),
                file_size=stored.file_size,
                source_kind=runtime_file_kinds[index],
                region=runtime_regions[index],
                company_name=runtime_companies[index],
                file_hash=stored.file_hash,
            )
            db.add(source_file)

        db.commit()
    except Exception:
        db.rollback()
        for path in stored_paths:
            if path.exists():
                path.unlink()
        if batch_dir.exists() and not any(batch_dir.iterdir()):
            shutil.rmtree(batch_dir)
        raise

    return get_import_batch(db, batch.id)


def list_import_batches(db: Session) -> list[ImportBatchSummaryRead]:
    batches = db.query(ImportBatch).order_by(ImportBatch.created_at.desc()).all()
    return [_to_summary_schema(batch) for batch in batches]


def get_import_batch(db: Session, batch_id: str) -> ImportBatch:
    batch = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
    if batch is None:
        raise BatchNotFoundError(f"Import batch '{batch_id}' was not found.")
    return batch


def preview_import_batch(db: Session, batch_id: str) -> ImportBatchPreviewRead:
    batch = get_import_batch(db, batch_id)
    file_previews = [_build_source_file_preview(source_file) for source_file in batch.source_files]
    return ImportBatchPreviewRead(
        batch_id=batch.id,
        batch_name=batch.batch_name,
        status=batch.status.value,
        source_files=file_previews,
    )


def parse_import_batch(db: Session, batch_id: str) -> ImportBatchPreviewRead:
    batch = get_import_batch(db, batch_id)
    batch.status = BatchStatus.PARSING
    db.flush()

    try:
        file_previews = []
        for source_file in batch.source_files:
            analyzed = analyze_source_file(source_file)
            _persist_source_file_mappings(db, source_file, analyzed.normalization.decisions)
            file_preview = _build_source_file_preview_from_analysis(source_file, analyzed)
            file_previews.append(file_preview)
            source_file.raw_sheet_name = analyzed.standardized.sheet_name
        batch.status = BatchStatus.NORMALIZED
        db.commit()
    except Exception:
        batch.status = BatchStatus.FAILED
        db.commit()
        raise

    db.refresh(batch)
    return ImportBatchPreviewRead(
        batch_id=batch.id,
        batch_name=batch.batch_name,
        status=batch.status.value,
        source_files=file_previews,
    )


def serialize_import_batch(batch: ImportBatch) -> ImportBatchDetailRead:
    return ImportBatchDetailRead(
        id=batch.id,
        batch_name=batch.batch_name,
        status=batch.status.value,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
        file_count=len(batch.source_files),
        source_files=[
            SourceFileRead(
                id=source_file.id,
                file_name=source_file.file_name,
                file_path=source_file.file_path,
                file_size=source_file.file_size,
                source_kind=source_file.source_kind,
                region=source_file.region,
                company_name=source_file.company_name,
                file_hash=source_file.file_hash,
                uploaded_at=source_file.uploaded_at,
            )
            for source_file in batch.source_files
        ],
    )


def analyze_source_file(source_file: SourceFile) -> AnalyzedSourceFile:
    workbook_path = Path(source_file.file_path)
    if source_file.source_kind == SourceFileKind.HOUSING_FUND.value:
        housing_analysis = analyze_housing_fund_workbook(
            workbook_path,
            region=source_file.region,
            company_name=source_file.company_name,
            source_file_name=source_file.file_name,
        )
        return AnalyzedSourceFile(
            normalization=housing_analysis.normalization,
            standardized=housing_analysis.standardized,
        )

    extraction = extract_header_structure(workbook_path)
    base_normalization = normalize_header_extraction(extraction, region=source_file.region)
    normalization = _apply_manual_mapping_overrides(base_normalization, source_file.header_mappings)
    standardized = standardize_workbook(
        workbook_path,
        region=source_file.region,
        company_name=source_file.company_name,
        source_file_name=source_file.file_name,
        extraction=extraction,
        normalization=normalization,
    )
    return AnalyzedSourceFile(normalization=normalization, standardized=standardized)


def _build_source_file_preview(source_file: SourceFile) -> SourceFilePreviewRead:
    return _build_source_file_preview_from_analysis(source_file, analyze_source_file(source_file))


def _build_source_file_preview_from_analysis(
    source_file: SourceFile,
    analysis: AnalyzedSourceFile,
) -> SourceFilePreviewRead:
    standardized = analysis.standardized
    normalization = analysis.normalization
    return SourceFilePreviewRead(
        source_file_id=source_file.id,
        file_name=source_file.file_name,
        source_kind=source_file.source_kind,
        region=source_file.region,
        company_name=source_file.company_name,
        raw_sheet_name=standardized.sheet_name,
        raw_header_signature=standardized.raw_header_signature,
        normalized_record_count=len(standardized.records),
        filtered_row_count=len(standardized.filtered_rows),
        unmapped_headers=standardized.unmapped_headers,
        header_mappings=[
            HeaderMappingPreviewRead(
                raw_header=decision.raw_header,
                raw_header_signature=decision.raw_header_signature,
                canonical_field=decision.canonical_field,
                mapping_source=decision.mapping_source,
                confidence=decision.confidence,
                candidate_fields=decision.candidate_fields,
                matched_rules=decision.matched_rules,
                llm_attempted=decision.llm_attempted,
                llm_status=decision.llm_status,
                rule_overrode_llm=decision.rule_overrode_llm,
            )
            for decision in normalization.decisions
        ],
        filtered_rows=[
            FilteredRowPreviewRead(
                row_number=row.row_number,
                reason=row.reason,
                first_value=row.first_value,
            )
            for row in standardized.filtered_rows
        ],
        preview_records=[
            NormalizedPreviewRecordRead(
                source_row_number=record.source_row_number,
                values=_json_safe_dict(record.values),
                unmapped_values=_json_safe_dict(record.unmapped_values),
                raw_values=_json_safe_dict(record.raw_values),
                raw_payload=_json_safe_dict(record.raw_payload),
            )
            for record in standardized.records[:20]
        ],
    )


def _apply_manual_mapping_overrides(
    normalization: HeaderNormalizationResult,
    persisted_mappings: list[HeaderMapping],
) -> HeaderNormalizationResult:
    manual_by_signature = {
        mapping.raw_header_signature: mapping
        for mapping in persisted_mappings
        if mapping.manually_overridden
    }
    if not manual_by_signature:
        return normalization

    decisions: list[HeaderMappingDecision] = []
    for decision in normalization.decisions:
        manual_mapping = manual_by_signature.get(decision.raw_header_signature)
        if manual_mapping is None:
            decisions.append(decision)
            continue
        candidate_fields = list(manual_mapping.candidate_fields or decision.candidate_fields)
        if manual_mapping.canonical_field and manual_mapping.canonical_field not in candidate_fields:
            candidate_fields.insert(0, manual_mapping.canonical_field)
        decisions.append(
            HeaderMappingDecision(
                raw_header=decision.raw_header,
                raw_header_signature=decision.raw_header_signature,
                canonical_field=manual_mapping.canonical_field,
                mapping_source=MappingSource.MANUAL.value,
                confidence=manual_mapping.confidence,
                candidate_fields=candidate_fields,
                matched_rules=decision.matched_rules,
                llm_attempted=decision.llm_attempted,
                llm_status=decision.llm_status,
                rule_overrode_llm=decision.rule_overrode_llm,
            )
        )

    return HeaderNormalizationResult(
        source_file=normalization.source_file,
        sheet_name=normalization.sheet_name,
        raw_header_signature=normalization.raw_header_signature,
        decisions=decisions,
        unmapped_headers=[decision.raw_header_signature for decision in decisions if decision.canonical_field is None],
    )


def _persist_source_file_mappings(
    db: Session,
    source_file: SourceFile,
    decisions: list[HeaderMappingDecision],
) -> None:
    existing_by_signature = {mapping.raw_header_signature: mapping for mapping in source_file.header_mappings}
    seen_signatures: set[str] = set()

    for decision in decisions:
        seen_signatures.add(decision.raw_header_signature)
        mapping = existing_by_signature.get(decision.raw_header_signature)
        if mapping is None:
            mapping = HeaderMapping(source_file_id=source_file.id)
            db.add(mapping)
            source_file.header_mappings.append(mapping)

        mapping.raw_header = decision.raw_header
        mapping.raw_header_signature = decision.raw_header_signature
        mapping.canonical_field = decision.canonical_field
        mapping.mapping_source = (
            MappingSource(decision.mapping_source)
            if decision.mapping_source in {item.value for item in MappingSource}
            else MappingSource.RULE
        )
        mapping.confidence = decision.confidence
        mapping.manually_overridden = decision.mapping_source == MappingSource.MANUAL.value
        mapping.candidate_fields = decision.candidate_fields

    for signature, mapping in list(existing_by_signature.items()):
        if signature not in seen_signatures:
            db.delete(mapping)


def _to_summary_schema(batch: ImportBatch) -> ImportBatchSummaryRead:
    return ImportBatchSummaryRead(
        id=batch.id,
        batch_name=batch.batch_name,
        status=batch.status.value,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
        file_count=len(batch.source_files),
    )


def _build_batch_name() -> str:
    return f"import-batch-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def _normalize_metadata_list(values: list[str] | None, file_count: int, field_name: str) -> list[str | None]:
    if not values:
        return [None] * file_count

    normalized = [value.strip() if value and value.strip() else None for value in values]
    if len(normalized) == 1 and file_count > 1:
        return normalized * file_count
    if len(normalized) != file_count:
        raise InvalidUploadError(f"Field '{field_name}' must be empty, contain one value, or match the number of files.")
    return normalized


def _normalize_file_kinds(values: list[str] | None, file_count: int) -> list[str]:
    if not values:
        return [SourceFileKind.SOCIAL_SECURITY.value] * file_count
    normalized = [((value or '').strip() or SourceFileKind.SOCIAL_SECURITY.value) for value in values]
    if len(normalized) == 1 and file_count > 1:
        normalized = normalized * file_count
    if len(normalized) != file_count:
        raise InvalidUploadError("Field 'file_kinds' must be empty, contain one value, or match the number of files.")
    invalid = [value for value in normalized if value not in ALLOWED_SOURCE_KINDS]
    if invalid:
        raise InvalidUploadError(f"Unsupported source kinds: {', '.join(sorted(set(invalid)))}.")
    return normalized


async def _store_upload(batch_dir: Path, upload: UploadFile) -> StoredUpload:
    original_name = Path(upload.filename or 'upload.xlsx').name
    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise InvalidUploadError(f"Unsupported file type '{extension or 'unknown'}'. Only .xlsx and .xls are allowed.")

    payload = await upload.read()
    if not payload:
        raise InvalidUploadError(f"File '{original_name}' is empty.")

    stored_name = f'{uuid4().hex}{extension}'
    storage_path = batch_dir / stored_name
    storage_path.write_bytes(payload)

    return StoredUpload(
        original_name=original_name,
        storage_path=storage_path.resolve(),
        file_size=len(payload),
        file_hash=hashlib.sha256(payload).hexdigest(),
    )


def _json_safe_dict(values: dict[str, object | None]) -> dict[str, object | None]:
    normalized: dict[str, object | None] = {}
    for key, value in values.items():
        if isinstance(value, Decimal):
            normalized[key] = format(value, 'f')
        elif isinstance(value, dict):
            normalized[key] = _json_safe_dict(value)
        else:
            normalized[key] = value
    return normalized
