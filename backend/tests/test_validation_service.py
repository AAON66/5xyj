from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from backend.app.core.config import ROOT_DIR
from backend.app.services import (
    NormalizedPreviewRecord,
    StandardizationResult,
    build_normalized_models,
    build_validation_issue_models,
    standardize_workbook,
    validate_standardized_result,
)


SAMPLES_DIR = ROOT_DIR / 'data' / 'samples'


def find_sample(keyword: str) -> Path:
    for path in sorted(SAMPLES_DIR.glob('*.xlsx')):
        if keyword in path.name:
            return path
    pytest.skip(f'Sample containing {keyword!r} was not found in {SAMPLES_DIR}.')


def clone_record(record: NormalizedPreviewRecord, **value_updates: object) -> NormalizedPreviewRecord:
    values = deepcopy(record.values)
    values.update(value_updates)
    return NormalizedPreviewRecord(
        source_row_number=record.source_row_number,
        values=values,
        unmapped_values=deepcopy(record.unmapped_values),
        raw_values=deepcopy(record.raw_values),
        raw_payload=deepcopy(record.raw_payload),
    )


def test_validate_standardized_result_on_real_guangzhou_sample_has_no_issues() -> None:
    sample_path = find_sample('\u5e7f\u5206')
    result = standardize_workbook(sample_path, region='guangzhou')

    validation = validate_standardized_result(result)

    assert validation.issues == []


def test_validate_standardized_result_on_real_xiamen_sample_has_no_issues() -> None:
    sample_path = find_sample('\u53a6\u95e8202602\u793e\u4fdd\u8d26\u5355.xlsx')
    result = standardize_workbook(sample_path, region='xiamen')

    validation = validate_standardized_result(result)

    assert validation.issues == []


def test_validate_standardized_result_reports_required_missing_and_invalid_id_and_amount_mismatch() -> None:
    sample_path = find_sample('\u6df1\u5733\u521b\u9020\u6b22\u4e50')
    standardized = standardize_workbook(sample_path, region='shenzhen')
    broken = clone_record(
        standardized.records[0],
        person_name=None,
        id_number='123456789012345678',
        total_amount=Decimal('1.00'),
        billing_period=None,
    )
    broken_result = StandardizationResult(
        source_file=standardized.source_file,
        sheet_name=standardized.sheet_name,
        raw_header_signature=standardized.raw_header_signature,
        records=[broken],
        filtered_rows=standardized.filtered_rows,
        unmapped_headers=standardized.unmapped_headers,
    )

    validation = validate_standardized_result(broken_result)

    issues = {(issue.issue_type, issue.field_name) for issue in validation.issues}
    assert ('required_missing', 'person_name') in issues
    assert ('required_missing', 'billing_period') in issues
    assert ('invalid_format', 'id_number') in issues
    assert ('amount_mismatch', 'total_amount') in issues


def test_validate_standardized_result_reports_duplicate_records_by_id_number_and_period() -> None:
    sample_path = find_sample('\u6b66\u6c49')
    standardized = standardize_workbook(sample_path, region='wuhan')
    first = standardized.records[0]
    duplicate = NormalizedPreviewRecord(
        source_row_number=99,
        values=deepcopy(first.values),
        unmapped_values=deepcopy(first.unmapped_values),
        raw_values=deepcopy(first.raw_values),
        raw_payload=deepcopy(first.raw_payload),
    )
    duplicated_result = StandardizationResult(
        source_file=standardized.source_file,
        sheet_name=standardized.sheet_name,
        raw_header_signature=standardized.raw_header_signature,
        records=[first, duplicate],
        filtered_rows=standardized.filtered_rows,
        unmapped_headers=standardized.unmapped_headers,
    )

    validation = validate_standardized_result(duplicated_result)

    duplicate_issues = [issue for issue in validation.issues if issue.issue_type == 'duplicate_record']
    assert len(duplicate_issues) == 2
    assert {issue.source_row_number for issue in duplicate_issues} == {first.source_row_number, 99}


def test_validate_standardized_result_reports_duplicate_records_by_name_company_and_period() -> None:
    sample_path = find_sample('\u957f\u6c99')
    standardized = standardize_workbook(sample_path, region='changsha', company_name='\u957f\u6c99\u793a\u4f8b\u516c\u53f8')
    first = clone_record(standardized.records[0], id_number=None)
    duplicate = clone_record(first)
    duplicate = NormalizedPreviewRecord(
        source_row_number=100,
        values=duplicate.values,
        unmapped_values=duplicate.unmapped_values,
        raw_values=duplicate.raw_values,
        raw_payload=duplicate.raw_payload,
    )
    duplicated_result = StandardizationResult(
        source_file=standardized.source_file,
        sheet_name=standardized.sheet_name,
        raw_header_signature=standardized.raw_header_signature,
        records=[first, duplicate],
        filtered_rows=standardized.filtered_rows,
        unmapped_headers=standardized.unmapped_headers,
    )

    validation = validate_standardized_result(duplicated_result)

    duplicate_issues = [issue for issue in validation.issues if issue.issue_type == 'duplicate_record']
    assert len(duplicate_issues) == 2
    assert {issue.source_row_number for issue in duplicate_issues} == {first.source_row_number, 100}


def test_build_validation_issue_models_links_normalized_record_ids() -> None:
    sample_path = find_sample('\u5e7f\u5206')
    standardized = standardize_workbook(sample_path, region='guangzhou')
    broken = clone_record(standardized.records[0], id_number='123456789012345678')
    broken_result = StandardizationResult(
        source_file=standardized.source_file,
        sheet_name=standardized.sheet_name,
        raw_header_signature=standardized.raw_header_signature,
        records=[broken],
        filtered_rows=standardized.filtered_rows,
        unmapped_headers=standardized.unmapped_headers,
    )
    validation = validate_standardized_result(broken_result)
    normalized_models = build_normalized_models(broken_result, batch_id='batch-1', source_file_id='source-1')

    issue_models = build_validation_issue_models(
        validation,
        batch_id='batch-1',
        normalized_record_ids={broken.source_row_number: normalized_models[0].id},
    )

    assert len(issue_models) == 1
    assert issue_models[0].batch_id == 'batch-1'
    assert issue_models[0].normalized_record_id == normalized_models[0].id
    assert issue_models[0].issue_type == 'invalid_format'
    assert issue_models[0].field_name == 'id_number'
    assert issue_models[0].resolved is False
