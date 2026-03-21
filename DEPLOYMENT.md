# Deployment And Integration Guide

## 1. Scope

This document describes how to run the current project locally, what has been verified, and what is still intentionally incomplete.

Current completed areas:
- import batch creation and file upload
- workbook discovery and header extraction
- rule-first field normalization with DeepSeek fallback hooks
- non-detail row filtering
- standardized preview generation
- validation and employee matching runtime
- dual-template export
- dashboard and operator-facing frontend pages
- regression coverage for regional parsing, dual-template export, and DeepSeek fallback behavior

Current remaining limitation area:
- employee master workflow now supports import and listing, but not fine-grained edit/delete administration yet

## 2. Runtime Prerequisites

Required:
- Python 3.11+
- Node.js 18+
- a reachable database from `DATABASE_URL`
- local output directories with write permission
- both export templates available through `SALARY_TEMPLATE_PATH` and `FINAL_TOOL_TEMPLATE_PATH`

Optional:
- `DEEPSEEK_API_KEY` for live fallback calls

## 3. Environment Setup

Create `.env` in the repository root from `.env.example`.

Recommended minimum fields:

```env
DATABASE_URL=sqlite:///./data/app.db
UPLOAD_DIR=./data/uploads
SAMPLES_DIR=./data/samples
TEMPLATES_DIR=./data/templates
OUTPUTS_DIR=./data/outputs
SALARY_TEMPLATE_PATH=C:\path\to\salary-template.xlsx
FINAL_TOOL_TEMPLATE_PATH=C:\path\to\final-tool-template.xlsx
DEEPSEEK_API_KEY=
DEEPSEEK_API_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-reasoner
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Notes:
- If `DEEPSEEK_API_KEY` is empty, the backend will keep the rule-based chain working and skip live fallback calls.
- If either template path is missing, export will fail by design.
- If employee master data is missing, matching can become blocked by design.
- Employee master import now supports CSV/XLSX upsert by employee ID.

## 4. Local Startup

### Backend

```powershell
py -m pip install -r backend\requirements.txt
py backend\run.py
```

Expected base URL:
- `http://127.0.0.1:8000`

### Frontend

```powershell
cd frontend
cmd /c npm.cmd install
cmd /c npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

Expected URL:
- `http://127.0.0.1:5173`

## 5. End-To-End Operator Flow

1. Open the dashboard and confirm backend health is green.
2. Go to `/imports` and upload one or more regional Excel files.
3. Open the batch detail page and trigger parse if needed.
4. Review detected sheet, header mapping, filtered rows, and normalized preview.
5. Use `/mappings` if a field needs manual correction.
6. Run validation from `/results`.
7. Run matching from `/results` after employee master data is present.
8. Run export from `/exports`.
9. Check the generated dual-template artifacts in `OUTPUTS_DIR`.

## 6. Recommended Verification Commands

### Backend smoke and regression

```powershell
py -m compileall backend
.\.venv\Scripts\python.exe -m pytest backend\tests\test_region_sample_regression.py -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest backend\tests\test_template_exporter_regression.py -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest backend\tests\test_llm_mapping_service.py -p no:cacheprovider
```

### Frontend verification

```powershell
cd frontend
cmd /c npm.cmd run lint
cmd /c npm.cmd run build
```

### Wider backend confidence

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -p no:cacheprovider
```

Important note:
- In the current desktop shell session, very long pytest runs can be terminated by shell timeout even after most suites have already passed. When that happens, prefer running the heaviest suites separately rather than assuming a code failure.

## 7. Verified Test Areas

These areas now have dedicated automated coverage:
- region sample parsing regression across Guangzhou, Hangzhou, Xiamen, Shenzhen, Wuhan, and Changsha
- dual-template export regression across the same regional sample families
- DeepSeek fallback behavior, including disabled fallback, no API key, invalid payloads, invalid canonical fields, candidate sanitization, and request-shape checks
- import, preview, validation, matching, export, and dashboard API flows

## 8. Deployment Risks And Known Gaps

### Still open
- Employee master import is now available, but the `/employees` page currently focuses on import and search rather than full CRUD administration.
- Live DeepSeek connectivity has not been included in automated regression because network availability and provider response times are unstable in this environment.

### Operational implications
- Matching depends on employee master data already existing in the database or being imported through `/api/v1/employees/import`.
- Export depends on successful matching and both template files being reachable.
- Real-sample regression depends on local sample files being present under `data/samples`.

## 9. Release Readiness Guidance

Reasonably ready now for:
- parser and normalization iteration
- mapping-rule tuning
- local operator demos using seeded employee master data
- export-template verification against real sample files

Not fully ready yet for:
- teams that need a richer employee master administration console with edit, disable, audit, and delete operations

## 10. Recommended Next Work

1. Add employee master edit, disable, and audit operations on top of the new import/list foundation.
2. Add a short seeded demo dataset path for local end-to-end demos.
3. Add deployment packaging if Docker or service supervision becomes mandatory.
4. Add one optional live DeepSeek smoke check outside the default CI-style suite.
