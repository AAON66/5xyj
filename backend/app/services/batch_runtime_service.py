from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy.orm import Session

from backend.app.models import EmployeeMaster, MatchResult, NormalizedRecord, ValidationIssue
from backend.app.models.enums import BatchStatus, MatchStatus
from backend.app.schemas.imports import (
    BatchMatchRead,
    BatchValidationRead,
    MatchRecordRead,
    SourceFileMatchRead,
    SourceFileValidationRead,
    ValidationIssueRead,
)
from backend.app.services.import_service import get_import_batch
from backend.app.services.matching_service import (
    MatchPreviewResult,
    apply_match_results_to_normalized_records,
    build_match_result_models,
    match_preview_records,
)
from backend.app.services.normalization_service import (
    NormalizedPreviewRecord,
    StandardizationResult,
    build_normalized_models,
    standardize_workbook,
)
from backend.app.services.validation_service import build_validation_issue_models, validate_standardized_result


CANONICAL_VALUE_FIELDS = (
    'person_name',
    'id_type',
    'id_number',
    'employee_id',
    'social_security_number',
    'company_name',
    'region',
    'billing_period',
    'period_start',
    'period_end',
    'payment_base',
    'payment_salary',
    'total_amount',
    'company_total_amount',
    'personal_total_amount',
    'pension_company',
    'pension_personal',
    'medical_company',
    'medical_personal',
    'medical_maternity_company',
    'maternity_amount',
    'unemployment_company',
    'unemployment_personal',
    'injury_company',
    'supplementary_medical_company',
    'supplementary_pension_company',
    'large_medical_personal',
    'late_fee',
    'interest',
    'raw_sheet_name',
    'raw_header_signature',
    'source_file_name',
)

BLOCKED_REASON = 'Employee master data is required before batch matching can run.'


@dataclass(slots=True)
class _SourceFileValidationContext:
    source_file_id: str
    file_name: str
    raw_sheet_name: str
    issues: list[ValidationIssueRead]


@dataclass(slots=True)
class _SourceFileMatchContext:
    source_file_id: str
    file_name: str
    raw_sheet_name: str
    results: list[MatchRecordRead]


class BatchRuntimeError(Exception):
    """Raised when batch runtime orchestration fails."""


def validate_batch(db: Session, batch_id: str) -> BatchValidationRead:
    batch = get_import_batch(db, batch_id)
    _ensure_normalized_records(db, batch_id)
    batch = get_import_batch(db, batch_id)

    db.query(ValidationIssue).filter(ValidationIssue.batch_id == batch.id).delete(synchronize_session=False)
    db.flush()

    source_file_contexts: list[_SourceFileValidationContext] = []
    total_issue_count = 0

    for source_file in batch.source_files:
        file_records = sorted(source_file.normalized_records, key=lambda item: item.source_row_number)
        preview_records = [_preview_from_model(record) for record in file_records]
        validation = validate_standardized_result(
            StandardizationResult(
                source_file=source_file.file_name,
                sheet_name=source_file.raw_sheet_name or '',
                raw_header_signature=file_records[0].raw_header_signature if file_records else '',
                records=preview_records,
                filtered_rows=[],
                unmapped_headers=[],
            )
        )
        issue_models = build_validation_issue_models(
            validation,
            batch_id=batch.id,
            normalized_record_ids={record.source_row_number: record.id for record in file_records},
        )
        db.add_all(issue_models)

        issue_reads = [
            ValidationIssueRead(
                normalized_record_id=issue.normalized_record_id,
                source_row_number=preview_issue.source_row_number,
                issue_type=preview_issue.issue_type,
                severity=preview_issue.severity,
                field_name=preview_issue.field_name,
                message=preview_issue.message,
            )
            for issue, preview_issue in zip(issue_models, validation.issues, strict=True)
        ]
        total_issue_count += len(issue_reads)
        source_file_contexts.append(
            _SourceFileValidationContext(
                source_file_id=source_file.id,
                file_name=source_file.file_name,
                raw_sheet_name=source_file.raw_sheet_name or '',
                issues=issue_reads,
            )
        )

    batch.status = BatchStatus.VALIDATED
    db.commit()
    db.refresh(batch)
    return BatchValidationRead(
        batch_id=batch.id,
        batch_name=batch.batch_name,
        status=batch.status.value,
        total_issue_count=total_issue_count,
        source_files=[
            SourceFileValidationRead(
                source_file_id=context.source_file_id,
                file_name=context.file_name,
                raw_sheet_name=context.raw_sheet_name,
                issue_count=len(context.issues),
                issues=context.issues,
            )
            for context in source_file_contexts
        ],
    )


