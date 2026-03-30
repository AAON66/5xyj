# Phase 6: Data Management - Research

**Researched:** 2026-03-30
**Domain:** Full-stack data browsing, filtering, quality metrics, import history (React + FastAPI + SQLAlchemy)
**Confidence:** HIGH

## Summary

Phase 6 adds data management capabilities to the existing social insurance system. The work divides into four distinct streams: (1) a new DataManagement page with cascading region/company/period filters and a detail/summary tab pair, (2) full-employee summary views with dual-dimension toggling, (3) data quality metrics enhancement on the existing Dashboard, and (4) import history enhancement on the existing Imports page. All backend models, auth patterns, API conventions, and frontend component patterns are already established -- this phase extends them without introducing new libraries.

The codebase already has NormalizedRecord with indexed region, company_name, and billing_period columns, making server-side filtering efficient. The Employees page provides a proven pattern for cascading filter dropdowns + server-side pagination. The ValidationIssue model already stores per-record quality issues, and the dashboard_service.py already aggregates batch-level stats.

**Primary recommendation:** Follow the established patterns from Phase 4 (Employees) for filtering and pagination, extend existing services for quality metrics, and add a single new `created_by` column to ImportBatch with an Alembic migration.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01: New standalone "Data Management" page, separate from existing Results/Imports pages
- D-02: Three-condition cascading filter: region -> company -> period, selecting region filters company dropdown
- D-03: Table defaults to summary columns (name, employee_id, region, company, period, company_total, personal_total, total), click row to expand insurance type details
- D-04: Filter state persisted via URL query params (?region=shenzhen&company=xxx&period=202602), refresh-safe, shareable
- D-05: Data Management as sidebar first-level nav item, alongside Dashboard, Imports, Exports
- D-06: Data Management page does NOT include export functionality
- D-07: Two tabs within Data Management: "Detail Data" and "Full Employee Summary"
- D-08: Full-employee summary supports dual-dimension toggle: by-employee (one row per person, latest month) and by-period (one row per month, totals/averages)
- D-09: Summary view reuses the same three-condition cascading filter
- D-10: Enhance existing Dashboard.tsx, add data quality section
- D-11: Monitor three quality indicators: missing fields (name/ID/employee_id), anomalous amounts (base outside range), duplicate records (same person+period)
- D-12: Quality metrics shown per-import-batch, each batch shows issue counts
- D-13: Enhance existing Imports.tsx, add operator, record count, timestamp columns
- D-14: ImportBatch model gets new created_by field (ForeignKey to User table), extracted from current user token at import time
- D-15: Legacy ImportBatch records have null created_by (backward compatible)

### Claude's Discretion
- Tab component implementation approach
- Loading and empty state display for cascading filters
- Summary view sorting order
- Specific threshold values for anomalous amount detection
- Import history pagination parameters

### Deferred Ideas (OUT OF SCOPE)
- Filtered result export to Excel -- future phase
- Custom table column configuration -- Phase 8 UI rebuild
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-01 | HR can filter social insurance records by region, company, and billing period | NormalizedRecord already indexed on region/company_name/billing_period; Employees.tsx cascading filter pattern is reusable; new API endpoints for filter options and paginated records |
| DATA-02 | HR can view full-employee summary with totals across insurance types | SQLAlchemy GROUP BY on employee_id or billing_period with SUM aggregation; two sub-views toggled via secondary tab bar |
| DATA-03 | Data quality dashboard shows import health metrics per batch | ValidationIssue model already captures missing/anomalous/duplicate issues; extend dashboard_service.py with quality aggregation queries |
| DATA-04 | Import history shows filename, timestamp, operator, record count | ImportBatch needs created_by FK to User; Alembic migration; import API reads user from auth token |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- React frontend, FastAPI backend, SQLAlchemy ORM
- No new component libraries in Phase 6 (Phase 7 introduces Ant Design)
- Hand-rolled CSS using existing styles.css design tokens
- API responses wrapped in `success_response()`
- Route protection via `require_role("admin", "hr")`
- Auth token provides username; `require_authenticated_user` returns `AuthUser(username, role)`
- Rules-first, LLM-fallback principle (not directly relevant to this phase)
- All data provenance must be traceable
- Must use Chinese for user-facing text

## Standard Stack

