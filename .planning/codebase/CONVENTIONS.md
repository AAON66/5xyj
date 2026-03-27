# Coding Conventions

**Analysis Date:** 2026-03-27

## Naming Patterns

**Files (Backend Python):**
- Modules use `snake_case.py`: `import_service.py`, `header_normalizer.py`, `non_detail_row_filter.py`
- Models are singular nouns: `source_file.py`, `import_batch.py`, `employee_master.py`
- API route modules match their resource name: `imports.py`, `employees.py`, `dashboard.py`
- Schemas mirror their domain: `imports.py`, `employees.py`, `dashboard.py`
- Test files use `test_` prefix: `test_header_normalizer.py`, `test_import_batches_api.py`

**Files (Frontend TypeScript):**
- Components use `PascalCase.tsx`: `AppShell.tsx`, `PageContainer.tsx`, `SurfaceNotice.tsx`
- Pages use `PascalCase.tsx`: `Imports.tsx`, `Dashboard.tsx`, `Employees.tsx`
- Services use `camelCase.ts`: `api.ts`, `imports.ts`, `dashboard.ts`, `authSession.ts`
- Hooks use `camelCase.ts` with `use` prefix: `useAuth.ts`, `useApiFeedback.ts`, `useAggregateSession.ts`
- Utilities use `camelCase.ts`: `format.ts`
- Config files use `camelCase.ts`: `env.ts`

**Functions (Backend):**
- Service functions use `snake_case` verbs: `create_import_batch()`, `normalize_header_column()`, `validate_batch()`
- Helper functions prefixed with underscore for private: `_normalize()`, `_looks_numeric()`, `_match_non_detail_token()`
- Error classes use `PascalCase` with descriptive suffix: `BatchNotFoundError`, `InvalidUploadError`, `ExportBlockedError`

**Functions (Frontend):**
- React components use `PascalCase` named exports: `export function ImportsPage()`, `export function PageContainer()`
- Hooks use `camelCase` with `use` prefix: `useAuth()`, `useApiFeedback()`
- Utility functions use `camelCase`: `formatDateTime()`, `normalizeApiError()`

**Variables (Backend):**
- Constants use `UPPER_SNAKE_CASE`: `NON_DETAIL_TOKENS`, `SAMPLES_DIR`, `ROOT_DIR`
- Tuple constants also use `UPPER_SNAKE_CASE`: `LLM_RELEVANCE_KEYWORDS`, `EXPLICIT_SKIP_SIGNATURE_KEYWORDS`
- Local variables use `snake_case`: `kept_rows`, `normalized_values`, `first_value`

**Variables (Frontend):**
- Constants use `UPPER_SNAKE_CASE`: `DEFAULT_REQUEST_TIMEOUT_MS`, `PRESET_REGIONS`
- State variables use `camelCase`: `selectedBatchId`, `pageLoading`, `submitting`
- Interfaces use `PascalCase`: `ApiSuccessResponse`, `ImportBatchSummary`, `HeaderMappingPreview`

**Types (Backend):**
- Pydantic schemas use `PascalCase` with `Read`/`Input` suffix: `ImportBatchSummaryRead`, `DeleteImportBatchesInput`
- SQLAlchemy models use `PascalCase` singular: `SourceFile`, `ImportBatch`, `EmployeeMaster`
- Enums use `PascalCase` with descriptive name: `BatchStatus`, `MatchStatus`, `TemplateType`
- Enum values use `UPPER_SNAKE_CASE` in class, `lower_snake_case` as string values: `UPLOADED = "uploaded"`
- Dataclasses use `PascalCase`: `RowFilterDecision`, `FilteredRowsResult`, `HeaderColumn`

**Types (Frontend):**
- Interfaces use `PascalCase`: `ApiSuccessResponse<T>`, `ImportBatchSummary`
- Props interfaces use `PascalCase` with `Props` suffix: `PageContainerProps`

## Code Style

**Formatting (Backend):**
- No dedicated formatter config file detected (no `pyproject.toml`, `setup.cfg`, or `.flake8`)
- Consistent single-quote strings in Python: `'ok'`, `'imports'`
- Line length appears to follow ~120 character soft limit
- All Python files start with `from __future__ import annotations`

**Formatting (Frontend):**
- ESLint with `typescript-eslint` recommended rules: `frontend/eslint.config.js`
- No Prettier config file detected
- Mix of single quotes in `.tsx`/`.ts` files: `'react'`, `'../services/api'`
- TypeScript strict mode enabled: `frontend/tsconfig.json`

**Linting (Frontend):**
- ESLint 9 flat config at `frontend/eslint.config.js`
- Plugins: `react-hooks`, `react-refresh`
- Rules: `react-hooks/recommended`, `react-refresh/only-export-components` (warn, allowConstantExport)
- Run via: `npm run lint`

## Import Organization

**Backend Python (observed order):**
1. `from __future__ import annotations` (always first)
2. Standard library imports: `typing`, `pathlib`, `datetime`, `dataclasses`, `uuid`, `json`
3. Third-party imports: `fastapi`, `sqlalchemy`, `pydantic`, `openpyxl`, `pytest`
4. Internal imports: `backend.app.core.*`, `backend.app.models.*`, `backend.app.services.*`

