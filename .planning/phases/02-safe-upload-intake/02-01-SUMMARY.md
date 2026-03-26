# 02-01 Summary

## Outcome
- Added `UploadTooLargeError` so streamed upload overflows now fail through an explicit service-layer path instead of relying only on `content-length`.
- Updated `import_service._store_upload()` to enforce `settings.max_upload_size_bytes` while chunks are read, so missing or understated `content-length` can no longer bypass upload limits.
- Preserved deterministic cleanup: oversized uploads remove any partial file, roll back the batch, and leave `/api/v1/imports` with no persisted batch artifact.
- Updated `/api/v1/imports` and `/api/v1/aggregate` to return HTTP 413 for streamed oversized uploads, and `/api/v1/aggregate/stream` now emits `payload_too_large` for the same condition.
- Added regression coverage for missing/incorrect `content-length` on imports and aggregate, while keeping the existing import parse flow, aggregate happy path, and upload-guard fast path green.

## Files Changed
- `backend/app/services/import_service.py`
- `backend/app/api/v1/imports.py`
- `backend/app/api/v1/aggregate.py`
- `backend/tests/test_import_batches_api.py`
- `backend/tests/test_aggregate_api.py`

## Verification
- Passed: `.\.venv\Scripts\python.exe -m pytest backend/tests/test_import_batches_api.py backend/tests/test_aggregate_api.py backend/tests/test_app_initialization.py -x` (38/38)

## Requirements Covered
- `PIPE-01`: Streamed uploads now enforce the configured size limit even when `content-length` is missing or understated.
- `PIPE-02`: Oversized uploads now fail with explicit 413 / `payload_too_large` responses and clean up partial artifacts.
- `PIPE-03`: Existing import and aggregate regression coverage still passes after the hardening change, including dual-template export coverage.

## Task Commits
- `cb8f25f` `test(02-01): add failing oversized upload regressions`
- `d585c74` `feat(02-01): enforce streamed upload size limits`

## Notes
- `UploadGuardMiddleware` remains the early header-based optimization; service-layer streaming enforcement is now the source of truth.
- `backend/tests/test_app_initialization.py` needed no edits because the existing middleware fast-path regression already covered the intended behavior.
