# Roadmap: 社保公积金管理系统

## Overview

Transform the existing Excel merge tool into a complete social insurance & housing fund management platform. The journey starts by stabilizing the one broken feature (Tool template export), then layers on access control, employee-facing capabilities, a professional UI redesign, external API access, Feishu integration, and finally intelligence features. Each phase delivers a coherent, verifiable capability that builds on the previous ones.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Export Stabilization** - Fix Tool template, split exporter, protect Salary template with regression tests
- [ ] **Phase 2: Authentication & RBAC** - Three-role login system with PyJWT tokens and session persistence
- [ ] **Phase 3: Security Hardening** - PII protection, rate limiting, audit logging, ID masking
- [x] **Phase 4: Employee Master Data** - HR can manage and import employee registry for matching (completed 2026-03-29)
- [x] **Phase 5: Employee Portal** - Employees can verify identity and view personal contribution records (completed 2026-03-30)
- [ ] **Phase 6: Data Management** - HR can filter, browse, and audit all social insurance data
- [ ] **Phase 7: Design System & UI Foundation** - Ant Design 5 adoption, Feishu-inspired theme, animations
- [ ] **Phase 8: Page Rebuild & UX Flow** - Role-aware routing, responsive layout, localization, workflow optimization
- [ ] **Phase 9: API System** - RESTful API formalization with API key authentication for external access
- [ ] **Phase 10: Feishu Integration** - Bidirectional Bitable sync with manual triggers and OAuth login
- [ ] **Phase 11: Intelligence & Polish** - Cross-period comparison, anomaly detection, housing fund coverage

## Phase Details

### Phase 1: Export Stabilization
**Goal**: Both dual templates export correctly with maintainable, separated exporter code and a permanent Salary regression safety net
**Depends on**: Nothing (first phase)
**Requirements**: EXPORT-01, EXPORT-02, EXPORT-03, EXPORT-04
**Success Criteria** (what must be TRUE):
  1. Tool template exports with all fields correctly matched to their column headers (no field-title misalignment)
  2. Salary template continues to export identically to its current output (regression test passes)
  3. Exporter code is split into salary_exporter.py, tool_exporter.py, and export_utils.py with no shared mutable state
  4. User can trigger both exports in a single operation and receive two correct files
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md -- Split monolithic exporter into 3 modules + Salary regression tests
- [x] 01-02-PLAN.md -- Fix Tool template field-title alignment + dual export verification

### Phase 2: Authentication & RBAC
**Goal**: Admin and HR users can log in with credentials, employees can verify identity, and all routes enforce role-based access
**Depends on**: Phase 1
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06
**Success Criteria** (what must be TRUE):
  1. Admin/HR can log in with username+password and receive a JWT token (PyJWT, not python-jose)
  2. Employee can verify identity using employee_id + id_number + name combination
  3. Three roles (admin/HR/employee) enforced at route level -- HR cannot access admin routes, employee cannot access HR routes
  4. Admin can create, edit, and disable user accounts from a management interface
  5. User session persists across browser refresh (token stored and auto-attached)
**Plans**: 3 plans

Plans:
- [x] 02-01-PLAN.md -- Backend auth core: PyJWT migration, User model, employee verification, require_role, rate limiter
- [x] 02-02-PLAN.md -- User management CRUD endpoints + RBAC route protection
- [x] 02-03-PLAN.md -- Frontend auth: employee role, localStorage persistence, dual-mode login page

**UI hint**: yes

### Phase 3: Security Hardening
**Goal**: PII data is protected behind authentication with rate limiting, audit trails, and ID masking
**Depends on**: Phase 2
**Requirements**: SEC-01, SEC-02, SEC-03, SEC-04
**Success Criteria** (what must be TRUE):
  1. Every endpoint returning PII (id_number, contribution amounts) requires a valid auth token -- unauthenticated requests receive 401
  2. Employee verification endpoint enforces rate limiting (repeated failed attempts are blocked)
  3. Login, export, and data modification events are recorded in an audit log viewable by admin
  4. ID card numbers display as masked (e.g., 310***1234) in all non-export contexts
