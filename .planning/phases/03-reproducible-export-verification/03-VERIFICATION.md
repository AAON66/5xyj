---
status: passed
phase: 03-reproducible-export-verification
verified: 2026-03-26
requirements:
  - VER-01
  - VER-02
---

# Phase 3 Verification

## Result
- Passed.

## Automated Checks
- `.\.venv\Scripts\python.exe -m pytest backend/tests/test_export_fixture_support.py backend/tests/test_export_api.py -x -p no:cacheprovider` (13/13)
- `.\.venv\Scripts\python.exe -m pytest backend/tests/test_template_exporter.py::test_export_dual_templates_writes_both_template_outputs backend/tests/test_template_exporter.py::test_export_dual_templates_marks_overall_failure_when_any_template_is_missing backend/tests/test_template_exporter.py::test_export_dual_templates_filters_header_like_dirty_rows backend/tests/test_template_exporter.py::test_export_dual_templates_filters_zero_amount_rows_even_when_identity_exists backend/tests/test_template_exporter.py::test_export_dual_templates_filters_inferred_housing_only_when_mixed_with_explicit_split_rows backend/tests/test_template_exporter.py::test_export_dual_templates_merges_records_with_same_employee_id_before_writing backend/tests/test_template_exporter.py::test_export_dual_templates_keeps_housing_burden_zero_even_with_repeated_source_baseline backend/tests/test_template_exporter.py::test_export_dual_templates_defaults_social_burden_to_zero_without_explicit_rule backend/tests/test_template_exporter.py::test_export_dual_templates_sums_duplicate_social_records_from_distinct_sources backend/tests/test_template_exporter.py::test_export_dual_templates_uses_single_xiamen_company_medical_baseline_when_duplicate_sources_repeat_amounts -x -p no:cacheprovider` (10/10)
- `.\.venv\Scripts\python.exe -m pytest backend/tests/test_template_exporter.py::test_export_dual_templates_keeps_large_housing_burden_zero_without_inference backend/tests/test_template_exporter.py::test_export_dual_templates_derives_housing_amount_from_total_when_personal_value_is_ratio backend/tests/test_template_exporter.py::test_export_dual_templates_zeroes_housing_burden_when_no_reliable_baseline_exists backend/tests/test_template_exporter.py::test_export_dual_templates_filters_housing_only_rows_when_split_is_only_inferred backend/tests/test_template_exporter.py::test_export_dual_templates_keeps_housing_only_rows_when_source_has_explicit_split_columns backend/tests/test_template_exporter.py::test_export_dual_templates_keeps_housing_only_rows_when_prefixed_headers_include_explicit_split_columns backend/tests/test_template_exporter.py::test_export_dual_templates_routes_wuhan_large_medical_to_personal_output backend/tests/test_template_exporter.py::test_export_dual_templates_keeps_changsha_large_medical_at_source_amount -x -p no:cacheprovider` (8/8)
- `.\.venv\Scripts\python.exe -m pytest backend/tests/test_template_exporter_regression.py -x -p no:cacheprovider` (6/6)
- `.\.venv\Scripts\python.exe -m pytest backend/tests/test_aggregate_api.py backend/tests/test_dashboard_api.py -x -p no:cacheprovider` (15/15)

## Requirement Coverage
- `VER-01`: Verified shared resolution of required salary/final-tool templates from repo fixtures, `templates_dir` discovery, and valid explicit configuration overrides.
- `VER-02`: Verified fail-loud behavior for missing required fixtures, missing required samples, and bad explicit template paths, with no remaining Desktop-only or placeholder-file assumptions in export-related suites.

## Notes
- The shared helper contract is now `RequiredExportTemplates(salary, final_tool, manifest)` via `backend/tests/support/export_fixtures.py`.
- This environment requires repo-local test artifact directories and `-p no:cacheprovider` because the default Windows temp/cache locations are not reliably writable.