### Core (already installed -- no new packages)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | existing | Frontend framework | Already in use |
| react-router-dom | existing | Routing + URL query params | Already in use for all pages |
| axios | existing | HTTP client | Already in use via apiClient |
| FastAPI | existing | Backend API framework | Already in use |
| SQLAlchemy | existing | ORM + query building | Already in use for all models |
| Alembic | existing | DB migrations | Already used (6 migrations exist) |
| Pydantic | existing | API schemas | Already in use for all responses |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| URLSearchParams | built-in | Parse/build URL query strings | Filter state persistence (D-04) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Manual URL sync | react-router useSearchParams | Adds coupling; manual URLSearchParams is simpler and matches existing pattern |
| New UI component lib | Existing hand-rolled CSS | Phase 7 introduces Ant Design; Phase 6 must stay consistent |

**Installation:**
```bash
# No new packages needed -- everything is already installed
```

## Architecture Patterns

### Recommended Project Structure (new files only)
```
backend/app/
  api/v1/
    data_management.py          # New API router for data browsing/filtering/summary
  schemas/
    data_management.py          # New Pydantic schemas for records, summaries, quality
  services/
    data_management_service.py  # New service: filtering, pagination, summaries
    dashboard_service.py        # EXTEND: add quality metrics methods

frontend/src/
  pages/
    DataManagement.tsx           # New page with tabs, filters, tables
  services/
    dataManagement.ts            # New API client functions
```

### Pattern 1: Cascading Filter with Server-Side Pagination
**What:** Three-select filter bar where each dropdown constrains the next, with URL query param sync
**When to use:** DATA-01, DATA-02
**Example (based on existing Employees.tsx pattern):**
```typescript
// Frontend: Read filter from URL on mount
const [searchParams, setSearchParams] = useSearchParams();
const [region, setRegion] = useState(searchParams.get('region') || '');
const [company, setCompany] = useState(searchParams.get('company') || '');
const [period, setPeriod] = useState(searchParams.get('period') || '');

// When region changes: reset company & period, fetch filtered companies
useEffect(() => {
  setCompany('');
  setPeriod('');
  if (region) fetchCompaniesByRegion(region).then(setCompanies);
}, [region]);

// Sync to URL
useEffect(() => {
  const params = new URLSearchParams();
  if (region) params.set('region', region);
  if (company) params.set('company', company);
  if (period) params.set('period', period);
  params.set('tab', activeTab);
  setSearchParams(params, { replace: true });
}, [region, company, period, activeTab]);
```

```python
# Backend: data_management.py router
@router.get('/records')
def list_normalized_records(
    region: Optional[str] = Query(default=None),
    company_name: Optional[str] = Query(default=None),
    billing_period: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    # Service builds query with optional filters, returns paginated result
    ...
```

### Pattern 2: Tab-Based Views Sharing Filter State
**What:** Two tabs (detail + summary) that share the same filter bar state
**When to use:** D-07, D-08, D-09
**Key:** Tab switching does NOT reset filters. Both tabs fetch from different API endpoints but pass the same filter params. Active tab stored in URL as `tab=detail|summary`.

### Pattern 3: Inline Row Expansion (Detail View)
**What:** Click a row to expand an inline sub-row showing insurance type breakdown
**When to use:** D-03
**Key:** Only one row expanded at a time. Data is already in the paginated response (no additional API call). Use a `colspan` TR below the data row with conditional rendering.

### Pattern 4: Aggregation Endpoints for Summary Views
**What:** Backend GROUP BY queries for employee-level and period-level summaries
**When to use:** DATA-02
```python
# By employee: GROUP BY person_name, id_number, employee_id
def get_employee_summary(db, region=None, company_name=None, billing_period=None, limit=20, offset=0):
    query = db.query(
        NormalizedRecord.employee_id,
        NormalizedRecord.person_name,
        NormalizedRecord.company_name,
        NormalizedRecord.region,
        func.max(NormalizedRecord.billing_period).label('latest_period'),
        func.sum(NormalizedRecord.company_total_amount).label('company_total'),
        func.sum(NormalizedRecord.personal_total_amount).label('personal_total'),
        func.sum(NormalizedRecord.total_amount).label('total'),
    ).group_by(
        NormalizedRecord.employee_id,
        NormalizedRecord.person_name,
        NormalizedRecord.company_name,
        NormalizedRecord.region,
    )
    # Apply filters, pagination...

# By period: GROUP BY billing_period
def get_period_summary(db, region=None, company_name=None, limit=20, offset=0):
    query = db.query(
        NormalizedRecord.billing_period,
        func.count(NormalizedRecord.id).label('total_count'),
        func.sum(NormalizedRecord.company_total_amount).label('company_total'),
        func.sum(NormalizedRecord.personal_total_amount).label('personal_total'),
        func.sum(NormalizedRecord.total_amount).label('total'),
        func.avg(NormalizedRecord.personal_total_amount).label('avg_personal'),
        func.avg(NormalizedRecord.company_total_amount).label('avg_company'),
    ).group_by(NormalizedRecord.billing_period)
```

