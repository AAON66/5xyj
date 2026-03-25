from __future__ import annotations

from typing import Optional

import hashlib
import inspect
import shutil
from collections.abc import Awaitable, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import re
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session, load_only, selectinload

from backend.app.core.config import Settings
from backend.app.models import ExportJob, HeaderMapping, ImportBatch, SourceFile
from backend.app.models.enums import BatchStatus, MappingSource, SourceFileKind
from backend.app.parsers import HeaderExtraction, extract_header_structure
from backend.app.schemas.imports import (
    DeleteImportBatchesRead,
    FilteredRowPreviewRead,
    HeaderMappingPreviewRead,
    ImportBatchDetailRead,
    ImportBatchPreviewRead,
    ImportBatchSummaryRead,
    NormalizedPreviewRecordRead,
    SourceFilePreviewRead,
    SourceFileRead,
)
from backend.app.services.header_normalizer import (
    HeaderMappingDecision,
    HeaderNormalizationResult,
    normalize_header_extraction_with_sync_fallback,
)
from backend.app.services.housing_fund_service import analyze_housing_fund_workbook
from backend.app.services.normalization_service import StandardizationResult, standardize_workbook
from backend.app.services.region_detection_service import detect_region_for_workbook, detect_region_from_filename

ALLOWED_EXTENSIONS = {'.xlsx', '.xls'}
ALLOWED_SOURCE_KINDS = {item.value for item in SourceFileKind}
LLM_FALLBACK_CONFIDENCE_THRESHOLD = 0.72
UPLOAD_CHUNK_SIZE = 1024 * 1024
MAX_PARSE_WORKERS = 5
DATE_PATTERN = re.compile(r'(20\d{2}\u5e74\d{1,2}\u6708|20\d{4}|\d{6})')
FILENAME_NOISE = (
    '\u793e\u4f1a\u4fdd\u9669\u8d39\u7533\u62a5\u4e2a\u4eba\u660e\u7ec6\u8868',
    '\u793e\u4fdd\u7f34\u8d39\u660e\u7ec6',
    '\u793e\u4fdd\u660e\u7ec6',
    '\u793e\u4fdd\u8d26\u5355',
    '\u793e\u4fdd\u53f0\u8d26',
    '\u516c\u79ef\u91d1\u8d26\u5355',
    '\u516c\u79ef\u91d1\u6c47\u7f34\u660e\u7ec6',
    '\u516c\u79ef\u91d1',
    '\u4f4f\u623f\u516c\u79ef\u91d1\u5355\u4f4d\u6c47\u7f34\u660e\u7ec6',
    '\u5355\u7b14\u7f34\u5b58\u6e05\u5355',
    '\u8d26\u5355',
    '\u660e\u7ec6',
    '\u53f0\u8d26',
    '\u8865\u7f34',
)
ImportProgressCallback = Callable[[dict[str, object]], Awaitable[None] | None]

REGION_LABELS = {
    'guangzhou': '\u5e7f\u5dde',
    'hangzhou': '\u676d\u5dde',
    'xiamen': '\u53a6\u95e8',
    'shenzhen': '\u6df1\u5733',
    'wuhan': '\u6b66\u6c49',
    'changsha': '\u957f\u6c99',
}



class ImportServiceError(Exception):
    pass


class InvalidUploadError(ImportServiceError):
    pass


class BatchNotFoundError(ImportServiceError):
    pass


class SourceFileNotFoundError(ImportServiceError):
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


@dataclass(frozen=True, slots=True)
class ManualMappingSnapshot:
    raw_header_signature: str
    canonical_field: Optional[str]
    confidence: Optional[float]
    candidate_fields: list[str]
    manually_overridden: bool


@dataclass(frozen=True, slots=True)
class SourceFileAnalysisContext:
    source_file_id: str
    file_name: str
    file_path: str
    source_kind: str
    region: Optional[str]
    company_name: Optional[str]
    file_index: int
    total_files: int
    worker_count: int
    manual_mappings: tuple[ManualMappingSnapshot, ...]


