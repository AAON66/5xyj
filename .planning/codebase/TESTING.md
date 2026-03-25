# Testing Patterns

**Analysis Date:** 2026-03-25

## Test Framework

**Runner:**
- `pytest` 8.3.4 from `backend/requirements.txt`
- Config: Not detected. There is no `pytest.ini`, `.coveragerc`, `pyproject.toml`, or `conftest.py` in the project root, `backend/`, or `backend/tests/`.

**Assertion Library:**
- Native `assert` statements with `pytest` markers and skipping.
- API tests use `fastapi.testclient.TestClient`.

**Run Commands:**
```bash
pytest backend/tests                    # Run backend test suite
pytest backend/tests -k region_sample   # Run real-sample regression slice
pytest backend/tests -k exporter        # Run dual-template export slice
```

Watch mode:
```bash
Not configured
```

Coverage:
```bash
Not configured
```

## Test File Organization

**Location:**
- Backend tests are in `backend/tests/`.
- Root `tests/README.md` exists, but the active automated suite lives under `backend/tests/`.
- No frontend test files were detected under `frontend/src/`.

**Naming:**
- File names are `test_<feature>.py`. Examples: `backend/tests/test_import_batches_api.py`, `backend/tests/test_header_normalizer.py`, `backend/tests/test_region_sample_regression.py`.
- Test functions are descriptive `test_<behavior>()` names that read as executable specifications.

**Structure:**
```text
backend/tests/
├── test_*_api.py                  # FastAPI endpoint coverage
├── test_*_service.py              # Business logic / workflow services
├── test_*_regression.py           # Real Excel sample and template regressions
├── test_workbook_*.py             # Parser/discovery heuristics
└── test_runtime_config.py         # Configuration behavior
```

## Test Structure

**Suite Organization:**
```python
def test_parse_and_preview_import_batch_return_normalized_preview() -> None:
    client, _ = build_test_client('parse_preview')
    sample_path = find_sample('深圳创造欢乐')

    with client:
        created = client.post('/api/v1/imports', ...)
        batch_id = created.json()['data']['id']
        parse_response = client.post(f'/api/v1/imports/{batch_id}/parse')

    assert parse_response.status_code == 200
    assert parse_response.json()['data']['status'] == 'normalized'
```

**Patterns:**
- Tests favor arrange/act/assert in a single function with very little abstraction.
- Per-file helpers are preferred over shared fixtures. Examples: `build_test_client()` and `find_sample()` in `backend/tests/test_import_batches_api.py`, `clone_record()` in `backend/tests/test_validation_service.py`.
- Context managers are used around `TestClient` for cleanup and startup hooks.
- Real sample files are discovered dynamically and skipped if absent using `pytest.skip(...)`.

## Mocking

**Framework:** `pytest` + `monkeypatch`

**Patterns:**
```python
monkeypatch.setattr(
    llm_mapping_module,
    "get_settings",
    lambda: Settings(deepseek_api_key="test-key", enable_llm_fallback=False),
)
monkeypatch.setattr(llm_mapping_module.httpx, "AsyncClient", lambda **kwargs: client)
```

**What to Mock:**
- External HTTP calls to DeepSeek in `backend/tests/test_llm_mapping_service.py`.
- Settings retrieval when a test needs specific env-free behavior.
- Service internals only when the purpose is downgrade/fallback behavior, not spreadsheet parsing.

**What NOT to Mock:**
- Workbook parsing and normalization for regression coverage. These tests intentionally use real files from `data/samples/`.
- Export generation when validating template cell placement. `backend/tests/test_template_exporter_regression.py` loads actual workbooks with `openpyxl`.
- FastAPI routing for endpoint tests. API suites build a full app with an isolated SQLite database instead of mocking route internals.

## Fixtures and Factories

**Test Data:**
```python
ARTIFACTS_ROOT = ROOT_DIR / '.test_artifacts' / 'import_batches_api'
SAMPLES_DIR = ROOT_DIR / 'data' / 'samples'

def find_sample(keyword: str) -> Path:
    for path in sorted(SAMPLES_DIR.glob('*.xlsx')):
        if keyword in path.name:
            return path
    pytest.skip(...)
```

**Location:**
- Real spreadsheet fixtures live in `data/samples/` and `data/samples/公积金/`.
- Test-generated databases, uploads, and export outputs are written under `.test_artifacts/`.
- Export regression tests also probe configured desktop templates if present, falling back to `Path.home() / "Desktop" / "202602社保公积金台账" / "202602社保公积金汇总"` in `backend/tests/test_template_exporter_regression.py`.

