# 02 Research

## Research Goal
Determine how to harden upload intake for Phase 2 so oversized or malformed uploads fail safely during streaming, cleanup is deterministic, and the existing import and aggregate flows remain intact.

## Current State

### 1. Request boundary protection exists, but only for trustworthy `content-length`
- `backend/app/core/upload_guard.py` checks multipart requests only when `content-length` is present.
- If `content-length` is missing, invalid, or understated, the middleware allows the request through.
- Current middleware behavior is still worth preserving as a cheap early rejection path for obviously oversized requests.

### 2. The real write path is in `import_service._store_upload()`
- `backend/app/services/import_service.py:_store_upload()` writes the upload stream chunk by chunk.
- It already tracks `file_size` and hashes the file while writing.
- It does **not** stop writing when `file_size` exceeds `settings.max_upload_size_bytes`.
- This is the concrete bypass for `PIPE-01`.

### 3. Cleanup semantics already exist and should be reused
- `create_import_batch()` wraps `_store_upload()` inside a try/except that deletes saved files, removes empty batch directories, and deletes the persisted `ImportBatch` row on failure.
- `_store_upload()` itself also deletes the partially written file when an exception occurs.
- This is the best seam for `PIPE-02`: fail early inside `_store_upload()` and let existing batch rollback logic finish the cleanup.

### 4. Two entry paths depend on the same upload storage behavior
- `/api/v1/imports` uses `create_import_batch()` directly via `backend/app/api/v1/imports.py`.
- `/api/v1/aggregate` also uses `create_import_batch()` via `backend/app/services/aggregate_service.py`.
- Hardening the shared storage path is preferable to duplicating upload-limit logic in multiple endpoints.

## Recommended Implementation Direction

### A. Keep middleware as fast-path, move authoritative enforcement into `_store_upload()`
Recommended behavior:
- Keep `UploadGuardMiddleware` for immediate 413 rejection when `content-length` is present and clearly oversized.
- Add authoritative stream-time enforcement inside `_store_upload()` by checking `file_size` after each chunk write or before persisting the chunk.
- When the accumulated size crosses `settings.max_upload_size_bytes`, raise a dedicated upload-size exception immediately.

Why:
- This closes the header-bypass gap.
- It avoids redesigning request parsing or middleware buffering.
- It centralizes protection where bytes are actually written to disk.

### B. Introduce a dedicated streamed overflow exception
Recommended shape:
- Reuse `InvalidUploadError` only if keeping API status `400` is acceptable, or add a narrower subclass such as `UploadTooLargeError(InvalidUploadError)`.
- Translate that exception to HTTP `413 Payload Too Large` in `backend/app/api/v1/imports.py` and any aggregate API boundary that currently handles upload errors.

Why:
- Phase 2 explicitly calls for explainable API failures.
- A dedicated exception keeps cleanup logic distinct from extension validation, metadata mismatch, or empty-file failures.

### C. Delete partial files before surfacing the error
Recommended behavior inside `_store_upload()`:
- If streamed size exceeds the limit, close the handle, delete the partially written file, and raise the overflow exception.
- Let `create_import_batch()` continue to clean up batch-level artifacts and DB state.

Why:
- Prevents ambiguous leftover files.
- Preserves the current rollback structure instead of adding a second cleanup path higher in the stack.

### D. Preserve success-path behavior for normal regional samples
Do **not** change:
- File naming rules, extension rules, hashing, or region detection order.
- The parse/normalize/validate/match/export sequence used by `parse_import_batch()` and `run_simple_aggregate()`.
- The aggregate progress event contract unless the new upload failure path requires an explicit additional failure event.

## Testing Strategy

### Import API coverage
Extend `backend/tests/test_import_batches_api.py` to prove:
- oversized upload with honest `content-length` still fails as before
- oversized upload with missing `content-length` now fails during streaming
- oversized upload with understated `content-length` now fails during streaming
- failed streamed upload leaves no persisted batch row and no uploaded file artifact behind

### Middleware / app initialization coverage
Keep `backend/tests/test_app_initialization.py` focused on middleware fast-path behavior:
- verify the existing header-based 413 still works
- do not overload this file with service-level streamed-write tests

### Aggregate regression coverage
Extend `backend/tests/test_aggregate_api.py` or `backend/tests/test_aggregate_service.py` to prove:
- aggregate happy path still works after upload hardening
- a streamed oversize on aggregate input fails cleanly instead of leaving the system in a partially uploaded state

### Required regression scope for `PIPE-03`
Before Phase 2 is considered done, rerun supported regional happy paths through at least:
- one `/api/v1/imports` parse/preview flow using a real regional sample
- one `/api/v1/aggregate` export flow using existing regression samples/templates

This preserves confidence that upload hardening did not break the core pipeline.

## Risks To Plan Around
- If the new streamed-overflow exception is mapped inconsistently between `/imports` and `/aggregate`, user-facing failure semantics will drift.
- If cleanup happens only in `create_import_batch()` but not in `_store_upload()`, partial files may survive on abrupt streamed overflow paths.
- If tests only hit middleware rejection, the real bypass in `_store_upload()` will remain unprotected.
- If the plan changes upload storage semantics too broadly, Phase 2 can accidentally destabilize region detection and downstream parsing, violating `PIPE-03`.

## Recommended Plan Shape
One plan is probably enough if scoped tightly:
1. Harden stream-time enforcement and cleanup in `import_service` and API error translation.
2. Add regression tests for import and aggregate oversized/malformed upload paths plus pipeline happy-path preservation.

## Research Conclusion
The safest and smallest viable Phase 2 approach is to keep header-based middleware as an optimization, make `_store_upload()` the authoritative upload-size enforcement point, surface a deterministic oversized-upload error, and prove through API-level regression tests that both `/api/v1/imports` and `/api/v1/aggregate` still work for supported regional samples.