async def create_import_batch(
    db: Session,
    settings: Settings,
    files: list[UploadFile],
    batch_name: Optional[str] = None,
    regions: Optional[list[str]] = None,
    company_names: Optional[list[str]] = None,
    file_kinds: Optional[list[str]] = None,
    progress_callback: Optional[ImportProgressCallback] = None,
) -> ImportBatch:
    if not files:
        raise InvalidUploadError('At least one Excel file is required.')

    runtime_regions = _normalize_metadata_list(regions, len(files), 'regions')
    runtime_companies = _normalize_metadata_list(company_names, len(files), 'company_names')
    runtime_file_kinds = _normalize_file_kinds(file_kinds, len(files))

    batch = ImportBatch(batch_name=(batch_name or _build_batch_name()).strip(), status=BatchStatus.UPLOADED)
    db.add(batch)
    db.commit()
    db.refresh(batch)

    batch_dir = settings.upload_path / batch.id
    batch_dir.mkdir(parents=True, exist_ok=True)

    stored_paths: list[Path] = []
    pending_source_files: list[SourceFile] = []
    try:
        for index, upload in enumerate(files, start=1):
            file_name = Path(upload.filename or 'upload.xlsx').name
            await _notify_progress(
                progress_callback,
                {
                    'phase': 'uploading_started',
                    'current': index,
                    'total': len(files),
                    'file_name': file_name,
                    'batch_id': batch.id,
                    'batch_name': batch.batch_name,
                },
            )
            stored = await _store_upload(batch_dir, upload)
            stored_paths.append(stored.storage_path)
            await _notify_progress(
                progress_callback,
                {
                    'phase': 'uploading_saved',
                    'current': index,
                    'total': len(files),
                    'file_name': stored.original_name,
                    'batch_id': batch.id,
                    'batch_name': batch.batch_name,
                },
            )

            detected_region = runtime_regions[index - 1] or detect_region_from_filename(stored.original_name)
            if detected_region is None:
                await _notify_progress(
                    progress_callback,
                    {
                        'phase': 'region_detection',
                        'current': index,
                        'total': len(files),
                        'file_name': stored.original_name,
                        'batch_id': batch.id,
                        'batch_name': batch.batch_name,
                    },
                )
                detection = detect_region_for_workbook(
                    stored.storage_path,
                    filename=stored.original_name,
                    source_kind=runtime_file_kinds[index - 1],
                )
                detected_region = detection.region
            pending_source_files.append(
                SourceFile(
                    batch_id=batch.id,
                    file_name=stored.original_name,
                    file_path=str(stored.storage_path),
                    file_size=stored.file_size,
                    source_kind=runtime_file_kinds[index - 1],
                    region=detected_region,
                    company_name=runtime_companies[index - 1]
                    or _infer_company_name_from_filename(stored.original_name, detected_region),
                    file_hash=stored.file_hash,
                )
            )

        db.add_all(pending_source_files)
        db.commit()
    except Exception:
        db.rollback()
        for stored_path in stored_paths:
            if stored_path.exists():
                stored_path.unlink()
        if batch_dir.exists() and not any(batch_dir.iterdir()):
            shutil.rmtree(batch_dir)
        persisted_batch = db.query(ImportBatch).filter(ImportBatch.id == batch.id).first()
        if persisted_batch is not None:
            db.delete(persisted_batch)
            db.commit()
        raise

    return get_import_batch(db, batch.id)


def list_import_batches(db: Session) -> list[ImportBatchSummaryRead]:
    batches = (
        db.query(ImportBatch)
        .options(selectinload(ImportBatch.source_files).load_only(SourceFile.id))
        .order_by(ImportBatch.created_at.desc())
        .all()
    )
    return [_to_summary_schema(batch) for batch in batches]


