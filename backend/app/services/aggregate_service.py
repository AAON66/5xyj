from __future__ import annotations

import inspect
import re
from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.models import EmployeeMaster, MatchResult
from backend.app.models.enums import BatchStatus, SourceFileKind
from backend.app.schemas.aggregate import AggregateEmployeeImportRead, AggregateRunRead, AggregateSourceFileRead
from backend.app.schemas.imports import ExportArtifactRead
from backend.app.services.batch_export_service import export_batch
from backend.app.services.batch_runtime_service import match_batch, validate_batch
from backend.app.services.employee_service import import_employee_master_file
from backend.app.services.import_service import InvalidUploadError, create_import_batch, get_import_batch, parse_import_batch
from backend.app.services.matching_service import apply_match_results_to_normalized_records, build_match_result_models, match_preview_records
from backend.app.services.normalization_service import NormalizedPreviewRecord
from backend.app.services.region_detection_service import REGION_LABELS, detect_region_from_filename as detect_region_from_filename_by_rules

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

DATE_PATTERN = re.compile(r'(20\d{2}\u5e74\d{1,2}\u6708|20\d{4}|\d{6})')
ProgressCallback = Callable[[dict[str, object]], Awaitable[None] | None]


async def run_simple_aggregate(
    db: Session,
    settings: Settings,
    *,
    files: list[UploadFile],
    housing_fund_files: list[UploadFile] | None = None,
    employee_master_file: UploadFile | None = None,
    batch_name: str | None = None,
    regions: list[str] | None = None,
    company_names: list[str] | None = None,
    progress_callback: ProgressCallback | None = None,
) -> AggregateRunRead:
    all_files = [*files, *(housing_fund_files or [])]
    if not all_files:
        raise InvalidUploadError('At least one social security or housing fund file is required.')

    await _emit_progress(
        progress_callback,
        stage='employee_import',
        label='\u51c6\u5907\u5f00\u59cb',
        message='\u6b63\u5728\u51c6\u5907\u5feb\u901f\u805a\u5408\u4efb\u52a1\u3002',
        percent=5,
    )

    employee_summary: AggregateEmployeeImportRead | None = None
    if employee_master_file is not None and (employee_master_file.filename or '').strip():
        await _emit_progress(
            progress_callback,
            stage='employee_import',
            label='\u5bfc\u5165\u5458\u5de5\u4e3b\u6863',
            message='\u6b63\u5728\u5bfc\u5165\u5458\u5de5\u4e3b\u6863\u6587\u4ef6\u3002',
            percent=12,
        )
        employee_import = await import_employee_master_file(db, employee_master_file)
        employee_summary = AggregateEmployeeImportRead(
            file_name=employee_import.file_name,
            imported_count=employee_import.imported_count,
            created_count=employee_import.created_count,
            updated_count=employee_import.updated_count,
        )
        await _emit_progress(
            progress_callback,
            stage='employee_import',
            label='\u5458\u5de5\u4e3b\u6863\u5df2\u540c\u6b65',
            message=f'\u5df2\u5bfc\u5165 {employee_import.imported_count} \u6761\u5458\u5de5\u4e3b\u6863\u8bb0\u5f55\u3002',
            percent=18,
        )
    else:
        await _emit_progress(
            progress_callback,
            stage='employee_import',
            label='\u8df3\u8fc7\u5458\u5de5\u4e3b\u6863',
            message='\u672c\u6b21\u672a\u4e0a\u4f20\u5458\u5de5\u4e3b\u6863\uff0c\u5c06\u7ee7\u7eed\u805a\u5408\u5e76\u4fdd\u7559\u7a7a\u5de5\u53f7\u3002',
            percent=18,
        )

    resolved_regions = _resolve_metadata_values(all_files, regions, kind='region')
    resolved_companies = _resolve_metadata_values(all_files, company_names, kind='company')
    file_kinds = [
        *([SourceFileKind.SOCIAL_SECURITY.value] * len(files)),
        *([SourceFileKind.HOUSING_FUND.value] * len(housing_fund_files or [])),
    ]

    await _emit_progress(
        progress_callback,
        stage='batch_upload',
        label='\u4e0a\u4f20\u6279\u6b21',
        message='\u6b63\u5728\u521b\u5efa\u5bfc\u5165\u6279\u6b21\u5e76\u4fdd\u5b58\u793e\u4fdd\u3001\u516c\u79ef\u91d1\u6e90\u6587\u4ef6\u3002',
        percent=28,
    )
    batch = await create_import_batch(
        db=db,
        settings=settings,
        files=all_files,
        batch_name=batch_name,
        regions=resolved_regions,
        company_names=resolved_companies,
        file_kinds=file_kinds,
    )
    await _emit_progress(
        progress_callback,
        stage='batch_upload',
        label='\u6279\u6b21\u5df2\u521b\u5efa',
        message=f'\u6279\u6b21 {batch.batch_name} \u5df2\u521b\u5efa\uff0c\u5171 {len(batch.source_files)} \u4e2a\u6587\u4ef6\u3002',
        percent=36,
        batch_id=batch.id,
        batch_name=batch.batch_name,
    )

    await _emit_progress(
        progress_callback,
        stage='parse',
        label='\u89e3\u6790\u8bc6\u522b',
        message='\u6b63\u5728\u8bc6\u522b\u793e\u4fdd\u4e0e\u516c\u79ef\u91d1\u5de5\u4f5c\u8868\u3001\u8868\u5934\u548c\u6807\u51c6\u5b57\u6bb5\u3002',
        percent=48,
        batch_id=batch.id,
        batch_name=batch.batch_name,
    )
    preview = parse_import_batch(db, batch.id)
    await _emit_progress(
        progress_callback,
        stage='parse',
        label='\u89e3\u6790\u5b8c\u6210',
        message=f'\u5df2\u5b8c\u6210 {len(preview.source_files)} \u4e2a\u6587\u4ef6\u7684\u89e3\u6790\u3002',
        percent=60,
        batch_id=batch.id,
        batch_name=batch.batch_name,
    )

    await _emit_progress(
        progress_callback,
        stage='validate',
        label='\u6570\u636e\u6821\u9a8c',
        message='\u6b63\u5728\u6267\u884c\u7f3a\u5931\u3001\u91cd\u590d\u4e0e\u91d1\u989d\u6821\u9a8c\u3002',
        percent=68,
        batch_id=batch.id,
        batch_name=batch.batch_name,
    )
    validation = validate_batch(db, batch.id)
    await _emit_progress(
        progress_callback,
        stage='validate',
        label='\u6821\u9a8c\u5b8c\u6210',
        message=f'\u5171\u53d1\u73b0 {validation.total_issue_count} \u6761\u6821\u9a8c\u95ee\u9898\u3002',
        percent=76,
        batch_id=batch.id,
        batch_name=batch.batch_name,
    )

    await _emit_progress(
        progress_callback,
        stage='match',
        label='\u5de5\u53f7\u5339\u914d',
        message='\u6b63\u5728\u6839\u636e\u5458\u5de5\u4e3b\u6863\u6267\u884c\u5de5\u53f7\u5339\u914d\u3002',
        percent=84,
        batch_id=batch.id,
        batch_name=batch.batch_name,
    )
    match = _match_for_simple_aggregate(db, batch.id)
    await _emit_progress(
        progress_callback,
        stage='match',
        label='\u5339\u914d\u5b8c\u6210',
        message=f'\u5df2\u5339\u914d {match.matched_count} \u6761\uff0c\u672a\u5339\u914d {match.unmatched_count} \u6761\u3002',
        percent=90,
        batch_id=batch.id,
        batch_name=batch.batch_name,
    )

    await _emit_progress(
        progress_callback,
        stage='export',
        label='\u5bfc\u51fa\u53cc\u6a21\u677f',
        message='\u6b63\u5728\u751f\u6210\u85aa\u916c\u6a21\u677f\u548c\u5de5\u5177\u8868\u6700\u7ec8\u7248\u3002',
        percent=96,
        batch_id=batch.id,
        batch_name=batch.batch_name,
    )
    export = export_batch(db, batch.id, settings)

    result = AggregateRunRead(
        batch_id=batch.id,
        batch_name=batch.batch_name,
        status=export.status,
        export_status=export.export_status,
        blocked_reason=match.blocked_reason,
        employee_master=employee_summary,
        total_issue_count=validation.total_issue_count,
        matched_count=match.matched_count,
        unmatched_count=match.unmatched_count,
        duplicate_count=match.duplicate_count,
        low_confidence_count=match.low_confidence_count,
        source_files=[
            AggregateSourceFileRead(
                source_file_id=item.source_file_id,
                file_name=item.file_name,
                source_kind=item.source_kind,
                region=item.region,
                company_name=item.company_name,
                normalized_record_count=item.normalized_record_count,
                filtered_row_count=item.filtered_row_count,
            )
            for item in preview.source_files
        ],
        artifacts=[
            ExportArtifactRead(
                template_type=item.template_type,
                status=item.status,
                file_path=item.file_path,
                error_message=item.error_message,
                row_count=item.row_count,
            )
            for item in export.artifacts
        ],
    )
    await _emit_progress(
        progress_callback,
        stage='export',
        label='\u5bfc\u51fa\u5b8c\u6210',
        message='\u53cc\u6a21\u677f\u5bfc\u51fa\u6d41\u7a0b\u5df2\u7ed3\u675f\u3002',
        percent=100,
        batch_id=batch.id,
        batch_name=batch.batch_name,
    )
    return result