**Example from `backend/app/api/v1/imports.py`:**
```python
from __future__ import annotations

from typing import Optional

import json
from datetime import datetime, timezone
from json import JSONDecodeError
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import success_response
from backend.app.dependencies import get_db
```

**Frontend TypeScript (observed order):**
1. React/library imports: `react`, `react-router-dom`, `axios`
2. Internal component imports: `'../components'`
3. Internal service/hook imports: `'../services/api'`, `'../hooks'`

**Example from `frontend/src/pages/Imports.tsx`:**
```typescript
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { PageContainer, SectionState, SurfaceNotice } from '../components';
import { normalizeApiError } from '../services/api';
import { bulkDeleteImportBatches, createImportBatch, ... } from '../services/imports';
```

**Path Aliases:**
- None configured. All imports use relative paths: `'../components'`, `'../services/api'`
- Backend uses absolute dotted paths: `backend.app.core.config`, `backend.app.services.import_service`

## Error Handling

**Backend API Layer Pattern:**
- Service functions raise domain-specific exceptions (e.g., `BatchNotFoundError`, `InvalidUploadError`)
- API route handlers catch domain exceptions and convert to `HTTPException` with appropriate status codes
- Use `raise ... from exc` pattern for exception chaining
- Global exception handlers in `backend/app/main.py` catch unhandled `HTTPException`, `RequestValidationError`, and `Exception`

**Example pattern from `backend/app/api/v1/imports.py`:**
```python
try:
    batch = get_import_batch(db, batch_id)
except BatchNotFoundError as exc:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
```

**Backend Standardized Response Envelope:**
- All responses go through `success_response()` or `error_response()` from `backend/app/api/v1/responses.py`
- Success: `{"success": true, "message": "...", "data": {...}}`
- Error: `{"success": false, "error": {"code": "...", "message": "...", "details": ...}}`

**Frontend Error Pattern:**
- `ApiClientError` class wraps all API errors with `statusCode`, `code`, `details`, `raw`
- `normalizeApiError()` in `frontend/src/services/api.ts` converts any error to `ApiClientError`
- Axios interceptors handle 401 (clear auth session) and timeouts automatically
- Pages manage error state locally: `const [pageError, setPageError] = useState<string | null>(null)`

## Logging

**Framework:** Python `logging` module configured in `backend/app/core/logging.py`

**Configuration:**
- Supports two formats via `log_format` setting: `'json'` (default) or `'plain'`
- JSON format: `{"level":"INFO","logger":"backend.app","message":"..."}`
- Plain format: `%(levelname)s [%(name)s] %(message)s`
- Log level configurable via `log_level` setting (default: `'INFO'`)

**Note:** `loguru` is in `backend/requirements.txt` but the actual logging setup uses stdlib `logging`. This may be leftover or planned for migration.

**Frontend:** No structured logging framework. Uses implicit error propagation through `ApiClientError` and UI state.

## Comments

**When to Comment:**
- Minimal inline comments in production code
- Chinese comments appear in UI-facing strings and some domain logic
- No JSDoc/TSDoc usage observed in frontend
- No Python docstrings observed on functions or classes

**Documentation Style:**
- Project documentation primarily in `CLAUDE.md` (Chinese + English)
- No inline API documentation beyond FastAPI's auto-generated docs

## Function Design

**Backend Service Functions:**
- Accept primitive arguments (db session, batch_id, settings) rather than request objects
- Return Pydantic schema instances or domain dataclasses
- Side effects (DB writes, file I/O) are explicit in the function name: `create_import_batch`, `delete_import_batch`
- Pure logic functions are stateless: `classify_row()`, `normalize_header_column()`

**Frontend Service Functions:**
- Thin wrappers around `apiClient` (axios) calls
- Return typed response data, throw `ApiClientError` on failure
- Accept plain parameters matching API contract

**Frontend Components:**
- Use function components exclusively (no class components)
- Props defined via TypeScript interfaces
- State managed with `useState` hooks (no external state library)

## Module Design

**Exports (Backend):**
- Barrel file at `backend/app/services/__init__.py` re-exports all public service functions and types
- Barrel file at `backend/app/models/__init__.py` (assumed, standard pattern)
- Explicit `__all__` list in `backend/app/services/__init__.py`

**Exports (Frontend):**
- Barrel files at `frontend/src/components/index.ts`, `frontend/src/pages/index.ts`, `frontend/src/hooks/index.ts`, `frontend/src/utils/index.ts`
- Use `export * from "./ComponentName"` pattern
- Components use named exports: `export function PageContainer(...)`

**Backend Module Layout:**
- `backend/app/api/v1/` - Route handlers (thin, delegate to services)
- `backend/app/services/` - Business logic (stateless functions)
- `backend/app/models/` - SQLAlchemy ORM models
- `backend/app/schemas/` - Pydantic request/response schemas
- `backend/app/parsers/` - Excel parsing logic
- `backend/app/validators/` - Data validation/filtering
- `backend/app/mappings/` - Header synonym rules
- `backend/app/exporters/` - Template export logic
- `backend/app/core/` - Config, database, auth, logging

---

*Convention analysis: 2026-03-27*
