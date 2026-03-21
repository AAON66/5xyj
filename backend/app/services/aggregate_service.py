from __future__ import annotations

import re
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.models import EmployeeMaster, MatchResult
from backend.app.models.enums import BatchStatus
from backend.app.schemas.aggregate import AggregateEmployeeImportRead, AggregateRunRead, AggregateSourceFileRead
from backend.app.schemas.imports import ExportArtifactRead
from backend.app.services.batch_export_service import export_batch
from backend.app.services.batch_runtime_service import match_batch, validate_batch
from backend.app.services.employee_service import import_employee_master_file
from backend.app.services.import_service import create_import_batch, get_import_batch, parse_import_batch
from backend.app.services.matching_service import apply_match_results_to_normalized_records, build_match_result_models, match_preview_records
from backend.app.services.normalization_service import NormalizedPreviewRecord

REGION_KEYWORDS = {
    'guangzhou': ('\u5e7f\u5dde', '\u5e7f\u5206', '\u89c6\u64ad'),
    'hangzhou': ('\u676d\u5dde', '\u805a\u53d8', '\u88c2\u53d8'),
    'xiamen': ('\u53a6\u95e8',),
    'shenzhen': ('\u6df1\u5733', '\u5218\u8273\u73b2'),
    'wuhan': ('\u6b66\u6c49',),
    'changsha': ('\u957f\u6c99',),
}

REGION_LABELS = {
    'guangzhou': '\u5e7f\u5dde',
    'hangzhou': '\u676d\u5dde',
    'xiamen': '\u53a6\u95e8',
    'shenzhen': '\u6df1\u5733',
    'wuhan': '\u6b66\u6c49',
    'changsha': '\u957f\u6c99',
}

FILENAME_NOISE = (
    '\u793e\u4f1a\u4fdd\u9669\u8d39\u7533\u62a5\u4e2a\u4eba\u660e\u7ec6\u8868',
    '\u793e\u4fdd\u7f34\u8d39\u660e\u7ec6',
    '\u793e\u4fdd\u660e\u7ec6',
    '\u793e\u4fdd\u8d26\u5355',
    '\u793e\u4fdd\u53f0\u8d26',
    '\u8d26\u5355',
    '\u660e\u7ec6',
    '\u53f0\u8d26',
    '\u8865\u7f34',
)

DATE_PATTERN = re.compile(r'(20\d{2}\u5e74\d{1,2}\u6708|20\d{4}|\d{6})')


async def run_simple_aggregate(
    db: Session,
    settings: Settings,
    *,
    files: list[UploadFile],
    employee_master_file: UploadFile | None = None,
    batch_name: str | None = None,
    regions: list[str] | None = None,
    company_names: list[str] | None = None,
) -> AggregateRunRead:
    employee_summary: AggregateEmployeeImportRead | None = None
    if employee_master_file is not None and (employee_master_file.filename or '').strip():
        employee_import = await import_employee_master_file(db, employee_master_file)
        employee_summary = AggregateEmployeeImportRead(
            file_name=employee_import.file_name,
            imported_count=employee_import.imported_count,
            created_count=employee_import.created_count,
            updated_count=employee_import.updated_count,
        )

    resolved_regions = _resolve_metadata_values(files, regions, kind='region')
    resolved_companies = _resolve_metadata_values(files, company_names, kind='company')

    batch = await create_import_batch(
        db=db,
        settings=settings,
        files=files,
        batch_name=batch_name,
        regions=resolved_regions,
        company_names=resolved_companies,
    )

    preview = parse_import_batch(db, batch.id)
    validation = validate_batch(db, batch.id)
    match = _match_for_simple_aggregate(db, batch.id)
    export = export_batch(db, batch.id, settings)

    return AggregateRunRead(
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
        'billing_period', 'period_start', 'period_end', 'payment_base', 'payment_salary', 'total_amount',
        'company_total_amount', 'personal_total_amount', 'pension_company', 'pension_personal', 'medical_company',
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

    inferred: list[str | None] = []
    for upload in files:
        filename = Path(upload.filename or 'upload.xlsx').name
        region = infer_region_from_filename(filename)
        if kind == 'region':
            inferred.append(region)
        else:
            inferred.append(infer_company_name_from_filename(filename, region))
    return inferred


def infer_region_from_filename(filename: str) -> str | None:
    for region, keywords in REGION_KEYWORDS.items():
        if any(keyword in filename for keyword in keywords):
            return region
    return None


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