def delete_import_batch(db: Session, settings: Settings, batch_id: str) -> None:
    batch = _get_import_batch_for_delete(db, batch_id)
    cleanup_paths = _collect_batch_cleanup_paths(batch, settings.outputs_path)
    db.delete(batch)
    db.commit()
    _cleanup_batch_artifacts(cleanup_paths, upload_batch_dir=settings.upload_path / batch_id)


def bulk_delete_import_batches(db: Session, settings: Settings, batch_ids: list[str]) -> DeleteImportBatchesRead:
    normalized_ids: list[str] = []
    seen_ids: set[str] = set()
    for raw_batch_id in batch_ids:
        cleaned = raw_batch_id.strip()
        if not cleaned or cleaned in seen_ids:
            continue
        seen_ids.add(cleaned)
        normalized_ids.append(cleaned)

    deleted_ids: list[str] = []
    missing_ids: list[str] = []
    for batch_id in normalized_ids:
        try:
            delete_import_batch(db, settings, batch_id)
        except BatchNotFoundError:
            missing_ids.append(batch_id)
            continue
        deleted_ids.append(batch_id)

    return DeleteImportBatchesRead(
        deleted_count=len(deleted_ids),
        deleted_ids=deleted_ids,
        missing_ids=missing_ids,
    )


def get_import_batch(db: Session, batch_id: str) -> ImportBatch:
    batch = (
        db.query(ImportBatch)
        .options(
            selectinload(ImportBatch.source_files).load_only(
                SourceFile.id,
                SourceFile.file_name,
                SourceFile.file_path,
                SourceFile.file_size,
                SourceFile.source_kind,
                SourceFile.region,
                SourceFile.company_name,
                SourceFile.file_hash,
                SourceFile.uploaded_at,
                SourceFile.raw_sheet_name,
            )
        )
        .filter(ImportBatch.id == batch_id)
        .first()
    )
    if batch is None:
        raise BatchNotFoundError(f"Import batch '{batch_id}' was not found.")
    return batch


def _get_import_batch_for_delete(db: Session, batch_id: str) -> ImportBatch:
    batch = (
        db.query(ImportBatch)
        .options(
            selectinload(ImportBatch.source_files).load_only(SourceFile.file_path),
            selectinload(ImportBatch.export_jobs).selectinload(ExportJob.artifacts),
        )
        .filter(ImportBatch.id == batch_id)
        .first()
    )
    if batch is None:
        raise BatchNotFoundError(f"Import batch '{batch_id}' was not found.")
    return batch


def preview_import_batch(db: Session, batch_id: str, *, source_file_id: Optional[str] = None) -> ImportBatchPreviewRead:
    batch = get_import_batch(db, batch_id)
    source_files = _resolve_preview_source_files(batch, source_file_id)
    file_previews = [_build_source_file_preview(source_file) for source_file in source_files]
    return ImportBatchPreviewRead(
        batch_id=batch.id,
        batch_name=batch.batch_name,
        status=batch.status.value,
        source_files=file_previews,
    )


