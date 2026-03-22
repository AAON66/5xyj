from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.core.config import ROOT_DIR
from backend.app.models.employee_master import EmployeeMaster
from backend.app.models.enums import MatchStatus
from backend.app.services import (
    apply_match_results_to_normalized_records,
    build_match_result_models,
    build_normalized_models,
    match_preview_records,
    standardize_workbook,
)


SAMPLES_DIR = ROOT_DIR / 'data' / 'samples'


def find_sample(keyword: str) -> Path:
    for path in sorted(SAMPLES_DIR.glob('*.xlsx')):
        if keyword in path.name:
            return path
    pytest.skip(f'Sample containing {keyword!r} was not found in {SAMPLES_DIR}.')


def make_employee(
    employee_id: str,
    person_name: str,
    *,
    id_number: str | None = None,
    company_name: str | None = None,
    active: bool = True,
    record_id: str | None = None,
) -> EmployeeMaster:
    return EmployeeMaster(
        id=record_id or f'emp-{employee_id}',
        employee_id=employee_id,
        person_name=person_name,
        id_number=id_number,
        company_name=company_name,
        active=active,
    )


def test_match_preview_records_matches_by_id_number_exact() -> None:
    sample_path = find_sample('\u5e7f\u5206')
    standardized = standardize_workbook(sample_path, region='guangzhou', company_name='\u5e7f\u5dde\u793a\u4f8b')
    record = standardized.records[0]
    employee = make_employee(
        'E1001',
        record.values['person_name'],
        id_number=record.values['id_number'],
        company_name='\u5176\u5b83\u516c\u53f8',
    )

    results = match_preview_records([record], [employee])

    assert len(results) == 1
    assert results[0].match_status == MatchStatus.MATCHED.value
    assert results[0].employee_id == 'E1001'
    assert results[0].match_basis == 'id_number_exact'
    assert results[0].confidence == 1.0


def test_match_preview_records_normalizes_id_number_before_exact_match() -> None:
    sample_path = find_sample('\u5e7f\u5206')
    standardized = standardize_workbook(sample_path, region='guangzhou', company_name='\u5e7f\u5dde\u793a\u4f8b')
    record = standardized.records[0]
    record.values['id_number'] = f" {str(record.values['id_number']).lower()} "
    employee = make_employee(
        'E1002',
        record.values['person_name'],
        id_number=str(record.values['id_number']).strip().upper(),
        company_name='\u5176\u5b83\u516c\u53f8',
    )

    results = match_preview_records([record], [employee])

    assert results[0].match_status == MatchStatus.MATCHED.value
    assert results[0].employee_id == 'E1002'
    assert results[0].match_basis == 'id_number_exact'


def test_match_preview_records_matches_by_name_and_company_when_id_missing() -> None:
    sample_path = find_sample('\u957f\u6c99')
    standardized = standardize_workbook(sample_path, region='changsha', company_name='\u957f\u6c99\u793a\u4f8b\u516c\u53f8')
    record = standardized.records[0]
    employee = make_employee(
        'E2001',
        record.values['person_name'],
        company_name='\u957f\u6c99\u793a\u4f8b\u516c\u53f8',
    )

    results = match_preview_records([record], [employee])

    assert len(results) == 1
    assert results[0].match_status == MatchStatus.MATCHED.value
    assert results[0].employee_id == 'E2001'
    assert results[0].match_basis == 'person_name_company_exact'
    assert results[0].confidence == 0.9


def test_match_preview_records_marks_name_only_match_as_low_confidence() -> None:
    sample_path = find_sample('\u957f\u6c99')
    standardized = standardize_workbook(sample_path, region='changsha')
    record = standardized.records[0]
    employee = make_employee('E3001', record.values['person_name'])

    results = match_preview_records([record], [employee])

    assert results[0].match_status == MatchStatus.LOW_CONFIDENCE.value
    assert results[0].employee_id == 'E3001'
    assert results[0].match_basis == 'person_name_exact'
    assert results[0].confidence == 0.6