**Plans**: 2 plans

Plans:
- [x] 03-01-PLAN.md -- 后端安全基础设施：AuditLog 模型、审计服务、脱敏工具、登录限流、CORS 修复、测试
- [x] 03-02-PLAN.md -- 前端审计日志页面 + 人工验证

### Phase 4: Employee Master Data
**Goal**: HR can maintain a complete employee registry that powers identity verification and data matching
**Depends on**: Phase 2
**Requirements**: MASTER-01, MASTER-02, MASTER-03, MASTER-04
**Success Criteria** (what must be TRUE):
  1. HR can add/edit individual employee records (name, employee_id, id_number, company, region)
  2. HR can bulk-import employee master data from an Excel file
  3. HR can search and filter employee list by name, employee_id, company, or region
  4. Newly imported social insurance data automatically matches against employee master records by employee_id or id_number
**Plans**: 2 plans

Plans:
- [x] 04-01-PLAN.md -- 后端全链路：region 字段迁移、导入容错、双维度匹配、筛选 API、辅助端点
- [x] 04-02-PLAN.md -- 前端完善：地区/公司筛选下拉、region 表单字段、导入反馈增强

**UI hint**: yes

### Phase 5: Employee Portal
**Goal**: Employees can securely view their own social insurance and housing fund contribution records
**Depends on**: Phase 2, Phase 4
**Requirements**: PORTAL-01, PORTAL-02, PORTAL-03, PORTAL-04, PORTAL-05
**Success Criteria** (what must be TRUE):
  1. Employee can view monthly social insurance breakdown (each insurance type, company/personal split)
  2. Employee can view monthly housing fund contribution details
  3. Employee can browse historical records across multiple billing periods
  4. Employee cannot access any other employee's data (attempting to query another ID returns 403)
  5. Contribution details show payment base, each insurance type amount for both company and personal portions
**Plans**: TBD

Plans:
- [x] 05-01: TBD
- [x] 05-02: TBD

**UI hint**: yes

### Phase 6: Data Management
**Goal**: HR can efficiently browse, filter, and audit all social insurance data across regions and periods
**Depends on**: Phase 2, Phase 4
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04
**Success Criteria** (what must be TRUE):
  1. HR can filter social insurance records by region, company, and billing period in a single view
  2. HR can view a full-employee summary with totals across all insurance types
  3. Data quality dashboard shows import health metrics (missing fields, anomalies, duplicates) per import batch
  4. Import history page shows each upload with filename, timestamp, operator name, and record count
**Plans**: 2 plans

Plans:
- [x] 06-01-PLAN.md -- Backend infrastructure: migration, schemas, services, API endpoints, quality metrics, tests
- [x] 06-02-PLAN.md -- Frontend: DataManagement page, Dashboard quality section, Imports enhancement, navigation

**UI hint**: yes

### Phase 7: Design System & UI Foundation
**Goal**: The application adopts Ant Design 5 with a Feishu-inspired theme and polished visual identity
**Depends on**: Phase 2, Phase 5, Phase 6
**Requirements**: UI-01, UI-02, UI-03, UI-04
**Success Criteria** (what must be TRUE):
  1. All pages use Ant Design 5.x components (no legacy custom components remain)
  2. Application has a cohesive Feishu-inspired visual theme (card-based layout, clean typography, professional color palette)
  3. Page transitions and key interactions have smooth animations (not jarring full-page reloads)
  4. Background, spacing, and scrolling have intentional design details that create a premium feel
**Plans**: TBD

Plans:
- [ ] 07-01: TBD
- [ ] 07-02: TBD

**UI hint**: yes