def _match_for_simple_aggregate(db: Session, batch_id: str):
    batch = get_import_batch(db, batch_id)
    employee_masters = list(
        db.query(EmployeeMaster).filter(EmployeeMaster.active.is_(True)).order_by(EmployeeMaster.employee_id.asc()).all()
    )
    if employee_masters:
        return match_batch(db, batch_id)

    db.query(MatchResult).filter(MatchResult.batch_id == batch.id).delete(synchronize_session=False)
    for record in batch.normalized_records:
        record.employee_id = None
    db.flush()

    matched_count = 0
    unmatched_count = 0
    duplicate_count = 0
    low_confidence_count = 0

    for source_file in batch.source_files:
        file_records = sorted(source_file.normalized_records, key=lambda item: item.source_row_number)
        preview_records = [_preview_from_model(record) for record in file_records]
        preview_results = match_preview_records(preview_records, [])
        apply_match_results_to_normalized_records(file_records, preview_results)
        result_models = build_match_result_models(
            preview_results,
            batch_id=batch.id,
            normalized_record_ids={record.source_row_number: record.id for record in file_records},
        )
        db.add_all(result_models)

        for result in preview_results:
            if result.match_status == 'matched':
                matched_count += 1
            elif result.match_status == 'duplicate':
                duplicate_count += 1
            elif result.match_status == 'low_confidence':
                low_confidence_count += 1
            else:
                unmatched_count += 1

    batch.status = BatchStatus.MATCHED
    db.commit()
    db.refresh(batch)

    return type('SimpleBatchMatch', (), {
        'batch_id': batch.id,
        'batch_name': batch.batch_name,
        'status': batch.status.value,
        'employee_master_available': False,
        'employee_master_count': 0,
        'blocked_reason': None,
        'total_records': len(batch.normalized_records),
        'matched_count': matched_count,
        'unmatched_count': unmatched_count,
        'duplicate_count': duplicate_count,
        'low_confidence_count': low_confidence_count,
        'source_files': [],
    })


