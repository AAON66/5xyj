# Testing Patterns

**Analysis Date:** 2026-03-27

## Test Framework

**Runner:**
- pytest 8.3.4
- Config: No `conftest.py`, `pytest.ini`, `pyproject.toml`, or `setup.cfg` detected for pytest configuration
- Tests discovered by default pytest conventions in `backend/tests/`

**Assertion Library:**
- Built-in `assert` statements (pytest native)
- `pytest.skip()` for conditional skipping when sample files are missing
- `pytest.fail()` for hard failures in fixture support code
- `pytest.mark.parametrize` for parameterized tests

**Run Commands:**
```bash
pytest                     # Run all tests
pytest backend/tests/      # Run backend tests only
pytest -k "test_health"    # Run specific test
```

**Frontend Testing:**
- No frontend test framework detected
- No test files in `frontend/src/`
- No `vitest`, `jest`, or testing-library in `frontend/package.json`

## Test File Organization

**Location:**
- All tests in `backend/tests/` (separate directory, not co-located)
- Support/fixture files in `backend/tests/support/`

**Naming:**
- Test files: `test_<module_or_feature>.py`
- Test functions: `test_<description_of_behavior>()` with descriptive snake_case names
- No test classes used; all tests are standalone functions

**Structure:**
```
backend/tests/
├── support/
│   └── export_fixtures.py          # Shared test helpers for export tests
├── test_aggregate_api.py
├── test_aggregate_service.py
├── test_app_initialization.py
├── test_auth_api.py
├── test_batch_runtime_service.py
├── test_compare_api.py
├── test_dashboard_api.py
├── test_employee_master_api.py
├── test_export_api.py
├── test_export_fixture_support.py
├── test_header_extraction.py
├── test_header_normalizer.py
├── test_health.py
├── test_housing_fund_service.py
├── test_import_batches_api.py
├── test_llm_mapping_service.py
├── test_mapping_api.py
├── test_matching_service.py
├── test_non_detail_row_filter.py
├── test_normalization_service.py
├── test_region_detection_service.py
├── test_region_sample_regression.py
├── test_runtime_config.py
├── test_schema.py
├── test_template_exporter.py
├── test_template_exporter_regression.py
├── test_validation_matching_api.py
├── test_validation_service.py
├── test_workbook_discovery.py
└── test_workbook_loader.py
```

## Test Structure

**Suite Organization:**
```python
# No conftest.py - each test file self-contains its setup
from __future__ import annotations

from pathlib import Path
import pytest
from backend.app.core.config import ROOT_DIR

SAMPLES_DIR = ROOT_DIR / "data" / "samples"

def find_sample(keyword: str) -> Path:
    """Helper duplicated across test files to locate sample Excel files."""
    for path in sorted(SAMPLES_DIR.glob("*.xlsx")):
        if keyword in path.name:
            return path
    pytest.skip(f"Sample containing {keyword!r} was not found in {SAMPLES_DIR}.")

def test_specific_behavior() -> None:
    # Arrange
    sample_path = find_sample("广分")
    # Act
    result = some_service_function(sample_path)
    # Assert
    assert result.some_field == expected_value
```

**Patterns:**
- No `setUp`/`tearDown` or fixtures; each test is self-contained
- Helper functions defined at module level within each test file
- `find_sample()` helper is duplicated across multiple test files (see Concerns)
- Tests use real Excel sample files from `data/samples/` when available
- `pytest.skip()` used when sample files are absent (graceful degradation)

## Test Categories

**Unit Tests (pure logic, no DB):**
- `backend/tests/test_non_detail_row_filter.py` - Row classification logic
- `backend/tests/test_header_normalizer.py` - Header-to-canonical-field mapping
- `backend/tests/test_normalization_service.py` - Data standardization
- `backend/tests/test_region_detection_service.py` - Region auto-detection
- `backend/tests/test_matching_service.py` - Employee ID matching logic
- `backend/tests/test_validation_service.py` - Data validation rules
- `backend/tests/test_llm_mapping_service.py` - LLM fallback mapping
- `backend/tests/test_header_extraction.py` - Header structure parsing
- `backend/tests/test_workbook_discovery.py` - Sheet discovery
- `backend/tests/test_workbook_loader.py` - Workbook loading

**Integration Tests (API with in-memory DB):**
- `backend/tests/test_import_batches_api.py` - Import batch CRUD via HTTP
- `backend/tests/test_export_api.py` - Export pipeline via HTTP
- `backend/tests/test_auth_api.py` - Authentication endpoints
- `backend/tests/test_dashboard_api.py` - Dashboard stats endpoint
- `backend/tests/test_mapping_api.py` - Header mapping CRUD endpoint
- `backend/tests/test_employee_master_api.py` - Employee master endpoint
- `backend/tests/test_compare_api.py` - Batch comparison endpoint
- `backend/tests/test_aggregate_api.py` - Aggregate endpoint
- `backend/tests/test_validation_matching_api.py` - Validation + matching endpoint
- `backend/tests/test_health.py` - Health check endpoint

**Regression Tests:**
- `backend/tests/test_region_sample_regression.py` - Multi-region parsing regression
- `backend/tests/test_template_exporter_regression.py` - Export template regression

**E2E Tests:**
- None detected. No browser-based or Playwright/Cypress tests.

## API Integration Test Pattern