def parse_import_batch(
    db: Session,
    batch_id: str,
    progress_callback: Optional[ImportProgressCallback] = None,
) -> ImportBatchPreviewRead:
    batch = get_import_batch(db, batch_id)
    batch.status = BatchStatus.PARSING
    db.commit()
    db.refresh(batch)

    try:
        source_files = list(batch.source_files)
        total_files = len(source_files)
        worker_count = _resolve_parse_worker_count(total_files)
        contexts = [
            _build_source_file_analysis_context(
                source_file,
                file_index=index,
                total_files=total_files,
                worker_count=worker_count,
            )
            for index, source_file in enumerate(source_files, start=1)
        ]
        source_files_by_id = {source_file.id: source_file for source_file in source_files}
        previews_by_id: dict[str, SourceFilePreviewRead] = {}
        contexts_by_id = {context.source_file_id: context for context in contexts}
        _emit_parse_queued_events(
            contexts,
            batch_id=batch.id,
            batch_name=batch.batch_name,
            progress_callback=progress_callback,
        )

        if worker_count == 1:
            for context in contexts:
                analyzed = _analyze_source_file_context(
                    context,
                    batch_id=batch.id,
                    batch_name=batch.batch_name,
                    progress_callback=progress_callback,
                )
                _persist_analyzed_source_file(
                    db,
                    source_file=source_files_by_id[context.source_file_id],
                    context=context,
                    analyzed=analyzed,
                    batch_id=batch.id,
                    batch_name=batch.batch_name,
                    previews_by_id=previews_by_id,
                    progress_callback=progress_callback,
                )
        else:
            with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix='batch-parse') as executor:
                futures = {
                    executor.submit(
                        _analyze_source_file_context,
                        context,
                        batch.id,
                        batch.batch_name,
                        progress_callback,
                    ): context.source_file_id
                    for context in contexts
                }
                for future in as_completed(futures):
                    source_file_id = futures[future]
                    context = contexts_by_id[source_file_id]
                    analyzed = future.result()
                    _persist_analyzed_source_file(
                        db,
                        source_file=source_files_by_id[source_file_id],
                        context=context,
                        analyzed=analyzed,
                        batch_id=batch.id,
                        batch_name=batch.batch_name,
                        previews_by_id=previews_by_id,
                        progress_callback=progress_callback,
                    )
        batch = get_import_batch(db, batch_id)
        batch.status = BatchStatus.NORMALIZED
        db.commit()
    except Exception:
        db.rollback()
        failed_batch = get_import_batch(db, batch_id)
        failed_batch.status = BatchStatus.FAILED
        db.commit()
        raise

    batch = get_import_batch(db, batch.id)
    return ImportBatchPreviewRead(
        batch_id=batch.id,
        batch_name=batch.batch_name,
        status=batch.status.value,
        source_files=[previews_by_id[context.source_file_id] for context in contexts],
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


def _collect_batch_cleanup_paths(batch: ImportBatch, outputs_root: Path) -> list[Path]:
    cleanup_paths: list[Path] = []
    for source_file in batch.source_files:
        file_path = Path(source_file.file_path)
        if file_path not in cleanup_paths:
            cleanup_paths.append(file_path)

    for export_job in batch.export_jobs:
        for artifact in export_job.artifacts:
            resolved = _resolve_export_artifact_cleanup_path(outputs_root, artifact.file_path)
            if resolved is not None and resolved not in cleanup_paths:
                cleanup_paths.append(resolved)
    return cleanup_paths


def _resolve_export_artifact_cleanup_path(outputs_root: Path, raw_path: Optional[str]) -> Optional[Path]:
    if not raw_path:
        return None

    candidate = Path(raw_path)
    resolved = candidate.resolve() if candidate.is_absolute() else (outputs_root / candidate).resolve()
    allowed_root = outputs_root.resolve()
    if resolved != allowed_root and allowed_root not in resolved.parents:
        return None
    return resolved


def _cleanup_batch_artifacts(cleanup_paths: list[Path], *, upload_batch_dir: Path) -> None:
    for path in cleanup_paths:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            continue

    if upload_batch_dir.exists():
        shutil.rmtree(upload_batch_dir, ignore_errors=True)


def _resolve_parse_worker_count(total_files: int) -> int:
    if total_files <= 1:
        return 1
    return min(MAX_PARSE_WORKERS, total_files)


def _build_source_file_analysis_context(
    source_file: SourceFile,
    *,
    file_index: int,
    total_files: int,
    worker_count: int,
) -> SourceFileAnalysisContext:
    manual_mappings = tuple(
        ManualMappingSnapshot(
            raw_header_signature=mapping.raw_header_signature,
            canonical_field=mapping.canonical_field,
            confidence=mapping.confidence,
            candidate_fields=list(mapping.candidate_fields or []),
            manually_overridden=bool(mapping.manually_overridden),
        )
        for mapping in source_file.header_mappings
    )
    return SourceFileAnalysisContext(
        source_file_id=source_file.id,
        file_name=source_file.file_name,
        file_path=source_file.file_path,
        source_kind=source_file.source_kind,
        region=source_file.region,
        company_name=source_file.company_name,
        file_index=file_index,
        total_files=total_files,
        worker_count=worker_count,
        manual_mappings=manual_mappings,
    )


def _build_parse_progress_payload(batch_id: str, batch_name: str, context: SourceFileAnalysisContext) -> dict[str, object]:
    return {
        'current': context.file_index,
        'file_index': context.file_index,
        'total': context.total_files,
        'file_name': context.file_name,
        'batch_id': batch_id,
        'batch_name': batch_name,
        'source_file_id': context.source_file_id,
        'source_kind': context.source_kind,
        'region': context.region,
        'company_name': context.company_name,
        'worker_count': context.worker_count,
    }


def _emit_parse_queued_events(
    contexts: list[SourceFileAnalysisContext],
    *,
    batch_id: str,
    batch_name: str,
    progress_callback: Optional[ImportProgressCallback],
) -> None:
    for context in contexts:
        _run_progress_callback(
            progress_callback,
            {
                **_build_parse_progress_payload(batch_id, batch_name, context),
                'phase': 'parse_queued',
            },
        )


def _persist_analyzed_source_file(
    db: Session,
    *,
    source_file: SourceFile,
    context: SourceFileAnalysisContext,
    analyzed: AnalyzedSourceFile,
    batch_id: str,
    batch_name: str,
    previews_by_id: dict[str, SourceFilePreviewRead],
    progress_callback: Optional[ImportProgressCallback],
) -> None:
    _persist_source_file_mappings(db, source_file, analyzed.normalization.decisions)
    source_file.raw_sheet_name = analyzed.standardized.sheet_name
    db.commit()
    previews_by_id[context.source_file_id] = _build_source_file_preview_from_analysis(source_file, analyzed)
    _run_progress_callback(
        progress_callback,
        {
            **_build_parse_progress_payload(batch_id, batch_name, context),
            'phase': 'parse_saved',
            'normalized_record_count': len(analyzed.standardized.records),
            'filtered_row_count': len(analyzed.standardized.filtered_rows),
            'unmapped_header_count': len(analyzed.standardized.unmapped_headers),
            'raw_sheet_name': analyzed.standardized.sheet_name,
        },
    )


def _analyze_source_file_context(
    context: SourceFileAnalysisContext,
    batch_id: str,
    batch_name: str,
    progress_callback: Optional[ImportProgressCallback] = None,
) -> AnalyzedSourceFile:
    progress_base_payload = _build_parse_progress_payload(batch_id, batch_name, context)
    _run_progress_callback(
        progress_callback,
        {
            **progress_base_payload,
            'phase': 'parse_started',
        },
    )
    analyzed = analyze_source_file_context(context)
    _run_progress_callback(
        progress_callback,
        {
            **progress_base_payload,
            'phase': 'parse_analyzed',
            'normalized_record_count': len(analyzed.standardized.records),
            'filtered_row_count': len(analyzed.standardized.filtered_rows),
            'unmapped_header_count': len(analyzed.standardized.unmapped_headers),
        },
    )
    return analyzed


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
    base_normalization = normalize_header_extraction_with_sync_fallback(
        extraction,
        region=source_file.region,
        confidence_threshold=LLM_FALLBACK_CONFIDENCE_THRESHOLD,
    )
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


def analyze_source_file_context(context: SourceFileAnalysisContext) -> AnalyzedSourceFile:
    workbook_path = Path(context.file_path)
    if context.source_kind == SourceFileKind.HOUSING_FUND.value:
        housing_analysis = analyze_housing_fund_workbook(
            workbook_path,
            region=context.region,
            company_name=context.company_name,
            source_file_name=context.file_name,
        )
        return AnalyzedSourceFile(
            normalization=housing_analysis.normalization,
            standardized=housing_analysis.standardized,
        )

    extraction = extract_header_structure(workbook_path)
    base_normalization = normalize_header_extraction_with_sync_fallback(
        extraction,
        region=context.region,
        confidence_threshold=LLM_FALLBACK_CONFIDENCE_THRESHOLD,
    )
    normalization = _apply_manual_mapping_overrides(base_normalization, list(context.manual_mappings))
    standardized = standardize_workbook(
        workbook_path,
        region=context.region,
        company_name=context.company_name,
        source_file_name=context.file_name,
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


def _resolve_preview_source_files(batch: ImportBatch, source_file_id: Optional[str]) -> list[SourceFile]:
    source_files = list(batch.source_files)
    if source_file_id is None:
        return source_files

    matched = next((source_file for source_file in source_files if source_file.id == source_file_id), None)
    if matched is None:
        raise SourceFileNotFoundError(
            f"Source file '{source_file_id}' was not found in import batch '{batch.id}'."
        )
    return [matched]


async def _notify_progress(
    progress_callback: Optional[ImportProgressCallback],
    payload: dict[str, object],
) -> None:
    if progress_callback is None:
        return
    result = progress_callback(payload)
    if inspect.isawaitable(result):
        await result


def _run_progress_callback(
    progress_callback: Optional[ImportProgressCallback],
    payload: dict[str, object],
) -> None:
    if progress_callback is None:
        return
    result = progress_callback(payload)
    if inspect.isawaitable(result):
        raise RuntimeError('Synchronous parse progress callback cannot be awaitable.')


def _build_batch_name() -> str:
    return f"import-batch-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def _infer_company_name_from_filename(filename: str, region: Optional[str]) -> Optional[str]:
    stem = Path(filename).stem
    if '--' in stem:
        tail = stem.split('--')[-1].strip()
        return tail or None

    cleaned = DATE_PATTERN.sub('', stem)
    cleaned = cleaned.replace('??1???2?', '')
    for noise in FILENAME_NOISE:
        cleaned = cleaned.replace(noise, '')
    if region:
        cleaned = cleaned.replace(REGION_LABELS.get(region, ''), '')
    cleaned = re.sub(r'[()??_\-\s]+', '', cleaned)
    return cleaned or (REGION_LABELS.get(region) if region else None)


def _normalize_metadata_list(values: Optional[list[str]], file_count: int, field_name: str) -> Optional[list[str]]:
    if not values:
        return [None] * file_count

    normalized = [value.strip() if value and value.strip() else None for value in values]
    if len(normalized) == 1 and file_count > 1:
        return normalized * file_count
    if len(normalized) != file_count:
        raise InvalidUploadError(f"Field '{field_name}' must be empty, contain one value, or match the number of files.")
    return normalized


def _normalize_file_kinds(values: Optional[list[str]], file_count: int) -> list[str]:
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

    stored_name = f'{uuid4().hex}{extension}'
    storage_path = batch_dir / stored_name
    file_size = 0
    hasher = hashlib.sha256()

    try:
        with storage_path.open('wb') as handle:
            while True:
                chunk = await upload.read(UPLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                handle.write(chunk)
                hasher.update(chunk)
                file_size += len(chunk)
    except Exception:
        if storage_path.exists():
            storage_path.unlink()
        raise

    if file_size == 0:
        if storage_path.exists():
            storage_path.unlink()
        raise InvalidUploadError(f"File '{original_name}' is empty.")

    return StoredUpload(
        original_name=original_name,
        storage_path=storage_path.resolve(),
        file_size=file_size,
        file_hash=hasher.hexdigest(),
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