def _preview_from_model(record) -> NormalizedPreviewRecord:
    raw_payload = record.raw_payload or {}
    values = {}
    for field in (
        'person_name', 'id_type', 'id_number', 'employee_id', 'social_security_number', 'company_name', 'region',
        'billing_period', 'period_start', 'period_end', 'payment_base', 'payment_salary',
        'housing_fund_account', 'housing_fund_base', 'housing_fund_personal', 'housing_fund_company', 'housing_fund_total',
        'total_amount', 'company_total_amount', 'personal_total_amount', 'pension_company', 'pension_personal', 'medical_company',
        'medical_personal', 'medical_maternity_company', 'maternity_amount', 'unemployment_company',
        'unemployment_personal', 'injury_company', 'supplementary_medical_company', 'supplementary_pension_company',
        'large_medical_personal', 'late_fee', 'interest', 'raw_sheet_name', 'raw_header_signature', 'source_file_name',
    ):
        value = getattr(record, field)
        if value is not None:
            values[field] = value
    return NormalizedPreviewRecord(
        source_row_number=record.source_row_number,
        values=values,
        unmapped_values=dict(raw_payload.get('unmapped_values') or {}),
        raw_values=dict(raw_payload.get('raw_values') or {}),
        raw_payload=raw_payload,
    )


def _resolve_metadata_values(files: list[UploadFile], values: list[str] | None, *, kind: str) -> list[str | None]:
    if values:
        cleaned = [(value or '').strip() or None for value in values]
        if len(cleaned) == 1 and len(files) > 1:
            return cleaned * len(files)
        if len(cleaned) == len(files):
            return cleaned

    if kind == 'region':
        return [None] * len(files)

    inferred: list[str | None] = []
    for upload in files:
        filename = Path(upload.filename or 'upload.xlsx').name
        region = infer_region_from_filename(filename)
        inferred.append(infer_company_name_from_filename(filename, region))
    return inferred


def infer_region_from_filename(filename: str) -> str | None:
    return detect_region_from_filename_by_rules(filename)


def infer_company_name_from_filename(filename: str, region: str | None) -> str | None:
    stem = Path(filename).stem
    if '--' in stem:
        tail = stem.split('--')[-1].strip()
        return tail or None

    cleaned = DATE_PATTERN.sub('', stem)
    cleaned = cleaned.replace('\u8865\u7f341\u6708\u5165\u804c2\u4eba', '')
    for noise in FILENAME_NOISE:
        cleaned = cleaned.replace(noise, '')
    if region:
        cleaned = cleaned.replace(REGION_LABELS.get(region, ''), '')
    cleaned = re.sub(r'[()\uff08\uff09_\-\s]+', '', cleaned)
    return cleaned or (REGION_LABELS.get(region) if region else None)


async def _emit_progress(
    progress_callback: ProgressCallback | None,
    *,
    stage: str,
    label: str,
    message: str,
    percent: int,
    batch_id: str | None = None,
    batch_name: str | None = None,
) -> None:
    if progress_callback is None:
        return

    payload: dict[str, object] = {
        'stage': stage,
        'label': label,
        'message': message,
        'percent': percent,
    }
    if batch_id is not None:
        payload['batch_id'] = batch_id
    if batch_name is not None:
        payload['batch_name'] = batch_name

    result = progress_callback(payload)
    if inspect.isawaitable(result):
        await result