### Pattern 5: Extending Existing Services
**What:** Add methods to dashboard_service.py for quality metrics rather than creating a separate service
**When to use:** DATA-03
```python
# In dashboard_service.py or a new quality section
def get_data_quality_metrics(db: Session) -> DataQualityRead:
    # Missing fields: count records where person_name, id_number, or employee_id is null
    missing_count = db.query(func.count(NormalizedRecord.id)).filter(
        or_(
            NormalizedRecord.person_name.is_(None),
            NormalizedRecord.id_number.is_(None),
            NormalizedRecord.employee_id.is_(None),
        )
    ).scalar() or 0

    # Anomalous amounts: payment_base outside reasonable range
    # Duplicate records: same person_name + billing_period appearing more than once
    ...
```

### Anti-Patterns to Avoid
- **Loading all records client-side:** Always use server-side pagination with limit/offset
- **Separate API call per filter dropdown:** Use a single endpoint that returns all filter options for the cascade (or two at most: regions static, companies+periods filtered)
- **Duplicating filter logic:** Both detail and summary tabs MUST share the same FilterBar component
- **Modifying Salary template export logic:** Explicitly forbidden by CLAUDE.md

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| URL query param sync | Custom URL parser | URLSearchParams API | Built into browser, handles encoding |
| Pagination | Custom pagination math | Same pattern from Employees.tsx | Already battle-tested in Phase 4 |
| Date formatting | Custom date formatter | `Intl.DateTimeFormat('zh-CN')` | Already used in Dashboard/Employees/Imports |
| DB migrations | Manual ALTER TABLE | Alembic `alembic revision --autogenerate` | Standard migration pipeline, 6 migrations already exist |
| Auth user extraction | Custom token parsing | `Depends(require_authenticated_user)` | Already established dependency |

## Common Pitfalls

### Pitfall 1: Cascading Filter Race Conditions
**What goes wrong:** User rapidly changes region, multiple API calls fire, stale company/period lists overwrite fresh ones
**Why it happens:** useEffect cleanup not implemented; no request cancellation
**How to avoid:** Use the same `let active = true` / cleanup pattern from Employees.tsx. When region changes, immediately clear company/period state before fetching.
**Warning signs:** Dropdown shows companies from wrong region after fast switching

### Pitfall 2: ImportBatch created_by Migration on Existing Data
**What goes wrong:** Alembic migration fails because existing rows have no created_by value
**Why it happens:** Foreign key constraint with NOT NULL on a populated table
**How to avoid:** Make created_by NULLABLE (D-15 explicitly requires this). Migration adds column with `nullable=True, default=None`.
**Warning signs:** Migration error on `ALTER TABLE`

### Pitfall 3: Summary Aggregation Performance
**What goes wrong:** GROUP BY queries on large NormalizedRecord table are slow
**Why it happens:** No composite index for the aggregation pattern
**How to avoid:** Existing indexes on region, company_name, billing_period individually should be sufficient for v1 data volumes. If needed later, add composite index. Use `.count()` subquery for total count rather than loading all rows.
**Warning signs:** API response time > 2 seconds

### Pitfall 4: Decimal Serialization in Aggregations
**What goes wrong:** SQLAlchemy func.sum() returns Decimal but JSON serialization fails
**Why it happens:** Pydantic/JSON does not natively serialize Decimal
**How to avoid:** Use `float()` conversion in Pydantic schema or configure `model_dump(mode='json')` which the project already uses consistently.
**Warning signs:** 500 error on summary endpoints

### Pitfall 5: AppShell Navigation Visibility
**What goes wrong:** Employee role sees the Data Management nav item
**Why it happens:** Current AppShell only filters by `adminOnly` boolean, no general role filter
**How to avoid:** The nav item needs the same filtering logic. Either add a `roles` property to nav items (preferred) or add a separate flag. Route-level protection via `RoleRoute(['admin', 'hr'])` in App.tsx is the safety net regardless.
**Warning signs:** Employee user sees nav link but gets redirected when clicking

