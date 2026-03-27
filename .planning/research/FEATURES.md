# Feature Landscape

**Domain:** Chinese Enterprise Social Insurance & Housing Fund Management (社保公积金管理系统)
**Researched:** 2026-03-27
**Mode:** Ecosystem research for milestone transition (Excel tool -> management system)

## Table Stakes

Features users expect from any internal social insurance management system. Missing = product feels incomplete or unprofessional.

| # | Feature | Why Expected | Complexity | Notes |
|---|---------|--------------|------------|-------|
| 1 | **Role-based access control (Admin/HR/Employee)** | Every enterprise system has permission boundaries. HR sees all, employees see only their own data. Without this, system is unusable in a real company. | Medium | Three roles sufficient for this domain. No need for fine-grained ABAC. |
| 2 | **Employee self-service query** | Employees expect to check their own social insurance contributions without asking HR every time. This is the #1 reason employees would use the system at all. | Medium | Login via employee ID + ID card number + name (no password system needed for read-only access). |
| 3 | **Multi-period data browsing** | Users need to view and compare data across months (e.g., Feb vs Jan contributions). A system that only shows the latest import is a tool, not a management system. | Low-Med | Period selector + historical batch data. Requires data retention strategy. |
| 4 | **Data search and filtering** | HR must filter by region, company, employee name, ID number, insurance type. Without robust filtering, large datasets (hundreds of employees across 6+ regions) become unmanageable. | Medium | Full-text search on name/ID + faceted filters on region, company, period, match status. |
| 5 | **Export to standard templates** | Already implemented (dual template export). This is absolute table stakes for any social insurance tool. | Done | Salary template working perfectly. Tool template has field mapping issues to fix. |
| 6 | **Data validation dashboard** | HR needs to see at a glance: how many records imported, how many validated, how many have issues, how many matched. Without visibility into data quality, trust in the system collapses. | Medium | Existing dashboard endpoint exists but frontend needs redesign. |
| 7 | **Import history and audit trail** | HR must be able to trace any number back to its source file and row. Required for accountability during payroll disputes. | Low | Largely exists via ImportBatch + source_file_name + source_row_number. Needs UI exposure. |
| 8 | **Employee master data management** | A central registry of employees (name, ID, employee number, company, region) that incoming social insurance data matches against. Without this, matching is impossible. | Medium | Partially exists. Needs CRUD UI for HR to maintain. |
| 9 | **Responsive, professional UI** | Internal tools with ugly UIs get abandoned. Feishu-inspired design signals quality and encourages adoption. | High | Full frontend redesign planned. |
| 10 | **Secure authentication** | JWT auth with proper session management. Even for internal tools, preventing unauthorized access to salary/insurance data is a legal and compliance requirement. | Medium | JWT auth exists in backend. Needs proper login UI and session handling. |

## Differentiators

Features that set this product apart from generic HR SaaS. Not expected but highly valued by users.

| # | Feature | Value Proposition | Complexity | Notes |
|---|---------|-------------------|------------|-------|
| 1 | **Feishu Bitable bidirectional sync** | Company already uses Feishu. Pushing aggregated social insurance data to a shared Bitable means HR managers who live in Feishu never need to open another tool. Pulling updates back keeps both systems consistent. This is a killer feature for Feishu-native organizations. | High | Feishu Bitable API supports batch CRUD (up to 1000 records/request), webhooks for change notifications. Requires tenant_access_token or user_access_token. Rate limits recommend single write at a time per Bitable. |
| 2 | **REST API for external integration** | Enables other internal tools (payroll systems, reporting dashboards, custom scripts) to pull social insurance data programmatically. Transforms the system from an isolated tool into a data platform. | Medium | FastAPI makes this natural. Need versioned API docs (OpenAPI/Swagger already built-in). |
| 3 | **Intelligent header recognition with LLM fallback** | Already implemented. No competitor in the internal-tool space does rule-based + LLM hybrid header mapping for multi-region social insurance Excel files. This is genuinely unique. | Done | Maintain and improve. This is the core technical moat. |
| 4 | **Cross-period comparison and trend view** | Show an employee's contribution trend over months. HR can spot anomalies (sudden base changes, missing months) at a glance. Most internal tools just show flat tables. | Medium | Requires storing multiple periods and a simple line/bar chart component. |
| 5 | **Anomaly detection and alerts** | Automatically flag: contribution base changes, missing employees compared to last month, new employees not in master data, amount discrepancies between regions. Proactive rather than reactive. | Medium-High | Build on existing validation service. Add diff logic between periods. |
| 6 | **One-click re-export after corrections** | After HR fixes validation issues or mapping overrides, re-export without re-uploading. Saves significant time in the monthly cycle. | Low-Med | Existing pipeline supports this conceptually. Need UI trigger. |
| 7 | **Feishu OAuth login** | Single sign-on via Feishu identity. Eliminates separate credential management for a Feishu-native company. | Medium | Feishu OAuth 2.0 is well-documented. Optional enhancement after basic auth works. |
| 8 | **Housing fund unified view** | Display social insurance and housing fund data side-by-side per employee. Most tools treat them separately. Unified view = complete picture for HR. | Medium | Housing fund parsing partially exists. Needs full standardization and UI integration. |
| 9 | **Batch import progress with granular feedback** | NDJSON streaming already exists. Add per-file, per-region progress indicators with success/failure counts. Makes large imports (20+ files) manageable. | Low | Enhance existing streaming infrastructure. |
| 10 | **Mapping override UI** | Let HR manually correct header-to-field mappings and have those corrections persist as rules for future imports. Turns HR knowledge into system intelligence. | Medium | Backend mapping review endpoint exists. Needs interactive UI. |

