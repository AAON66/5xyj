# Phase 11: Intelligence & Polish - Research

**Researched:** 2026-04-02
**Domain:** Cross-period comparison, anomaly detection, housing fund standardization, field mapping UI
**Confidence:** HIGH

## Summary

Phase 11 builds four features on top of well-established existing infrastructure. The codebase already contains: (1) a complete batch comparison service (`compare_service.py`) with identity matching, field diffing, and Excel export; (2) a housing fund parser (`housing_fund_service.py`) with header detection, amount inference, and non-detail row filtering; (3) a mapping CRUD service (`mapping_service.py`) with backend API and basic frontend page; and (4) a data management service with period-level summaries.

The primary work is extending existing services rather than building from scratch. Cross-period comparison requires adapting `compare_batches()` to query by `billing_period` instead of `batch_id`. Anomaly detection is a new service that compares adjacent-period records for the same employee and flags threshold-exceeding changes. Housing fund needs testing and fixing parsers for all 6 regions (samples exist for Guangzhou, Hangzhou, Xiamen, Shenzhen, Changsha -- Wuhan sample is missing from `data/samples/`). Field mapping UI extends the existing `MappingsPage` with inline editing on the import detail page and a standalone management page.

**Primary recommendation:** Build each feature as an incremental extension of existing services, reusing the identity matching and field comparison patterns from `compare_service.py`, the parser framework from `housing_fund_service.py`, and the Ant Design Table patterns from existing pages.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Support two-period comparison (select two months/batches), side-by-side display
- **D-02:** Two granularity levels: default summary (by company/region) + expandable individual detail
- **D-03:** Diff display uses table + color highlighting: green for increase, red for decrease, change field background highlight
- **D-04:** Extend existing `compare_service.py`, add billing_period comparison (not limited to batch comparison)
- **D-05:** Anomaly: same employee adjacent periods, payment base or insurance amount change exceeds configured percentage threshold
- **D-06:** Thresholds configured per insurance type (pension, medical, unemployment, injury, maternity, supplementary medical, supplementary pension each independent)
- **D-07:** Detection results support HR marking: confirm (truly anomalous) / exclude (normal change)
- **D-08:** Anomaly records persisted to database, HR processing status is traceable
- **D-09:** 6 regions (Guangzhou, Hangzhou, Xiamen, Shenzhen, Wuhan, Changsha) housing fund samples all available
- **D-10:** Extend existing `housing_fund_service.py` for all 6 regions
- **D-11:** Housing fund standard fields unified into NormalizedRecord system
- **D-12:** Two entry points: inline mapping table on import result page (quick fix) + standalone field mapping management page (bulk management)
- **D-13:** HR mapping correction only affects currently imported file, future imports still use auto mapping
- **D-14:** Build frontend UI on existing `mapping_service.py` and `/api/v1/mappings` API
- **D-15:** Mapping correction operations recorded in audit log

### Claude's Discretion
- Cross-period comparison SQL query optimization approach
- Anomaly detection threshold default values
- Housing fund per-region parser implementation details
- Field mapping management page filter design
- Anomaly detection: batch run vs real-time detection

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INTEL-01 | Cross-period comparison view (multi-month data comparison) | Existing `compare_service.py` provides batch comparison logic; extend with `billing_period` query dimension. Existing Compare page and frontend service provide UI foundation. |
| INTEL-02 | Anomaly detection (payment base sudden change, amount abnormally high/low) | New `anomaly_detection_service.py` comparing adjacent periods per employee. AuditLog model provides persistence pattern. NormalizedRecord has all required fields indexed. |
| INTEL-03 | Housing fund data standardization for all regions | `housing_fund_service.py` already handles header detection and amount inference. 5 of 6 region samples exist in `data/samples/`. Parser framework is extensible. |
| INTEL-04 | Field mapping override UI (HR can manually correct mappings) | `mapping_service.py` + `/api/v1/mappings` API already support list/update. Frontend `MappingsPage` exists with basic table. Need inline editing on ImportBatchDetail page. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | existing | API endpoints for anomaly detection, period comparison | Already in project |
| SQLAlchemy | existing | ORM for anomaly records, period queries | Already in project |
| Pydantic | existing | Request/response schemas | Already in project |
| React | existing | Frontend UI | Already in project |
| Ant Design | 5.x | Table, Select, Tag, Modal, Form, ColorPicker components | Already in project, established pattern |
| openpyxl | existing | Housing fund Excel parsing | Already used by housing_fund_service |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pandas | existing | Potential optimization for large cross-period queries | Only if SQLAlchemy queries become too complex |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom anomaly model | ValidationIssue extension | ValidationIssue is for import-time issues; anomaly detection is a separate cross-period concern, deserves own model |
| New comparison endpoint | Extend existing `/compare` | Existing endpoint takes batch_id; adding period-based params is cleaner as separate endpoint or mode |

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
  services/
    compare_service.py          # EXTEND: add compare_periods() alongside compare_batches()
    anomaly_detection_service.py # NEW: cross-period anomaly detection
    housing_fund_service.py      # EXTEND: fix/verify all 6 regions
    mapping_service.py           # EXTEND: add audit logging to update
  api/v1/
    compare.py                   # EXTEND: add period comparison endpoint
    anomaly.py                   # NEW: anomaly CRUD endpoints
  models/
    anomaly_record.py            # NEW: AnomalyRecord model
  schemas/
    anomaly.py                   # NEW: anomaly request/response schemas
    compare.py                   # EXTEND: add period comparison schemas