### Pitfall 6: Tab State Loss on Navigation
**What goes wrong:** User selects Summary tab, navigates away, comes back, tab resets to Detail
**Why it happens:** Tab state not in URL
**How to avoid:** D-04 specifies URL persistence. Tab state (`tab=detail|summary`) must be in URL query params and read on mount.
**Warning signs:** Tab always defaults to "detail" regardless of URL

## Code Examples

### Backend: New Alembic Migration for created_by
```python
# alembic/versions/YYYYMMDD_0007_add_import_batch_created_by.py
def upgrade():
    op.add_column('import_batches', sa.Column(
        'created_by',
        sa.Uuid(as_uuid=False),
        sa.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
    ))
    op.create_index('ix_import_batches_created_by', 'import_batches', ['created_by'])

def downgrade():
    op.drop_index('ix_import_batches_created_by', 'import_batches')
    op.drop_column('import_batches', 'created_by')
```

### Backend: ImportBatch Model Update
```python
# Add to ImportBatch model
created_by: Mapped[Optional[str]] = mapped_column(
    ForeignKey("users.id", ondelete="SET NULL"),
    nullable=True,
    index=True,
)
creator: Mapped["User | None"] = relationship()
```

### Backend: Quality Metrics Query
```python
# Per-batch quality metrics
def get_quality_by_batch(db: Session, limit: int = 10):
    batches = db.query(ImportBatch).order_by(ImportBatch.created_at.desc()).limit(limit).all()
    results = []
    for batch in batches:
        missing = db.query(func.count(NormalizedRecord.id)).filter(
            NormalizedRecord.batch_id == batch.id,
            or_(
                NormalizedRecord.person_name.is_(None),
                NormalizedRecord.id_number.is_(None),
                NormalizedRecord.employee_id.is_(None),
            )
        ).scalar() or 0
        # ... anomaly and duplicate counts
        results.append(BatchQualityRead(batch_id=batch.id, batch_name=batch.batch_name, missing=missing, ...))
    return results
```

### Frontend: FilterBar Component Pattern
```typescript
// Reusable filter bar matching Employees.tsx .employee-toolbar pattern
function FilterBar({ region, company, period, onRegionChange, onCompanyChange, onPeriodChange, onReset }) {
  const [regions, setRegions] = useState<string[]>([]);
  const [companies, setCompanies] = useState<string[]>([]);
  const [periods, setPeriods] = useState<string[]>([]);

  useEffect(() => { fetchFilterOptions().then(setRegions); }, []);
  useEffect(() => {
    if (region) fetchCompaniesByRegion(region).then(setCompanies);
    else setCompanies([]);
  }, [region]);
  // ... similar for periods

  return (
    <div className="employee-toolbar">
      <label className="form-field employee-toolbar__toggle">
        <span>地区</span>
        <select value={region} onChange={e => onRegionChange(e.target.value)}>
          <option value="">全部地区</option>
          {regions.map(r => <option key={r} value={r}>{r}</option>)}
        </select>
      </label>
      {/* ... company, period selects */}
      <button type="button" className="button button--ghost" onClick={onReset}>重置筛选</button>
    </div>
  );
}
```