## Anti-Features

Features to explicitly NOT build. Including these would increase complexity without proportional value, or would conflict with the project's scope and constraints.

| # | Anti-Feature | Why Avoid | What to Do Instead |
|---|--------------|-----------|-------------------|
| 1 | **Salary/payroll calculation** | Out of scope per PROJECT.md. Social insurance data informs payroll but this system must not become a payroll engine. Mixing concerns creates liability and regulatory risk. | Export clean data to payroll systems via API or Excel templates. |
| 2 | **Government portal integration (direct submission)** | Each city's social insurance bureau has different submission portals, formats, and authentication methods. Automating government submissions is a massive, ever-changing compliance surface. | Generate the Excel files that HR manually uploads to government portals. The system is a data aggregation layer, not a submission layer. |
| 3 | **Multi-tenant / SaaS architecture** | Single company internal use. Adding tenant isolation, billing, onboarding flows would multiply complexity 5-10x for zero benefit. | Keep single-tenant SQLite deployment. |
| 4 | **Mobile native app** | Out of scope per PROJECT.md. The responsive web UI covers mobile access adequately for query use cases. | Ensure frontend is mobile-responsive for employee self-service queries. |
| 5 | **Complex workflow / approval engine** | Social insurance data import does not require multi-step approvals in this company's workflow. Building a BPMN-style engine is massive over-engineering. | Simple status progression (imported -> validated -> exported) with role-based action permissions. |
| 6 | **Custom report builder** | Drag-and-drop report designers are complex to build and rarely used well. Feishu Bitable already serves as an ad-hoc analysis tool. | Provide fixed dashboards + API access + Feishu Bitable sync for custom analysis needs. |
| 7 | **Real-time collaboration / multi-user editing** | This is a batch processing system, not a collaborative document. Concurrent editing of the same batch creates conflict resolution nightmares. | Lock batches during processing. One user imports at a time. Others view results. |
| 8 | **Employee onboarding/offboarding workflows** | HR management scope creep. This system manages social insurance data, not the full employee lifecycle. | Maintain employee master data (CRUD) but leave lifecycle management to dedicated HR systems. |
| 9 | **SMS/email notification system** | Over-engineering for an internal tool. Feishu already handles company communication. | Use Feishu bot messages if notifications are needed (much simpler than SMS/email infrastructure). |
| 10 | **Detailed permission customization per field** | Field-level access control (e.g., "HR can see pension but not medical") is extreme granularity that no one has asked for. Three roles with clear boundaries is sufficient. | Admin sees everything, HR sees all employee data, Employee sees only their own record. |

## Feature Dependencies

```
Employee Master Data Management
  |
  +---> Employee Self-Service Query (needs master data to authenticate)
  |
  +---> Data Matching (needs master data to match against)
  |
  +---> Anomaly Detection (needs master data for "missing employee" checks)

Role-Based Access Control
  |
  +---> Employee Self-Service Query (needs role enforcement)
  |
  +---> Admin/HR Data Management (needs role-gated views)
  |
  +---> REST API (needs API key / token scoping)
  |
  +---> Feishu OAuth Login (alternative auth provider, same role model)

Secure Authentication (JWT)
  |
  +---> RBAC (auth is prerequisite for authorization)
  |
  +---> All protected routes

Multi-Period Data Storage
  |
  +---> Cross-Period Comparison
  |
  +---> Trend View
  |
  +---> Employee Self-Service (show history)

Data Validation Dashboard
  |
  +---> Anomaly Detection (extends validation with cross-period logic)

Tool Template Fix
  |
  +---> Dual Template Export (both must work before system is "complete")

Frontend Redesign
  |
  +---> All user-facing features depend on this for usability
  |
  (But can be done incrementally, page by page)

Feishu Bitable Sync
  |
  +---> Feishu OAuth Login (optional, but natural pairing)
  |
  +---> REST API (sync service uses internal API patterns)
```