def test_match_preview_records_marks_unmatched_when_no_candidate() -> None:
    sample_path = find_sample('\u6b66\u6c49')
    standardized = standardize_workbook(sample_path, region='wuhan')
    record = standardized.records[0]

    results = match_preview_records([record], [make_employee('E4001', '\u5176\u4ed6\u4eba', id_number='110101199001010011')])

    assert results[0].match_status == MatchStatus.UNMATCHED.value
    assert results[0].employee_id is None
    assert results[0].candidate_employee_ids == []


def test_match_preview_records_does_not_treat_header_text_as_id_number() -> None:
    sample_path = find_sample('\u6b66\u6c49')
    standardized = standardize_workbook(sample_path, region='wuhan')
    record = standardized.records[0]
    record.values['id_number'] = '\u8eab\u4efd\u8bc1\u53f7\u7801'

    results = match_preview_records([record], [make_employee('E4100', record.values['person_name'], id_number='440101199001010011')])

    assert results[0].match_status == MatchStatus.LOW_CONFIDENCE.value
    assert results[0].employee_id == 'E4100'
    assert results[0].match_basis == 'person_name_exact'


def test_match_preview_records_does_not_fallback_to_name_when_non_empty_id_is_invalid() -> None:
    sample_path = find_sample('\u6b66\u6c49')
    standardized = standardize_workbook(sample_path, region='wuhan', company_name='\u6b66\u6c49\u793a\u4f8b\u516c\u53f8')
    record = standardized.records[0]
    record.values['id_number'] = '12345'
    record.values['company_name'] = '\u6b66\u6c49\u793a\u4f8b\u516c\u53f8'

    results = match_preview_records([record], [make_employee('E4200', record.values['person_name'], company_name='\u6b66\u6c49\u793a\u4f8b\u516c\u53f8')])

    assert results[0].match_status == MatchStatus.UNMATCHED.value
    assert results[0].employee_id is None
    assert results[0].match_basis is None


def test_match_preview_records_marks_duplicate_for_multiple_exact_candidates() -> None:
    sample_path = find_sample('\u5e7f\u5206')
    standardized = standardize_workbook(sample_path, region='guangzhou')
    record = standardized.records[0]
    employees = [
        make_employee('E5001', record.values['person_name'], id_number=record.values['id_number']),
        make_employee('E5002', record.values['person_name'], id_number=record.values['id_number']),
    ]

    results = match_preview_records([record], employees)

    assert results[0].match_status == MatchStatus.DUPLICATE.value
    assert results[0].employee_id is None
    assert results[0].match_basis == 'id_number_exact_duplicate'
    assert results[0].candidate_employee_ids == ['E5001', 'E5002']


def test_build_match_result_models_and_apply_results_to_normalized_records() -> None:
    sample_path = find_sample('\u5e7f\u5206')
    standardized = standardize_workbook(sample_path, region='guangzhou', company_name='\u5e7f\u5dde\u793a\u4f8b')
    preview_record = standardized.records[0]
    employee = make_employee(
        'E6001',
        preview_record.values['person_name'],
        id_number=preview_record.values['id_number'],
        company_name='\u5e7f\u5dde\u793a\u4f8b',
        record_id='employee-master-1',
    )

    match_results = match_preview_records([preview_record], [employee])
    normalized_models = build_normalized_models(standardized, batch_id='batch-1', source_file_id='source-1')
    apply_match_results_to_normalized_records(normalized_models, match_results)
    match_models = build_match_result_models(
        match_results,
        batch_id='batch-1',
        normalized_record_ids={preview_record.source_row_number: normalized_models[0].id},
        employee_master_ids={'E6001': 'employee-master-1'},
    )

    assert normalized_models[0].employee_id == 'E6001'
    assert len(match_models) == 1
    assert match_models[0].batch_id == 'batch-1'
    assert match_models[0].normalized_record_id == normalized_models[0].id
    assert match_models[0].employee_master_id == 'employee-master-1'
    assert match_models[0].match_status == MatchStatus.MATCHED
    assert match_models[0].match_basis == 'id_number_exact'
    assert match_models[0].confidence == 1.0
