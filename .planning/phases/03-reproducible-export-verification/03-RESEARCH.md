# Phase 3: Reproducible Export Verification - Research

**Researched:** 2026-03-26
**Domain:** Reproducible dual-template export verification for FastAPI/openpyxl/pytest
**Confidence:** MEDIUM

## User Constraints

### Locked Inputs

- No `03-CONTEXT.md` exists for this phase. Planning must use `STATE.md`, `ROADMAP.md`, `REQUIREMENTS.md`, and the current code/tests as the source of truth.
- Treat the repository as a brownfield baseline with the core import, normalize, validate, match, and export flow already implemented.
- Scope this roadmap to hardening, verification, and operational clarity rather than new feature expansion.
- Preserve the rules-first parsing and dual-template export contracts while moving export verification onto reproducible fixtures or explicit configuration.
- Phase goal: dual-template export confidence must be reproducible from repo-controlled or explicitly configured inputs instead of one developer workstation.
- Phase requirements: `VER-01`, `VER-02`.
- Success criteria:
  1. Export regression verification can locate both required templates from repository-controlled fixtures or an explicit configuration path.
  2. Verification fails loudly when required export fixtures or templates are missing.
  3. Dual-template export coverage can be rerun on another machine without editing code to point at a desktop-only template path.
- Keep `AGENTS.md` unchanged and use `.planning/` as the project memory source for subsequent GSD steps.

### Claude's Discretion

- Choose the exact balance between repo fixtures and explicit configuration, as long as the default verification path is reproducible and fail-loud.
- Choose where to centralize export-fixture lookup and how to structure shared test helpers.
- Choose whether to keep production template discovery logic unchanged or tighten only the verification callers.

### Deferred Ideas

- Phase 4 operations/deployment workflow cleanup is out of scope.
- General template-onboarding architecture (`TPL-01`) is out of scope except where this phase should not make it harder later.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| VER-01 | Dual-template export regression tests can run from repository-controlled or explicitly configured template locations without depending on a developer desktop path | Repo fixture layout, shared resolver, explicit `Settings` override contract, removal of Desktop fallback |
| VER-02 | Mandatory export verification fails loudly when required fixtures or templates are missing instead of silently weakening confidence through broad skips | Replace `pytest.skip` and implicit fallback with fail-fast setup errors and preserve explicit bad-path failures |

## Summary

The exporter already has most of the runtime capability needed for this phase. `Settings` exposes `salary_template_path`, `final_tool_template_path`, and `templates_dir`; `template_exporter._resolve_template_path()` already supports explicit paths, configured paths, and discovery under `data/templates`, then raises `ExportServiceError` if nothing can be resolved. The main gap is the verification harness, not the workbook-writing core.

Today, export verification still depends on duplicated `find_template()` helpers in multiple test modules. Those helpers search configured settings, then fall back to a Desktop directory, and finally either `pytest.skip(...)` or raise only after trying the workstation path. The repo currently ships no template fixtures under `data/templates/`; only `.gitkeep` is tracked. On top of that, `batch_export_service.export_batch()` currently passes configured template paths into `export_dual_templates()` only if those paths already exist, which weakens explicit-path fail-loud behavior by silently turning a bad configured path into discovery fallback.

**Primary recommendation:** ship sanitized repo-controlled copies of both required templates under a dedicated fixture directory, add one shared export-fixture resolver for all export-related tests, and preserve loud failures for both missing repo fixtures and invalid explicit configuration paths.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.13.7 observed locally | Runtime for export verification | Existing backend/tests already run in the project venv |
| pytest | 8.3.4 | Verification harness | Already pinned and installed; `tmp_path` and `pytest.fail` match this phase well |
| openpyxl | 3.1.5 | Workbook load/save and semantic assertions | Already the exporter's Excel engine; verification should stay on the same stack |
| pydantic-settings | 2.6.1 | Explicit template-path configuration | Existing config model already uses `BaseSettings` and `.env` support |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pathlib | stdlib | Path-safe fixture resolution | Use everywhere in shared test helpers |
| shutil | stdlib | Disposable copies of mutable fixtures | Use only when a test must mutate source files |
| fastapi TestClient | current project stack | API-level export verification | Use for `/imports/{id}/export`, `/aggregate`, and dashboard coverage |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Repo-controlled template fixtures | Explicit config only | Smaller repo, but another machine still needs out-of-band template distribution |
| Real sanitized template copies | Tiny synthetic workbooks | Faster and smaller, but weaker confidence because formulas/layout can diverge from the real templates |
| Semantic workbook assertions | Full-file binary diff of `.xlsx` | Binary diff is brittle and validates the ZIP container, not the business contract |
| Shared resolver | One `find_template()` per test module | Duplication keeps Desktop fallback and inconsistent failure behavior alive |

