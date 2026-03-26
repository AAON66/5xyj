# 03-02 Summary

## Outcome
- Migrated exporter unit tests, cross-region exporter regression, aggregate API export tests, and dashboard export coverage onto the shared export fixture helpers.
- Removed remaining Desktop-path assumptions, local `find_template()` / `find_sample()` helpers, and the nonexistent `data/templates/placeholder.xlsx` dependency from Wave 2 suites.
- Switched exporter test artifact directories to unique repo-local paths per invocation so repeated Windows runs do not fail on stale file locks.
- Kept the full regional regression surface for Guangzhou, Hangzhou, Xiamen, Shenzhen, Wuhan, and Changsha while making template/sample setup reproducible on another machine.

## Files Changed
- `backend/tests/test_template_exporter.py`
- `backend/tests/test_template_exporter_regression.py`
- `backend/tests/test_aggregate_api.py`
- `backend/tests/test_dashboard_api.py`

## Verification
- Passed: `.\.venv\Scripts\python.exe -m pytest backend/tests/test_template_exporter.py::test_export_dual_templates_writes_both_template_outputs backend/tests/test_template_exporter.py::test_export_dual_templates_marks_overall_failure_when_any_template_is_missing backend/tests/test_template_exporter.py::test_export_dual_templates_filters_header_like_dirty_rows backend/tests/test_template_exporter.py::test_export_dual_templates_filters_zero_amount_rows_even_when_identity_exists backend/tests/test_template_exporter.py::test_export_dual_templates_filters_inferred_housing_only_when_mixed_with_explicit_split_rows backend/tests/test_template_exporter.py::test_export_dual_templates_merges_records_with_same_employee_id_before_writing backend/tests/test_template_exporter.py::test_export_dual_templates_keeps_housing_burden_zero_even_with_repeated_source_baseline backend/tests/test_template_exporter.py::test_export_dual_templates_defaults_social_burden_to_zero_without_explicit_rule backend/tests/test_template_exporter.py::test_export_dual_templates_sums_duplicate_social_records_from_distinct_sources backend/tests/test_template_exporter.py::test_export_dual_templates_uses_single_xiamen_company_medical_baseline_when_duplicate_sources_repeat_amounts -x -p no:cacheprovider` (10/10)
- Passed: `.\.venv\Scripts\python.exe -m pytest backend/tests/test_template_exporter.py::test_export_dual_templates_keeps_large_housing_burden_zero_without_inference backend/tests/test_template_exporter.py::test_export_dual_templates_derives_housing_amount_from_total_when_personal_value_is_ratio backend/tests/test_template_exporter.py::test_export_dual_templates_zeroes_housing_burden_when_no_reliable_baseline_exists backend/tests/test_template_exporter.py::test_export_dual_templates_filters_housing_only_rows_when_split_is_only_inferred backend/tests/test_template_exporter.py::test_export_dual_templates_keeps_housing_only_rows_when_source_has_explicit_split_columns backend/tests/test_template_exporter.py::test_export_dual_templates_keeps_housing_only_rows_when_prefixed_headers_include_explicit_split_columns backend/tests/test_template_exporter.py::test_export_dual_templates_routes_wuhan_large_medical_to_personal_output backend/tests/test_template_exporter.py::test_export_dual_templates_keeps_changsha_large_medical_at_source_amount -x -p no:cacheprovider` (8/8)
- Passed: `.\.venv\Scripts\python.exe -m pytest backend/tests/test_template_exporter_regression.py -x -p no:cacheprovider` (6/6)
- Passed: `.\.venv\Scripts\python.exe -m pytest backend/tests/test_aggregate_api.py backend/tests/test_dashboard_api.py -x -p no:cacheprovider` (15/15)

## Requirements Covered
- `VER-01`: Exporter, regression, aggregate, and dashboard suites all resolve required templates through the shared repo/default contract or explicit configuration.
- `VER-02`: Missing mandatory templates/samples fail loudly and the aggregate oversized-upload regression no longer depends on an absent tracked workbook.

## Notes
- A mid-run Windows file-lock failure in `test_template_exporter.py` was auto-fixed by switching exporter artifact directories from reuse-with-delete to unique repo-local directories per test invocation.
- The dashboard and regression test rewrites use `\u` escapes in string literals to keep the files ASCII-safe while still resolving the intended Chinese sample/company names at runtime.