### Frontend: Row Expansion Pattern
```typescript
const [expandedRowId, setExpandedRowId] = useState<string | null>(null);

{records.map(record => (
  <>
    <tr key={record.id}>
      {/* ... columns ... */}
      <td>
        <button className="button button--ghost"
          onClick={() => setExpandedRowId(expandedRowId === record.id ? null : record.id)}>
          {expandedRowId === record.id ? '收起详情' : '展开详情'}
        </button>
      </td>
    </tr>
    {expandedRowId === record.id && (
      <tr className="detail-expand-row">
        <td colSpan={9} style={{ background: 'rgba(243, 246, 251, 0.96)' }}>
          {/* Insurance type breakdown grid */}
        </td>
      </tr>
    )}
  </>
))}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Client-side filtering | Server-side filter + pagination | Phase 4 | All new data views must use server-side filtering |
| No auth on imports | Token-based auth on all endpoints | Phase 2-3 | Import API must extract user from token for created_by |
| Single dashboard | Dashboard + specialized pages | Phase 6 | Quality metrics go on Dashboard, browsing goes to new page |

## Open Questions

1. **Anomalous amount threshold values**
   - What we know: D-11 says "payment_base outside reasonable range"
   - What's unclear: Exact min/max values for "reasonable"
   - Recommendation: Claude's discretion area. Use a configurable range, e.g., payment_base < 1000 or > 50000 as initial defaults. Can be adjusted without code changes if stored as constants.

2. **Filter options source: NormalizedRecord vs EmployeeMaster**
   - What we know: Regions are currently from a static SUPPORTED_REGIONS list in employees.py; companies from EmployeeMaster
   - What's unclear: Should data management filter options come from NormalizedRecord (actual imported data) or EmployeeMaster?
   - Recommendation: Use NormalizedRecord for filter options since data management browses imported records, not master data. Query DISTINCT region/company_name/billing_period from normalized_records.

3. **User lookup for created_by**
   - What we know: `AuthUser` has `username` but ImportBatch.created_by needs User.id (UUID)
   - What's unclear: Need to look up User.id from username at import time
   - Recommendation: Add a quick query `db.query(User.id).filter(User.username == auth_user.username).scalar()` in the import service. This is a single indexed lookup.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already configured) |
| Config file | backend/pyproject.toml or pytest section |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | Filter records by region/company/period | integration | `pytest tests/test_data_management.py::test_filter_records -x` | Wave 0 |
| DATA-01 | Cascading filter options endpoint | integration | `pytest tests/test_data_management.py::test_filter_options -x` | Wave 0 |
| DATA-01 | URL query param persistence | manual-only | Manual browser test | N/A |
| DATA-02 | Employee summary aggregation | unit | `pytest tests/test_data_management.py::test_employee_summary -x` | Wave 0 |
| DATA-02 | Period summary aggregation | unit | `pytest tests/test_data_management.py::test_period_summary -x` | Wave 0 |
| DATA-03 | Quality metrics: missing fields count | unit | `pytest tests/test_data_quality.py::test_missing_fields -x` | Wave 0 |
| DATA-03 | Quality metrics: anomalous amounts | unit | `pytest tests/test_data_quality.py::test_anomalous_amounts -x` | Wave 0 |
| DATA-03 | Quality metrics: duplicate records | unit | `pytest tests/test_data_quality.py::test_duplicate_records -x` | Wave 0 |
| DATA-04 | ImportBatch created_by populated from token | integration | `pytest tests/test_import_created_by.py -x` | Wave 0 |
| DATA-04 | Legacy batches have null created_by | unit | `pytest tests/test_import_created_by.py::test_legacy_null -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_data_management.py tests/test_data_quality.py tests/test_import_created_by.py -x -q`
- **Per wave merge:** `pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_data_management.py` -- covers DATA-01, DATA-02
- [ ] `tests/test_data_quality.py` -- covers DATA-03
- [ ] `tests/test_import_created_by.py` -- covers DATA-04
- [ ] Test fixtures: NormalizedRecord factory with varied region/company/period data

## Sources

### Primary (HIGH confidence)
- Direct code reading: `backend/app/models/normalized_record.py` -- confirmed all indexed columns and field types
- Direct code reading: `backend/app/models/import_batch.py` -- confirmed current schema lacks created_by
- Direct code reading: `backend/app/models/user.py` -- confirmed User.id is UUID, has username/display_name
- Direct code reading: `backend/app/api/v1/employees.py` -- confirmed cascading filter pattern with region/company query params
- Direct code reading: `frontend/src/pages/Employees.tsx` -- confirmed frontend filter + pagination pattern
- Direct code reading: `backend/app/services/dashboard_service.py` -- confirmed service extension point
- Direct code reading: `backend/app/dependencies.py` -- confirmed `require_authenticated_user` returns `AuthUser(username, role)`
- Direct code reading: `frontend/src/components/AppShell.tsx` -- confirmed nav item structure and `adminOnly` filter pattern
- Direct code reading: `frontend/src/App.tsx` -- confirmed `RoleRoute` pattern for route protection
- Phase 6 UI-SPEC: `.planning/phases/06-data-management/06-UI-SPEC.md` -- CSS classes, layout, copywriting contract

### Secondary (MEDIUM confidence)
- Alembic migration history (6 existing migrations) -- confirmed migration workflow is established

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new libraries, everything already installed and used
- Architecture: HIGH - all patterns directly observed in existing codebase (Employees, Dashboard, Imports)
- Pitfalls: HIGH - derived from actual code patterns and model constraints observed in the codebase

**Research date:** 2026-03-30
**Valid until:** 2026-04-30 (stable -- no external dependency changes)