def get_batch_validation(db: Session, batch_id: str) -> BatchValidationRead:
    batch = get_import_batch(db, batch_id)
    source_files: list[SourceFileValidationRead] = []
    total_issue_count = 0

    for source_file in batch.source_files:
        file_issues = [
            ValidationIssueRead(
                normalized_record_id=issue.normalized_record_id,
                source_row_number=issue.normalized_record.source_row_number if issue.normalized_record is not None else -1,
                issue_type=issue.issue_type,
                severity=issue.severity,
                field_name=issue.field_name,
                message=issue.message,
            )
            for issue in sorted(_source_file_related_validation_issues(source_file.normalized_records), key=lambda item: (item.normalized_record.source_row_number if item.normalized_record is not None else -1, item.issue_type, item.id))
        ]
        total_issue_count += len(file_issues)
        source_files.append(
            SourceFileValidationRead(
                source_file_id=source_file.id,
                file_name=source_file.file_name,
                raw_sheet_name=source_file.raw_sheet_name or '',
                issue_count=len(file_issues),
                issues=file_issues,
            )
        )

    return BatchValidationRead(
        batch_id=batch.id,
        batch_name=batch.batch_name,
        status=batch.status.value,
        total_issue_count=total_issue_count,
        source_files=source_files,
    )


def match_batch(db: Session, batch_id: str) -> BatchMatchRead:
    batch = get_import_batch(db, batch_id)
    _ensure_normalized_records(db, batch_id)
    batch = get_import_batch(db, batch_id)

    employee_masters = list(
        db.query(EmployeeMaster).filter(EmployeeMaster.active.is_(True)).order_by(EmployeeMaster.employee_id.asc()).all()
    )
    db.query(MatchResult).filter(MatchResult.batch_id == batch.id).delete(synchronize_session=False)
    for record in batch.normalized_records:
        record.employee_id = None
    db.flush()

    if not employee_masters:
        batch.status = BatchStatus.BLOCKED
        db.commit()
        db.refresh(batch)
        return BatchMatchRead(
            batch_id=batch.id,
            batch_name=batch.batch_name,
            status=batch.status.value,
            employee_master_available=False,
            employee_master_count=0,
            blocked_reason=BLOCKED_REASON,
            total_records=len(batch.normalized_records),
            matched_count=0,
            unmatched_count=0,
            duplicate_count=0,
            low_confidence_count=0,
            source_files=[
                SourceFileMatchRead(
                    source_file_id=source_file.id,
                    file_name=source_file.file_name,
                    raw_sheet_name=source_file.raw_sheet_name or '',
                    result_count=len(source_file.normalized_records),
                    results=[],
                )
                for source_file in batch.source_files
            ],
        )

    source_file_contexts: list[_SourceFileMatchContext] = []
    aggregate_counts = {
        MatchStatus.MATCHED.value: 0,
        MatchStatus.UNMATCHED.value: 0,
        MatchStatus.DUPLICATE.value: 0,
        MatchStatus.LOW_CONFIDENCE.value: 0,
    }

    for source_file in batch.source_files:
        file_records = sorted(source_file.normalized_records, key=lambda item: item.source_row_number)
        preview_records = [_preview_from_model(record) for record in file_records]
        preview_results = match_preview_records(preview_records, employee_masters)
        apply_match_results_to_normalized_records(file_records, preview_results)
        result_models = build_match_result_models(
            preview_results,
            batch_id=batch.id,
            normalized_record_ids={record.source_row_number: record.id for record in file_records},
        )
        db.add_all(result_models)

        result_reads = [_match_read_from_preview(record, preview) for record, preview in zip(file_records, preview_results, strict=True)]
        for result in result_reads:
            aggregate_counts[result.match_status] += 1
        source_file_contexts.append(
            _SourceFileMatchContext(
                source_file_id=source_file.id,
                file_name=source_file.file_name,
                raw_sheet_name=source_file.raw_sheet_name or '',
                results=result_reads,
            )
        )

    batch.status = BatchStatus.MATCHED
    db.commit()
    db.refresh(batch)
    return BatchMatchRead(
        batch_id=batch.id,
        batch_name=batch.batch_name,
        status=batch.status.value,
        employee_master_available=True,
        employee_master_count=len(employee_masters),
        blocked_reason=None,
        total_records=len(batch.normalized_records),
        matched_count=aggregate_counts[MatchStatus.MATCHED.value],
        unmatched_count=aggregate_counts[MatchStatus.UNMATCHED.value],
        duplicate_count=aggregate_counts[MatchStatus.DUPLICATE.value],
        low_confidence_count=aggregate_counts[MatchStatus.LOW_CONFIDENCE.value],
        source_files=[
            SourceFileMatchRead(
                source_file_id=context.source_file_id,
                file_name=context.file_name,
                raw_sheet_name=context.raw_sheet_name,
                result_count=len(context.results),
                results=context.results,
            )
            for context in source_file_contexts
        ],
    )