**Installation:**

```bash
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

**Version verification:** Verified locally on 2026-03-26 via `.\.venv\Scripts\python.exe --version`, `.\.venv\Scripts\python.exe -m pytest --version`, and importing `openpyxl`, `pydantic_settings`, and `fastapi`. The repo pins these versions in `backend/requirements.txt`.

## Architecture Patterns

### Recommended Project Structure

```text
data/
|-- templates/
|   `-- regression/
|       |-- manifest.json
|       |-- salary-template.xlsx
|       `-- final-tool-template.xlsx
backend/
`-- tests/
    |-- support/
    |   `-- export_fixtures.py
    |-- test_template_exporter.py
    |-- test_template_exporter_regression.py
    |-- test_export_api.py
    |-- test_aggregate_api.py
    `-- test_dashboard_api.py
```

### Pattern 1: Shared Required-Template Resolver

**What:** Put all required template and sample lookup behind one helper that returns exact paths and fails test setup when mandatory assets are missing.

**When to use:** Every export-related unit, regression, API, aggregate, and dashboard test.

**Example:**

```python
# Source: local config pattern + pytest.fail docs
from dataclasses import dataclass
from pathlib import Path

import pytest

from backend.app.core.config import ROOT_DIR, get_settings


@dataclass(frozen=True, slots=True)
class RequiredExportTemplates:
    salary: Path
    final_tool: Path


def resolve_required_export_templates() -> RequiredExportTemplates:
    settings = get_settings()
    repo_root = ROOT_DIR / "data" / "templates" / "regression"
    salary = settings.salary_template_file or (repo_root / "salary-template.xlsx")
    final_tool = settings.final_tool_template_file or (repo_root / "final-tool-template.xlsx")

    missing = [str(path) for path in (salary, final_tool) if not path.exists()]
    if missing:
        pytest.fail(f"Missing required export templates: {', '.join(missing)}", pytrace=False)

    return RequiredExportTemplates(salary=salary, final_tool=final_tool)
```

### Pattern 2: Repo Default, Explicit Override

**What:** Default verification should use repo fixtures. `SALARY_TEMPLATE_PATH` and `FINAL_TOOL_TEMPLATE_PATH` remain supported as explicit overrides for external or operator-managed copies.

**When to use:** When the repo can ship sanitized fixtures but maintainers still need an external override path.

**Why:** This satisfies both allowed `VER-01` modes without requiring code edits.

### Pattern 3: Preserve Explicit Bad-Path Failures

**What:** If an operator explicitly configured a template path and it is wrong, that should stay a hard failure all the way into `_resolve_template_path()`.

**When to use:** `batch_export_service.export_batch()` and any other runtime caller that forwards settings into `export_dual_templates()`.

**Why:** Current code weakens `VER-02` by dropping bad explicit paths before exporter resolution.

### Pattern 4: Isolated Per-Test Output Directories

**What:** Use `tmp_path` for generated outputs, copied templates, temporary DBs, and upload folders instead of persistent repo directories.

**When to use:** All tests that generate `.xlsx`, SQLite DBs, or upload/output artifacts.

**Example:**

```python
# Source: pytest tmp_path docs
def test_export_dual_templates_writes_both_outputs(tmp_path, export_templates):
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()

    result = export_dual_templates(
        records,
        output_dir=output_dir,
        salary_template_path=export_templates.salary,
        final_tool_template_path=export_templates.final_tool,
        export_prefix="regression_shenzhen",
    )

    assert result.status == "completed"
```

### Anti-Patterns to Avoid

- **Desktop fallback in tests:** `Path.home() / "Desktop" / ...` makes verification workstation-specific.
- **Skip-heavy required-fixture lookup:** `pytest.skip(...)` hides missing mandatory coverage.
- **Keyword-only template selection:** substring matching can silently pick the wrong workbook.
- **Shared repo artifact directories for test writes:** `.test_artifacts` and tracked folders increase flakiness and cleanup noise.
- **Byte-for-byte `.xlsx` assertions:** the OOXML ZIP layout is not the stable business contract.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Required export asset discovery | One `find_template()` per test module | One shared resolver in `backend/tests/support/export_fixtures.py` | Duplicated lookup logic is how Desktop fallback spread |
| Mandatory fixture absence handling | Silent skip branches | `pytest.fail(...)` or raised setup exceptions | Missing required assets must break verification loudly |
| Temp output cleanup | Repo-local folders plus repeated `shutil.rmtree()` | `tmp_path` and `tmp_path_factory` | pytest already provides isolated temporary paths |
| Export result verification | Whole-file binary comparison | `openpyxl.load_workbook()` plus stable cell/formula assertions | Workbook semantics matter more than ZIP bytes |
| Template identity | "Newest file wins" or keyword guessing | Manifest-backed exact paths or explicit settings | Verification should prove the correct template was used |