## MVP Recommendation

For the milestone transition from "Excel tool" to "management system," prioritize in this order:

### Phase 1: Foundation (must ship together)
1. **Tool template export fix** - Existing broken feature. Fix before adding new features.
2. **RBAC (Admin/HR/Employee roles)** - Gate everything behind proper permissions.
3. **Secure authentication UI** - Login page, session management, JWT flow in frontend.
4. **Employee master data CRUD** - HR needs to manage the employee registry.
5. **Frontend redesign: core layout** - Navigation, role-aware routing, Feishu-inspired shell.

### Phase 2: Self-Service and Management
6. **Employee self-service query page** - The headline feature for non-HR users.
7. **Data search and filtering (HR view)** - Make large datasets manageable.
8. **Multi-period data browsing** - View historical imports by month.
9. **Data validation dashboard redesign** - Visual overview of import health.
10. **Import history and audit trail UI** - Traceability for HR.

### Phase 3: Integration and Intelligence
11. **REST API documentation and versioning** - Formalize the API for external use.
12. **Feishu Bitable bidirectional sync** - The flagship differentiator.
13. **Feishu OAuth login** - SSO convenience.
14. **Cross-period comparison** - Trend analysis for HR.
15. **Anomaly detection** - Proactive data quality.

### Phase 4: Polish
16. **Mapping override UI** - HR-driven system improvement.
17. **One-click re-export** - Workflow efficiency.
18. **Housing fund unified view** - Complete data picture.
19. **Batch import progress enhancement** - UX refinement.

### Defer Indefinitely
- **Salary calculation** - Out of scope, stay out of scope.
- **Government portal integration** - Too much compliance surface.
- **Custom report builder** - Feishu Bitable covers this.

## Rationale for Ordering

1. **Fix before extend**: The broken Tool template must work before anything new ships.
2. **Auth before features**: No point building employee self-service without authentication and roles.
3. **Data management before querying**: Employee master data must be maintainable before self-service queries make sense.
4. **Internal users before external integration**: HR and employees use the system daily. Feishu sync and API serve secondary workflows.
5. **Intelligence after data**: Anomaly detection and trends require multiple periods of clean data to be meaningful.

## Chinese Enterprise Context Notes

### Monthly Cycle Reality
Social insurance management in Chinese enterprises follows a strict monthly cycle:
1. **Month-end/start**: Regional social insurance bureaus publish contribution statements
2. **Days 1-5**: HR collects Excel files from multiple regions and companies
3. **Days 3-7**: HR aggregates, validates, and reconciles
4. **Days 5-10**: Data exported to payroll team and finance
5. **Day 15**: Social insurance contributions due

The system must optimize for this burst workflow: fast bulk import, quick validation, immediate export.

### Multi-Region Complexity
The defining challenge is that China has no national standard format for social insurance statements. Each city (and sometimes each district within a city) produces different Excel formats. This project already handles 6 regions, which is typical for a mid-size company. Large companies may need 20+ region parsers.

### Feishu as the Enterprise Hub
In Feishu-native companies, Feishu is the single pane of glass for work. Social insurance data that only lives in a separate web app gets forgotten. Bidirectional Bitable sync makes the data visible where people already work, which is why this is the top differentiator rather than a nice-to-have.

### Employee Self-Service Authentication
Chinese enterprise systems commonly use employee ID + ID card number as authentication factors rather than username/password. This is because:
- Employees already know these identifiers
- No password reset workflow needed
- ID card numbers are 18 digits and serve as a strong second factor
- The data being accessed is the employee's own social insurance records (moderate sensitivity)

For this system, the three-factor check (employee ID + ID card last 6 digits + name) is standard practice and sufficient.

## Sources

- [Feishu Bitable API Overview](https://open.feishu.cn/document/server-docs/docs/bitable-v1/bitable-overview) - Official API docs, HIGH confidence
- [Feishu Bitable FAQ](https://www.feishu.cn/hc/zh-CN/articles/336307279050) - API limitations and common issues
- [HROne Guide to China's Social Security](https://hrone.com/blog/guide-chinas-social-security-system-pays/) - Domain context
- [IBM RBAC Overview](https://www.ibm.com/think/topics/rbac) - RBAC patterns
- [2025 HR System Comparison (Chinese)](https://www.cnblogs.com/worktile/articles/19132742) - Competitor landscape (i人事, 北森)
- [JianDaoYun Social Insurance Management](https://www.jiandaoyun.com/news/article/693bd49953dc557abce3e505) - Feature expectations
- [China Social Insurance Guide 2025](https://www.hongdaservice.com/blog/china-social-insurance-guide-2025) - Regulatory context
