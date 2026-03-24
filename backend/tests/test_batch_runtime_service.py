from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from backend.app.services.batch_runtime_service import _build_missing_housing_warning_contexts


def test_build_missing_housing_warning_contexts_flags_outlier_when_company_has_uploaded_housing_data() -> None:
    social_source = SimpleNamespace(source_kind='social_security', region='shenzhen', company_name='ops')
    housing_source = SimpleNamespace(source_kind='housing_fund', region='shenzhen', company_name='ops')

    def social_record(*, record_id: str, row_number: int, person_name: str, id_number: str, has_housing: bool):
        return SimpleNamespace(
            id=record_id,
            source_file=social_source,
            source_file_id='social-file',
            source_row_number=row_number,
            person_name=person_name,
            id_number=id_number,
            housing_fund_personal=Decimal('175') if has_housing else None,
            housing_fund_company=Decimal('175') if has_housing else None,
            housing_fund_total=Decimal('350') if has_housing else None,
            raw_payload={'merged_sources': [{'source_kind': 'housing_fund'}]} if has_housing else {'merged_sources': []},
        )

    records = [
        social_record(record_id='r1', row_number=1, person_name='A', id_number='440101199001010011', has_housing=True),
        social_record(record_id='r2', row_number=2, person_name='B', id_number='440101199001010022', has_housing=True),
        social_record(record_id='r3', row_number=3, person_name='C', id_number='440101199001010033', has_housing=True),
        social_record(record_id='r4', row_number=4, person_name='D', id_number='440101199001010044', has_housing=False),
        SimpleNamespace(
            id='housing-row',
            source_file=housing_source,
            source_file_id='housing-file',
            source_row_number=1,
            person_name='A',
            id_number='440101199001010011',
            housing_fund_personal=Decimal('175'),
            housing_fund_company=Decimal('175'),
            housing_fund_total=Decimal('350'),
            raw_payload={'merged_sources': [{'source_kind': 'housing_fund'}]},
        ),
    ]

    warnings = _build_missing_housing_warning_contexts(records)

    assert len(warnings) == 1
    assert warnings[0].normalized_record_id == 'r4'
    assert warnings[0].issue.issue_type == 'missing_housing_match'
    assert warnings[0].issue.severity == 'warning'