def get_batch_match(db: Session, batch_id: str) -> BatchMatchRead:
    batch = get_import_batch(db, batch_id)
    employee_master_count = db.query(EmployeeMaster).filter(EmployeeMaster.active.is_(True)).count()
    results_by_record_id = {result.normalized_record_id: result for result in batch.match_results}

    source_files: list[SourceFileMatchRead] = []
    aggregate_counts = {
        MatchStatus.MATCHED.value: 0,
        MatchStatus.UNMATCHED.value: 0,
        MatchStatus.DUPLICATE.value: 0,
        MatchStatus.LOW_CONFIDENCE.value: 0,
    }

    for source_file in batch.source_files:
        file_results: list[MatchRecordRead] = []
        for record in sorted(source_file.normalized_records, key=lambda item: item.source_row_number):
            persisted = results_by_record_id.get(record.id)
            if persisted is None:
                continue
            item = MatchRecordRead(
                normalized_record_id=record.id,
                source_row_number=record.source_row_number,
                person_name=record.person_name,
                id_number=record.id_number,
                employee_id=record.employee_id,
                employee_master_id=persisted.employee_master_id,
                match_status=persisted.match_status.value,
                match_basis=persisted.match_basis,
                confidence=persisted.confidence,
                candidate_employee_ids=[record.employee_id] if record.employee_id else [],
            )
            aggregate_counts[item.match_status] += 1
            file_results.append(item)
        source_files.append(
            SourceFileMatchRead(
                source_file_id=source_file.id,
                file_name=source_file.file_name,
                raw_sheet_name=source_file.raw_sheet_name or '',
                result_count=len(file_results),
                results=file_results,
            )
        )

    blocked_reason = BLOCKED_REASON if batch.status == BatchStatus.BLOCKED else None
    return BatchMatchRead(
        batch_id=batch.id,
        batch_name=batch.batch_name,
        status=batch.status.value,
        employee_master_available=employee_master_count > 0,
        employee_master_count=employee_master_count,
        blocked_reason=blocked_reason,
        total_records=len(batch.normalized_records),
        matched_count=aggregate_counts[MatchStatus.MATCHED.value],
        unmatched_count=aggregate_counts[MatchStatus.UNMATCHED.value],
        duplicate_count=aggregate_counts[MatchStatus.DUPLICATE.value],
        low_confidence_count=aggregate_counts[MatchStatus.LOW_CONFIDENCE.value],
        source_files=source_files,
    )


def _ensure_normalized_records(db: Session, batch_id: str) -> None:
    batch = get_import_batch(db, batch_id)
    if batch.normalized_records:
        return

    for source_file in batch.source_files:
        standardized = standardize_workbook(
            source_file.file_path,
            region=source_file.region,
            company_name=source_file.company_name,
            source_file_name=source_file.file_name,
        )
        source_file.raw_sheet_name = standardized.sheet_name
        db.add_all(build_normalized_models(standardized, batch_id=batch.id, source_file_id=source_file.id))

    batch.status = BatchStatus.NORMALIZED
    db.commit()


def _preview_from_model(record: NormalizedRecord) -> NormalizedPreviewRecord:
    raw_payload = record.raw_payload or {}
    values = {}
    for field in CANONICAL_VALUE_FIELDS:
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


def _source_file_related_validation_issues(records: Iterable[NormalizedRecord]) -> list[ValidationIssue]:
    items: list[ValidationIssue] = []
    for record in records:
        items.extend(record.validation_issues)
    return items


def _match_read_from_preview(record: NormalizedRecord, preview: MatchPreviewResult) -> MatchRecordRead:
    return MatchRecordRead(
        normalized_record_id=record.id,
        source_row_number=record.source_row_number,
        person_name=record.person_name,
        id_number=record.id_number,
        employee_id=preview.employee_id,
        employee_master_id=preview.employee_master_id,
        match_status=preview.match_status,
        match_basis=preview.match_basis,
        confidence=preview.confidence,
        candidate_employee_ids=preview.candidate_employee_ids,
    )