**Key insight:** this phase should harden the verification harness around the existing exporter, not create a second export path.

## Common Pitfalls

### Pitfall 1: Mandatory Verification Quietly Disappears

**What goes wrong:** Export tests become skipped on machines without local template files.

**Why it happens:** Current helpers in `test_template_exporter.py`, `test_template_exporter_regression.py`, `test_export_api.py`, and `test_aggregate_api.py` call `pytest.skip(...)` when no configured/Desktop template is found.

**How to avoid:** Make repo fixtures mandatory by default and fail during fixture setup if they are missing.

**Warning signs:** Export-related pytest runs report skips instead of failures on clean machines.

### Pitfall 2: Bad Explicit Config Does Not Fail Loudly

**What goes wrong:** A misconfigured `SALARY_TEMPLATE_PATH` or `FINAL_TOOL_TEMPLATE_PATH` quietly falls back to discovery instead of failing.

**Why it happens:** `batch_export_service.export_batch()` currently only forwards a configured path if the file already exists.

**How to avoid:** Pass configured values through unchanged and let `_resolve_template_path()` raise the exporter-level error.

**Warning signs:** Export still succeeds after intentionally breaking the configured template path.

### Pitfall 3: Tests Use the Wrong Template

**What goes wrong:** A test picks an unintended workbook because multiple files match a keyword or because discovery chooses the latest file.

**Why it happens:** Current test helpers select by keyword; exporter discovery sorts candidates by mtime/name.

**How to avoid:** Use exact manifest entries or explicit paths in the shared resolver.

**Warning signs:** Flaky failures after adding a new template copy under `data/templates`.

### Pitfall 4: Repo Pollution and Cleanup Flakes

**What goes wrong:** Test runs leave behind outputs/DBs and collide with each other on Windows.

**Why it happens:** Current tests rely on persistent artifact directories and manual cleanup.

**How to avoid:** Use `tmp_path` for mutable outputs and keep only intentional fixtures in the repo.

**Warning signs:** Permission-denied cleanup errors or large untracked artifact trees after pytest.

### Pitfall 5: Unsupported Workbook Features Get Lost

**What goes wrong:** A workbook saves successfully but loses shapes or unsupported elements.

**Why it happens:** openpyxl does not round-trip every Excel feature.

**How to avoid:** Keep regression fixtures representative, assert on supported workbook semantics, and call out any required manual spot-checks for unsupported features.

**Warning signs:** Exported workbooks open with missing drawings or altered non-cell elements.

## Code Examples

Verified patterns from official sources and the current repo:

### Per-Test Temporary Directory

```python
# Source: https://docs.pytest.org/en/stable/how-to/tmp_path.html
def test_create_file(tmp_path):
    output = tmp_path / "sub"
    output.mkdir()
    file_path = output / "hello.txt"
    file_path.write_text("content", encoding="utf-8")
    assert file_path.read_text(encoding="utf-8") == "content"
```

### Explicit Failure for Missing Mandatory Assets

```python
# Source: https://docs.pytest.org/en/stable/reference/reference.html
import pytest


def require_path(path):
    if not path.exists():
        pytest.fail(f"Missing required fixture: {path}", pytrace=False)
```

### Settings-Based Override Without Code Edits

```python
# Source: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    salary_template_path: str | None = None
    final_tool_template_path: str | None = None


settings = Settings(_env_file=None)
```

### Workbook-Semantic Assertions

