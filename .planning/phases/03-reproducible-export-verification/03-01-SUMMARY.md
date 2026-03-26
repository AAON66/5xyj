# 03-01 Summary

## Outcome
- Added a repo-controlled regression template manifest and checked-in salary/final-tool template pair under `data/templates/regression`.
- Introduced `backend/tests/support/export_fixtures.py` as the shared contract for required export templates, required sample workbooks, and generated placeholder template pairs.
- Updated `batch_export_service.export_batch()` to pass explicit configured template paths through unchanged so missing explicit paths still fail loudly in exporter resolution.
- Moved export API verification onto the shared helper contract and added coverage for both repo-default discovery and valid explicit template overrides.
- Kept the dual-template export contract strict: missing required repo fixtures or explicit bad paths now fail the test flow loudly instead of silently falling back to workstation-specific discovery.

## Files Changed
- `data/templates/regression/manifest.json`
- `data/templates/regression/salary-template.xlsx`
- `data/templates/regression/final-tool-template.xlsx`
- `backend/tests/support/export_fixtures.py`
- `backend/tests/test_export_fixture_support.py`
- `backend/app/services/batch_export_service.py`
- `backend/app/exporters/template_exporter.py`
- `backend/tests/test_export_api.py`

## Verification
- Passed: `.\.venv\Scripts\python.exe -m pytest backend/tests/test_export_fixture_support.py backend/tests/test_export_api.py -x -p no:cacheprovider` (13/13)

## Requirements Covered
- `VER-01`: Export verification can resolve both required templates from repo-controlled fixtures or explicit configuration without editing test code.
- `VER-02`: Missing repo fixtures, samples, or explicit template paths now fail loudly instead of downgrading into silent discovery fallback.

## Task Commits
- `8bbe15d` `test(03-01): add failing export fixture helper tests`
- Remaining Wave 1 follow-up edits are currently present in the workspace and verified by pytest, but not committed yet.

## Notes
- `template_exporter.py` already had unrelated local modifications in the worktree; Phase 3 changes were limited to manifest-aware template discovery and were applied without reverting those unrelated edits.
- This environment cannot write to the default pytest temp/cache locations reliably, so verification uses repo-local artifact directories and `-p no:cacheprovider`.