**Factory Style:**
- There is no shared factory framework. Tests create state inline with helpers like `build_test_client()` or direct ORM/model construction.
- When a test needs modified normalized records, it clones an existing real record and mutates only the relevant fields. See `clone_record()` in `backend/tests/test_validation_service.py`.

## Coverage

**Requirements:** None enforced by tooling.

**Observed coverage shape:**
- Strong backend coverage across API, parsing, normalization, LLM fallback, matching, validation, export, and runtime configuration.
- 29 backend test modules under `backend/tests/`.
- Regression coverage is unusually strong for Excel structure diversity because `backend/tests/test_region_sample_regression.py` and `backend/tests/test_header_normalizer.py` exercise Guangzhou, Hangzhou, Xiamen, Shenzhen, Wuhan, and Changsha samples.
- Frontend has no automated test coverage for routes, hooks, contexts, or service modules.

**View Coverage:**
```bash
Not configured
```

## Test Types

**Unit Tests:**
- Pure helper and service behavior is tested directly. Examples:
- `backend/tests/test_validation_service.py` for required fields, ID format, totals, and duplicates.
- `backend/tests/test_non_detail_row_filter.py` for row classification.
- `backend/tests/test_workbook_discovery.py` and `backend/tests/test_header_extraction.py` for parsing heuristics.

**Integration Tests:**
- FastAPI endpoint suites spin up an app plus SQLite database and hit HTTP routes end-to-end. Examples:
- `backend/tests/test_import_batches_api.py`
- `backend/tests/test_export_api.py`
- `backend/tests/test_validation_matching_api.py`
- Template exporter regression uses actual workbook templates and emitted `.xlsx` files in `backend/tests/test_template_exporter_regression.py`.

**E2E Tests:**
- Browser/UI E2E tests are not used.
- No Playwright, Cypress, Vitest, or React Testing Library config was detected for `frontend/`.

## Common Patterns

**Async Testing:**
```python
@pytest.mark.anyio
async def test_llm_service_skips_when_api_key_missing(monkeypatch) -> None:
    monkeypatch.setattr(llm_mapping_module, "get_settings", lambda: Settings(deepseek_api_key=""))
    result = await map_header_with_llm("未知字段 / 金额", region="guangzhou")
    assert result.status == "skipped_no_api_key"
```

**Error Testing:**
```python
with client:
    response = client.post('/api/v1/imports/missing-batch/parse')

assert response.status_code == 404
assert response.json()['error']['code'] == 'not_found'
```

**Database Isolation:**
```python
database_path = artifacts_dir / 'imports.db'
settings = Settings(database_url=f'sqlite:///{database_path.as_posix()}', ...)
engine = create_database_engine(settings)
Base.metadata.create_all(engine)
```

**Regression via Real Samples:**
```python
result = standardize_workbook(sample_path, region=case.region)
assert result.records or result.filtered_rows
assert result.raw_header_signature
```

## Notable Gaps

**Frontend coverage gap:**
- `frontend/src/` has no `.test.*` or `.spec.*` files.
- Critical UI flows in `frontend/src/pages/Imports.tsx`, `frontend/src/pages/SimpleAggregate.tsx`, `frontend/src/components/AuthProvider.tsx`, and `frontend/src/services/api.ts` are currently protected only by manual testing.

**Shared fixture gap:**
- No `conftest.py` exists. Helper setup is duplicated across files, especially database/bootstrap logic in API tests.

**Coverage reporting gap:**
- There is no coverage threshold, HTML report workflow, or branch coverage signal.

**Watch/dev-test gap:**
- No watch-mode or frontend unit-test command exists in `frontend/package.json`.

**Template dependency risk:**
- `backend/tests/test_template_exporter_regression.py` depends on configured template paths or a specific Desktop folder. This is good for realism but makes suite portability weaker on fresh machines and CI.

**End-to-end workflow gap:**
- The backend pipeline is well covered, but there is no single automated test that drives the browser upload flow through `frontend/src/pages/SimpleAggregate.tsx` or `frontend/src/pages/Imports.tsx`.

## Guidance For New Tests

- Put new backend tests in `backend/tests/test_<feature>.py` and keep helpers local unless three or more files clearly need the same setup.
- Prefer real files from `data/samples/` when validating workbook discovery, header inference, row filtering, normalization, or export regressions.
- Use `.test_artifacts/<suite_name>/` for emitted databases, uploads, and exports so tests remain inspectable and isolated.
- For external integrations such as DeepSeek, mock only the network client and keep request/response parsing real.
- If frontend behavior changes, add a frontend test runner before expanding page complexity further; the current repo has no automated safety net for React state, routing, or auth/session flows.

---

*Testing analysis: 2026-03-25*