```python
# Source: local exporter tests + https://openpyxl.readthedocs.io/en/stable/tutorial.html
from openpyxl import load_workbook


workbook = load_workbook(result_path, data_only=False)
sheet = workbook[workbook.sheetnames[0]]
assert sheet["A2"].value == expected_name
assert str(sheet["AA7"].value).startswith("=")
workbook.close()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Desktop path fallback in tests | Repo fixtures with explicit override support | Phase 3 target | Another machine can rerun verification without source edits |
| Missing required assets become skips | Missing required assets fail setup | Phase 3 target | Coverage loss becomes visible immediately |
| Bad explicit template paths are silently softened | Bad explicit paths stay hard failures | Phase 3 target | Operators get deterministic configuration errors |
| Shared persistent test artifact folders | `tmp_path`-based test isolation | Current pytest standard | Cleaner reruns and fewer Windows cleanup issues |

**Deprecated/outdated:**

- Desktop-only export-test assumptions: conflicts directly with `VER-01`.
- Skip-heavy required export-fixture lookup: conflicts directly with `VER-02`.

## Open Questions

1. **Can sanitized copies of both required templates be committed to the repo?**
   - What we know: `data/templates/` currently contains only `.gitkeep`; `.env.example` exposes both template-path overrides; the local environment uses workstation-specific absolute template paths.
   - What's unclear: whether licensing, privacy, or size constraints block committing sanitized copies.
   - Recommendation: decide this first. If allowed, make repo fixtures the default verification path. If not, deliver an explicit-config-only mode and fail immediately when the required paths are not set.

2. **Which workbook invariants define "export confidence"?**
   - What we know: current tests already assert key cells, formulas, filenames, and artifact existence.
   - What's unclear: whether merged ranges, sheet protection, print areas, or hidden metadata also need coverage.
   - Recommendation: keep Phase 3 focused on stable workbook semantics first; add more only if tied to a real regression risk.

3. **Should mandatory export verification be one command or split into fast/full layers?**
   - What we know: `STATE.md` warns that regression pytest runs are slow on Windows, and one broad regression probe timed out during research.
   - What's unclear: whether planners want one long mandatory suite or a fast gate plus a full rerun command.
   - Recommendation: prefer a fast mandatory command plus a second documented full cross-region rerun if runtime remains high.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `.\.venv\Scripts\python.exe` | Backend export verification | yes | 3.13.7 | -- |
| `pytest` | Export regression execution | yes | 8.3.4 | Install from `backend/requirements.txt` |
| `openpyxl` | Workbook load/save assertions | yes | 3.1.5 | -- |
| Repo sample workbooks under `data/samples` | Cross-region regression inputs | yes | tracked fixtures | -- |
| Repo template workbooks under `data/templates` | Repo-controlled verification | no | -- | Explicit `SALARY_TEMPLATE_PATH` and `FINAL_TOOL_TEMPLATE_PATH` |

**Missing dependencies with no fallback:**

- None for basic implementation. The phase is not blocked because explicit template-path configuration already exists.

**Missing dependencies with fallback:**

- Repo-controlled template fixtures are missing today. Until they are added, only the explicit configured-path mode is available.

## Sources

### Primary (HIGH confidence)

- Local repo: `backend/app/core/config.py` - current `BaseSettings` fields and computed template paths
- Local repo: `backend/app/exporters/template_exporter.py` - `_resolve_template_path()` and repo discovery behavior
- Local repo: `backend/app/services/batch_export_service.py` - current weakening of explicit bad-path failures
- Local repo: `backend/tests/test_template_exporter.py` - Desktop fallback and `pytest.skip(...)` behavior
- Local repo: `backend/tests/test_template_exporter_regression.py` - cross-region export regression entry point
- Local repo: `backend/tests/test_export_api.py` - API export verification with duplicated template lookup
- Local repo: `backend/tests/test_aggregate_api.py` - aggregate-path export verification with duplicated template lookup
- Local repo: `backend/tests/test_dashboard_api.py` - dashboard coverage still using Desktop fallback logic
- https://docs.pytest.org/en/stable/how-to/tmp_path.html - `tmp_path` and `tmp_path_factory`
- https://docs.pytest.org/en/stable/reference/reference.html - `pytest.fail()` and `pytest.skip()`
- https://docs.pydantic.dev/latest/concepts/pydantic_settings/ - `BaseSettings`, `.env`, and runtime override behavior
- https://openpyxl.readthedocs.io/en/stable/tutorial.html - `load_workbook()`, `Workbook.save()`, and workbook feature caveats

### Secondary (MEDIUM confidence)

- https://openpyxl.readthedocs.io/en/stable/changes.html - stable release notes published in current docs

### Tertiary (LOW confidence)

- None

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - versions are pinned locally and already used by the repo
- Architecture: HIGH - recommendations directly target the observed verification gaps
- Pitfalls: MEDIUM - the major risks are verified, but template commitability and runtime budget still need decisions

**Research date:** 2026-03-26
**Valid until:** 2026-04-25