### Phase 8: Page Rebuild & UX Flow
**Goal**: Every page is rebuilt for role-aware navigation, responsive layout, and a smooth end-to-end workflow
**Depends on**: Phase 7
**Requirements**: UI-05, UI-06, UI-07, UI-08
**Success Criteria** (what must be TRUE):
  1. Navigation menu shows different items based on user role (admin sees admin tools, HR sees data management, employee sees portal)
  2. All pages render correctly at 1920x1080, 1440x900, and 1366x768 resolutions
  3. All UI text, labels, and messages display in Chinese with no untranslated strings
  4. Upload-to-export workflow completes in a logical sequence without dead ends or confusing navigation
**Plans**: TBD

Plans:
- [ ] 08-01: TBD
- [ ] 08-02: TBD

**UI hint**: yes

### Phase 9: API System
**Goal**: External programs can access all core functions through a documented REST API with API key authentication
**Depends on**: Phase 2, Phase 3
**Requirements**: API-01, API-02, API-03, API-04, AUTH-07, AUTH-08
**Success Criteria** (what must be TRUE):
  1. REST endpoints cover social insurance queries, employee management, and import/export operations
  2. Swagger/OpenAPI documentation is auto-generated and accessible at /docs
  3. All API responses follow a consistent envelope format (status, data, error, pagination)
  4. External program can authenticate with an API key and call any public endpoint
  5. Admin can create, view, and revoke API keys from the admin interface
**Plans**: TBD

Plans:
- [ ] 09-01: TBD
- [ ] 09-02: TBD

### Phase 10: Feishu Integration
**Goal**: System data syncs bidirectionally with Feishu Bitable via manual triggers, with optional Feishu OAuth login
**Depends on**: Phase 2, Phase 9
**Requirements**: FEISHU-01, FEISHU-02, FEISHU-03, FEISHU-04, FEISHU-05
**Success Criteria** (what must be TRUE):
  1. HR can push social insurance data from the system to a Feishu Bitable with one click
  2. HR can pull updated data from Feishu Bitable back into the system with conflict preview
  3. Sync status page shows history of sync operations (timestamp, direction, records synced, success/failure)
  4. All sync operations are manually triggered (no background auto-sync)
  5. Feishu OAuth login works when enabled via feature flag (disabled by default)
**Plans**: TBD

Plans:
- [ ] 10-01: TBD
- [ ] 10-02: TBD

**UI hint**: yes

### Phase 11: Intelligence & Polish
**Goal**: HR can compare data across periods, detect anomalies, and manage field mappings with full housing fund coverage
**Depends on**: Phase 6
**Requirements**: INTEL-01, INTEL-02, INTEL-03, INTEL-04
**Success Criteria** (what must be TRUE):
  1. HR can view a side-by-side comparison of contribution data across two or more billing periods
  2. System flags records where payment base or amounts changed significantly between periods (configurable threshold)
  3. Housing fund data parses and normalizes correctly for all six supported regions
  4. HR can view and manually override field mappings from a UI when automatic mapping is incorrect
**Plans**: TBD

Plans:
- [ ] 11-01: TBD
- [ ] 11-02: TBD

**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10 -> 11

Note: Phases 4, 5, 6 can partially overlap (4 unblocks 5; 4 and 6 share the Phase 2 dependency). Phases 7 and 8 are sequential. Phase 9 can start after Phase 3.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Export Stabilization | 0/2 | Not started | - |
| 2. Authentication & RBAC | 0/3 | Planning complete | - |
| 3. Security Hardening | 1/2 | In Progress|  |
| 4. Employee Master Data | 2/2 | Complete   | 2026-03-29 |
| 5. Employee Portal | 2/2 | Complete   | 2026-03-30 |
| 6. Data Management | 1/2 | In Progress|  |
| 7. Design System & UI Foundation | 0/2 | Not started | - |
| 8. Page Rebuild & UX Flow | 0/2 | Not started | - |
| 9. API System | 0/2 | Not started | - |
| 10. Feishu Integration | 0/2 | Not started | - |
| 11. Intelligence & Polish | 0/2 | Not started | - |