frontend/src/
  pages/
    PeriodCompare.tsx            # NEW: or extend Compare.tsx with tab/mode
    AnomalyDetection.tsx         # NEW: anomaly list + management
    MappingManagement.tsx        # NEW: standalone mapping management page
    ImportBatchDetail.tsx        # EXTEND: inline mapping editor
  services/
    compare.ts                   # EXTEND: add period comparison API calls
    anomaly.ts                   # NEW: anomaly API service
```

### Pattern 1: Cross-Period Comparison via billing_period
**What:** Query NormalizedRecords grouped by billing_period instead of batch_id, then reuse the existing identity matching and field diffing logic from `compare_service.py`.
**When to use:** When user selects two billing periods to compare.
**Example:**
```python
# Extend compare_service.py
def compare_periods(
    db: Session,
    left_period: str,
    right_period: str,
    *,
    region: str | None = None,
    company_name: str | None = None,
) -> PeriodCompareRead:
    left_records = (
        db.query(NormalizedRecord)
        .filter(NormalizedRecord.billing_period == left_period)
    )
    if region:
        left_records = left_records.filter(NormalizedRecord.region == region)
    # ... same pattern as compare_batches but with period-based grouping
```

### Pattern 2: Anomaly Detection Model
**What:** New SQLAlchemy model for persisting anomaly detection results with HR confirmation status.
**When to use:** Storing detected anomalies and HR review state.
**Example:**
```python
class AnomalyRecord(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "anomaly_records"
    
    employee_identifier: Mapped[str]  # id_number or employee_id
    person_name: Mapped[Optional[str]]
    company_name: Mapped[Optional[str]]
    region: Mapped[Optional[str]]
    left_period: Mapped[str]
    right_period: Mapped[str]
    field_name: Mapped[str]  # e.g. "pension_company", "payment_base"
    left_value: Mapped[Optional[Decimal]]
    right_value: Mapped[Optional[Decimal]]
    change_percent: Mapped[float]
    threshold_percent: Mapped[float]
    status: Mapped[str]  # "pending" | "confirmed" | "excluded"
    reviewed_by: Mapped[Optional[str]]
    reviewed_at: Mapped[Optional[datetime]]
```

### Pattern 3: Summary + Detail Two-Level Comparison
**What:** Default view shows aggregated comparison by company/region, with expandable rows showing individual employee details.
**When to use:** Cross-period comparison UI (D-02).
**Example:**
```typescript
// Summary level: group by company_name + region
// Detail level: expand to show individual CompareRow items
// Use Ant Design Table expandedRowRender for drill-down
<Table
  expandable={{
    expandedRowRender: (record) => <DetailTable rows={record.detailRows} />,
  }}
  columns={summaryColumns}
  dataSource={summaryData}
/>
```

### Anti-Patterns to Avoid
- **Loading all records for comparison in one query:** Use pagination and server-side grouping for large datasets.
- **Hardcoding anomaly thresholds:** Must be configurable per insurance type per D-06.
- **Modifying global mapping rules from UI:** D-13 explicitly says corrections only affect current file.
- **Building anomaly detection as a synchronous API call:** For large datasets with many employees, this could timeout. Use batch processing.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Identity matching for comparison | Custom employee matching | Reuse `_build_compare_identity()` from compare_service.py | Already handles employee_id, id_number, social_security_number, housing_fund_account fallback chain |
| Period selection UI | Custom date picker | Ant Design Select populated from existing `get_filter_options()` API | Already returns distinct billing_periods |
| Inline edit for mapping table | Custom form widgets | Ant Design Table with `editable: true` cells or Select dropdowns in columns | Standard Ant Design pattern |
| Color-coded diff display | CSS color system | Reuse existing DIFF_ROW_FILL pattern concept + Ant Design Tag colors | D-03 specifies green/red/highlight |

## Common Pitfalls

### Pitfall 1: Missing Wuhan Housing Fund Sample
**What goes wrong:** Wuhan housing fund sample not found in `data/samples/` directory (only social security sample exists for Wuhan).
**Why it happens:** D-09 states all 6 regions are available but the `ls` of the directory shows no Wuhan file.
**How to avoid:** Verify availability before implementing. If truly missing, document as blocked for Wuhan housing fund specifically. The Wuhan social security sample (`data/samples/`) may contain housing fund data embedded or the sample may need to be procured.
**Warning signs:** Test for Wuhan housing fund parse fails with FileNotFoundError.

### Pitfall 2: Large Dataset Performance in Cross-Period Comparison
**What goes wrong:** Loading all NormalizedRecords for two periods into memory causes slow response or OOM.
**Why it happens:** Existing `compare_batches()` loads all records eagerly via `selectinload`. Period comparison may involve thousands of records.
**How to avoid:** Add server-side pagination to the comparison. Return summary first, detail on expand. Add indexes on `billing_period` + `region` + `company_name`.
**Warning signs:** Response time > 3s for period comparison API call.

### Pitfall 3: Anomaly Detection Adjacent Period Logic
**What goes wrong:** "Adjacent periods" assumption breaks when months are skipped or employee changes company.
**Why it happens:** billing_period format is "YYYY-MM" but not all months have data for all employees.
**How to avoid:** Define "adjacent" as "the two selected periods" per D-05, not automatically computed previous month. Let HR select which two periods to compare.
**Warning signs:** Anomalies flagged for employees who legitimately joined/left between periods.

### Pitfall 4: Mapping Override Scope Confusion
**What goes wrong:** HR changes a mapping and expects it to apply to future imports.
**Why it happens:** D-13 says corrections only affect current file, but UI doesn't make this clear.
**How to avoid:** Display clear warning text in the UI: "This change only affects the current import batch." Consider a separate "mapping rule suggestion" feature for persistent changes (deferred to v2).
**Warning signs:** HR reports mappings "not working" on new imports.

### Pitfall 5: Housing Fund Amount Inference Edge Cases
**What goes wrong:** `_resolve_housing_amounts()` splits total equally when rates are unknown, producing incorrect per-employee amounts.
**Why it happens:** Some regions provide only total without rate breakdowns.
**How to avoid:** The existing inference logic is sound but add validation warnings when amounts are inferred. Flag records with `inference_notes` in the UI.
**Warning signs:** Housing fund personal + company amounts don't match known rates for a region.

## Code Examples

### Cross-Period Comparison API Endpoint
```python
# backend/app/api/v1/compare.py (extension)
@router.get('/periods', summary="跨期对比", description="按账单所属期对比两个月份的社保数据差异。")
def compare_periods_endpoint(
    left_period: str,
    right_period: str,
    region: Optional[str] = Query(default=None),
    company_name: Optional[str] = Query(default=None),
    page: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    payload = compare_periods(db, left_period, right_period, region=region, company_name=company_name)
    return success_response(payload.model_dump(mode='json'))
```

### Anomaly Detection Service Core
```python
# backend/app/services/anomaly_detection_service.py
INSURANCE_FIELDS = [
    'pension_company', 'pension_personal',
    'medical_company', 'medical_personal',
    'unemployment_company', 'unemployment_personal',
    'injury_company',
    'supplementary_medical_company', 'supplementary_pension_company',
    'large_medical_personal',
    'payment_base',
]

def detect_anomalies(
    db: Session,
    left_period: str,
    right_period: str,
    thresholds: dict[str, float],  # field_name -> percentage
) -> list[AnomalyRecord]:
    # 1. Query left and right period records
    # 2. Match by identity (reuse _build_compare_identity pattern)
    # 3. For each matched pair, check each field against threshold
    # 4. Create AnomalyRecord for threshold-exceeding changes
    ...
```

### Anomaly Threshold Configuration
```python
# backend/app/core/config.py (extension)
# Add to Settings class:
anomaly_threshold_pension: float = 20.0       # percentage
anomaly_threshold_medical: float = 20.0
anomaly_threshold_unemployment: float = 30.0
anomaly_threshold_injury: float = 50.0
anomaly_threshold_maternity: float = 30.0
anomaly_threshold_supplementary: float = 30.0
anomaly_threshold_payment_base: float = 15.0
```

### Inline Mapping Editor Component
```typescript
// Ant Design Table with Select dropdown for canonical_field
const columns: ColumnsType<HeaderMappingItem> = [
  { title: '原始表头', dataIndex: 'raw_header', key: 'raw_header' },
  {
    title: '标准字段',
    dataIndex: 'canonical_field',
    key: 'canonical_field',
    render: (value, record) => (
      <Select
        value={value}
        allowClear
        style={{ width: 200 }}
        options={availableFields.map(f => ({ label: f, value: f }))}
        onChange={(newValue) => handleMappingUpdate(record.id, newValue)}
      />
    ),
  },
  { title: '映射来源', dataIndex: 'mapping_source', render: mappingLabel },
  { title: '置信度', dataIndex: 'confidence', render: confidenceLabel },
];
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Batch-only comparison | Period-based comparison | Phase 11 | Users can compare months directly without knowing batch IDs |
| Manual anomaly checking | Automated threshold detection | Phase 11 | HR no longer needs to eyeball changes across spreadsheets |
| Backend-only mapping management | Full UI for mapping CRUD | Phase 11 | HR self-service for mapping corrections |

## Open Questions

1. **Wuhan Housing Fund Sample**
   - What we know: Wuhan social security sample exists, but no `武汉*公积金*` file found in `data/samples/公积金/`
   - What's unclear: Whether Wuhan housing fund data exists elsewhere or needs to be procured
   - Recommendation: Check if Wuhan housing fund data is embedded in another file; if truly missing, implement parser structure but mark Wuhan housing fund tests as skip-if-no-sample

2. **Anomaly Detection Triggering**
   - What we know: D-05 defines anomaly as adjacent-period comparison
   - What's unclear: Should detection run automatically on import or be manually triggered by HR?
   - Recommendation: Manual trigger (batch run) -- HR selects two periods and clicks "detect anomalies". This matches the existing manual workflow pattern and avoids background job complexity.

3. **Cross-Period Comparison Performance**
   - What we know: Current `compare_batches` loads all records into memory
   - What's unclear: How many records per period (could be hundreds to thousands)
   - Recommendation: Add pagination to the API. For summary view, use SQL GROUP BY with aggregation. Detail view loads on expand.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | None (default discovery in `backend/tests/`) |
| Quick run command | `.venv/bin/pytest backend/tests/ -x -q` |
| Full suite command | `.venv/bin/pytest backend/tests/ -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INTEL-01 | Period comparison returns correct diff rows | unit | `.venv/bin/pytest backend/tests/test_compare_api.py -x -q -k period` | No -- Wave 0 |
| INTEL-02 | Anomaly detection flags threshold-exceeding changes | unit | `.venv/bin/pytest backend/tests/test_anomaly_detection.py -x -q` | No -- Wave 0 |
| INTEL-02 | Anomaly status update (confirm/exclude) persists | unit | `.venv/bin/pytest backend/tests/test_anomaly_api.py -x -q` | No -- Wave 0 |
| INTEL-03 | Housing fund parses correctly for all 6 regions | integration | `.venv/bin/pytest backend/tests/test_housing_fund_service.py -x -q` | Yes (partial) |
| INTEL-04 | Mapping update via API records audit log | unit | `.venv/bin/pytest backend/tests/test_mapping_api.py -x -q -k audit` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `.venv/bin/pytest backend/tests/ -x -q --timeout=30`
- **Per wave merge:** `.venv/bin/pytest backend/tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_anomaly_detection.py` -- covers INTEL-02 anomaly detection service
- [ ] `backend/tests/test_anomaly_api.py` -- covers INTEL-02 anomaly API endpoints
- [ ] Extend `backend/tests/test_compare_api.py` with period comparison tests -- covers INTEL-01
- [ ] Extend `backend/tests/test_housing_fund_service.py` with all 6 regions -- covers INTEL-03
- [ ] Extend `backend/tests/test_mapping_api.py` with audit log verification -- covers INTEL-04

## Sources

### Primary (HIGH confidence)
- Direct codebase inspection of `compare_service.py`, `housing_fund_service.py`, `mapping_service.py` -- verified current implementation patterns
- Direct codebase inspection of `NormalizedRecord` model -- verified all field names and types
- Direct codebase inspection of `AuditLog` model -- verified audit log pattern
- Direct filesystem check of `data/samples/` -- verified housing fund sample availability

### Secondary (MEDIUM confidence)
- CONTEXT.md decisions D-01 through D-15 -- user-confirmed requirements

### Tertiary (LOW confidence)
- Wuhan housing fund sample availability -- could not verify, flagged as open question

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries already in project, no new dependencies needed
- Architecture: HIGH - extending well-established existing patterns with clear code references
- Pitfalls: HIGH - identified from direct code inspection and data availability audit
- Housing fund coverage: MEDIUM - 5 of 6 regions verified, Wuhan housing fund sample unconfirmed

**Research date:** 2026-04-02
**Valid until:** 2026-05-02 (stable -- internal project, no external API changes)