**Setup pattern for API tests (from `backend/tests/test_import_batches_api.py`):**
```python
def build_test_client(test_name: str, **overrides: object) -> tuple[TestClient, Settings]:
    artifacts_dir = ARTIFACTS_ROOT / test_name
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    database_path = artifacts_dir / 'imports.db'
    settings = Settings(
        app_name='导入测试',
        auth_enabled=False,
        database_url=f'sqlite:///{database_path.as_posix()}',
        upload_dir=str(artifacts_dir / 'uploads'),
        outputs_dir=str(artifacts_dir / 'outputs'),
        log_format='plain',
        **overrides,
    )

    engine = create_database_engine(settings)
    session_factory = create_session_factory(settings)
    Base.metadata.create_all(engine)

    app = create_app(settings)

    def override_get_db():
        db: Session = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client, settings
```

**Key characteristics:**
- Each test gets its own SQLite database and filesystem artifacts directory under `.test_artifacts/`
- FastAPI dependency injection overridden for database session
- Auth disabled for test simplicity (`auth_enabled=False`)
- `TestClient` from `fastapi.testclient` (wraps `starlette.testclient`)
- `build_test_client()` helper is duplicated across API test files with slight variations

## Mocking

**Framework:** No dedicated mocking library (no `unittest.mock`, `pytest-mock` in requirements)

**Approach:**
- Tests primarily use real implementations with real Excel sample files
- API tests use SQLite in-memory databases instead of mocking the DB layer
- FastAPI dependency overrides used instead of mocking: `app.dependency_overrides[get_db] = override_get_db`
- `pytest.skip()` for tests that require sample files not present

**What is NOT mocked:**
- Excel parsing (uses real `.xlsx` files from `data/samples/`)
- Database operations (uses real SQLite databases in `.test_artifacts/`)
- Service layer logic (tested with real inputs)

## Fixtures and Factories

**Test Data:**
```python
# Factory function pattern from test_matching_service.py
def make_employee(
    employee_id: str,
    person_name: str,
    *,
    id_number: Optional[str] = None,
    company_name: Optional[str] = None,
    active: bool = True,
    record_id: Optional[str] = None,
) -> EmployeeMaster:
    return EmployeeMaster(
        id=record_id or f'emp-{employee_id}',
        employee_id=employee_id,
        person_name=person_name,
        id_number=id_number,
        company_name=company_name,
        active=active,
    )
```

**Shared Fixtures Location:**
- `backend/tests/support/export_fixtures.py` - Export template helpers
  - `resolve_required_export_templates()` - Locates regression template files
  - `require_sample_workbook()` - Locates sample Excel files, fails if missing
  - `create_placeholder_template_pair()` - Creates minimal placeholder templates for tests

**Sample Data:**
- Real Excel files in `data/samples/` (Guangzhou, Hangzhou, Xiamen, Shenzhen, Wuhan, Changsha)
- Regression templates in `data/templates/regression/` with `manifest.json`

## Coverage

**Requirements:** None enforced. No coverage configuration detected.

**No coverage tools in `backend/requirements.txt`** (no `pytest-cov` or `coverage`).

## Parametrized Testing

**Pattern used in `backend/tests/test_non_detail_row_filter.py`:**
```python
@pytest.mark.parametrize(
    ("row_values", "expected_reason"),
    [
        (["小计", None, None], "summary_subtotal"),
        (["退休人员", None, None], "group_header"),
        (["家属统筹人员", None, None], "group_header"),
        ([None, "", "--"], "blank_row"),
        (["姓名", "身份证号码"], "header_row"),
    ],
)
def test_classify_row_filters_known_non_detail_shapes(row_values, expected_reason):
    decision = classify_row(row_values, row_number=12)
    assert decision.keep is False
    assert decision.reason == expected_reason
```

**Also used in `backend/tests/test_header_normalizer.py`:**
```python
@pytest.mark.parametrize(
    ("signature", "expected_status"),
    [
        ("险种", "skipped_irrelevant"),
        ("单位部分 / 应缴费额（元）", "skipped_irrelevant"),
        ("数据来源", "skipped_irrelevant"),
    ],
)
def test_normalize_header_column_skips_llm_for_auxiliary_headers(signature, expected_status):
    ...
```

## Test Artifact Management

- API and export tests write artifacts to `D:/execl_mix/.test_artifacts/<test_category>/<test_name>/`
- Each test cleans its artifact directory before running (`shutil.rmtree` + `mkdir`)
- Artifact directories contain: SQLite databases, uploaded files, export outputs
- `.test_artifacts/` directory is not gitignored (potential concern)

## Test Coverage Gaps

**No Frontend Tests:**
- Zero test files in `frontend/src/`
- No test runner configured for frontend
- No testing-library, vitest, or jest in dependencies
- All React components, hooks, services, and utilities are untested
- **Priority: High** - Frontend has significant logic in pages (state management, API calls, data formatting)

**No conftest.py:**
- `find_sample()` helper duplicated across at least 5 test files
- `build_test_client()` helper duplicated across API test files
- No shared pytest fixtures for common test setup
- **Priority: Medium** - Causes maintenance burden

**No E2E Tests:**
- No browser-based testing (Playwright, Cypress)
- Full user flows (upload -> parse -> validate -> match -> export) only tested at API level
- **Priority: Medium** - Critical user flows untested end-to-end

**Missing Coverage Tooling:**
- No `pytest-cov` in requirements
- No coverage thresholds or reports
- Cannot measure which code paths are tested
- **Priority: Medium**

**LLM Fallback Degradation:**
- `backend/tests/test_llm_mapping_service.py` exists but unclear if it tests no-API-key degradation path
- **Priority: Medium** - CLAUDE.md mandates testing degradation logic

**Housing Fund Tests:**
- `backend/tests/test_housing_fund_service.py` exists but housing fund is a newer feature
- Coverage of housing fund parsing edge cases unknown
- **Priority: Low**

---

*Testing analysis: 2026-03-27*
