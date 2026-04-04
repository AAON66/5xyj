# Milestones

## v1.0 社保公积金管理系统 (Shipped: 2026-04-04)

**Phases completed:** 12 phases, 31 plans, 56 tasks

**Key accomplishments:**

- PyJWT auth with bcrypt passwords, employee triple-factor verification with rate limiting, and require_role RBAC dependency factory
- 1. [Rule 3 - Blocking] Fixed SQLite in-memory StaticPool for test sessions
- Dual-mode login page with localStorage session persistence, employee triple-factor verification UI, and three-role AuthRole support
- AuditLog model with append-only audit service, login rate limiting (5-fail lockout), ID masking utility, audit logging on all key endpoints, and CORS configuration fix
- Admin audit log viewer with action/date filtering and server-side pagination, plus structured 12-point acceptance of all Phase 3 security features
- EmployeeMaster region field with Alembic migration, fault-tolerant import, employee_id+id_number dual matching, and region/company filter APIs
- Region/company dropdown filters on employee list, region field in create/edit forms, and enhanced import result feedback with error details
- Token-bound GET /self-service/my-records endpoint with 9 insurance breakdown fields, housing fund data, multi-period ordering, and data isolation via separate portal router
- React portal page with personal info overview, expandable insurance/housing fund details per billing period, and full role-based route protection for employee isolation
- Backend API for data management with cascading filters, deterministic pagination, quality metrics, and created_by tracking
- DataManagement page with cascading filters, URL persistence, dual-tab layout, and row expansion; Dashboard quality metrics; Imports operator display
- Ant Design 5 with Feishu-style theme, dark sidebar MainLayout, ConfigProvider with zhCN compact mode, and page transition animations
- Commit:
- Async Feishu Bitable client with rate-limited httpx, push/pull sync service with conflict detection and provenance tracking, SyncConfig/SyncJob models, and 16 passing unit tests
- Feishu sync/settings/OAuth API endpoints with NDJSON streaming, CSRF-protected OAuth state validation, and 18 comprehensive tests
- Feishu sync and settings pages with typed API service, feature flag hook, NDJSON streaming, and conditional navigation
- 1. [Rule 3 - Blocking] Added dayjs dependency
- Cross-period comparison API and anomaly detection service with configurable per-field thresholds and status workflow
- Housing fund parsing verified for all 6 regions with per-region tests, mapping updates now create audit log entries, and mapping list API supports source/confidence filtering
- Cross-period comparison page with expandable summary/detail tables and anomaly detection page with threshold config and batch status management
- Dual-entry mapping override with source/confidence filters on standalone page and inline editor on import detail page
- UniqueConstraint and delete-before-insert deduplication ensuring idempotent anomaly detection re-runs
- Fixed 3 frontend-backend path mismatches (Feishu OAuth, Feishu fields, API Keys nav) closing last v1.0 integration gaps

---
