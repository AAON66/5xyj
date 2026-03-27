# Technology Stack

**Project:** Social Security & Housing Fund Management System (v2 milestone)
**Researched:** 2026-03-27
**Scope:** Auth, employee portal, Feishu integration, premium UI, REST API

## Current Stack Baseline

The existing app runs React 18.3 + FastAPI 0.115 + SQLite + Vite 6.2. No UI framework is installed -- the frontend is raw React with custom CSS. The server requirements file already lists `python-jose[cryptography]` and `passlib[bcrypt]` for auth, but these are not in the main requirements.txt and python-jose is deprecated.

---

## Recommended Stack Additions

### Authentication & RBAC

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| PyJWT | 2.9+ | JWT token encode/decode | python-jose is abandoned (no releases since 2021, incompatible with Python 3.10+). FastAPI officially switched its docs to PyJWT in PR #11589. Lightweight, actively maintained. | HIGH |
| passlib[bcrypt] | 1.7.4+ | Password hashing | Industry standard for bcrypt hashing in Python. Already in server requirements. No reason to change. | HIGH |
| FastAPI Depends + Security | (built-in) | OAuth2 bearer + RBAC decorators | FastAPI's dependency injection is the idiomatic way to do RBAC. No third-party auth framework needed for 3-role system. Custom `role_required` dependency is ~20 lines. | HIGH |

**Architecture decision:** Roll custom RBAC with FastAPI dependencies, NOT a heavy auth framework. The project has only 3 roles (admin/HR/employee) with simple permission rules. Libraries like `fastapi-users` or `fastapi-permissions` add unnecessary abstraction for this use case.

**What NOT to use:**
- `python-jose` -- Deprecated, last release 2021, security issues on Python 3.10+. Replace with PyJWT.
- `fastapi-users` -- Over-engineered for a 3-role internal tool. Brings its own user model, database adapter, and OAuth flows that conflict with the existing SQLAlchemy models.
- `authlib` -- Full OAuth2 server library. Overkill unless you need to BE an OAuth provider (you don't).

**Employee self-service auth:** Employees authenticate with employee_id + id_number + name (triple-factor lookup against existing parsed data). This is NOT JWT-based login -- it is a stateless query verification. No password needed. Implement as a separate lightweight endpoint, not the same auth flow as admin/HR.

### Feishu/Lark Integration

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| lark-oapi | 1.5.3 | Official Lark/Feishu SDK (Python) | Official SDK from larksuite. Covers Bitable (multitable) CRUD, OAuth, event subscriptions. Typed, maintained, documented. | HIGH |
| httpx | 0.28.1 (existing) | HTTP fallback / webhook receiver | Already in the project for DeepSeek calls. Reuse for any raw Feishu API calls not covered by the SDK. | HIGH |

**Bitable sync approach:** Use `lark-oapi` for all multitable operations (list records, create records, update records, batch operations). The SDK provides typed request/response models for Bitable API v1.

**OAuth flow:** Feishu OAuth login uses the standard OAuth2 authorization code flow. `lark-oapi` handles token exchange. Store the Feishu user_id mapping in a local table linked to your user model.

**What NOT to use:**
- `pylark` (chyroc/pylark) -- Community SDK, less maintained than the official `lark-oapi`. No reason to use a community alternative when the official one exists.
- `lark-bitable-sdk` -- Narrow scope (Bitable only), less maintained. The official `lark-oapi` covers Bitable and everything else.

**Key config needed:**
- `FEISHU_APP_ID` -- App credential from Feishu open platform
- `FEISHU_APP_SECRET` -- App secret
- `FEISHU_BITABLE_APP_TOKEN` -- Target multitable app token
- `FEISHU_BITABLE_TABLE_ID` -- Target table within the app

### Frontend UI Framework

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Ant Design | 5.x (latest 5.x stable) | Component library | Best fit for this project: Chinese enterprise context, rich data table/form components out of the box, excellent i18n (zh-CN native), mature admin dashboard patterns. The project is a Chinese company internal tool -- Ant Design is the de facto standard for this context. | HIGH |
| @ant-design/icons | 5.x | Icon set | Consistent with Ant Design, large icon set. | HIGH |
| @ant-design/pro-components | 4.x | ProTable, ProForm, ProLayout | Pre-built admin layout, advanced table with filter/sort/export, form with complex validation. Saves weeks of custom work for admin dashboards. | MEDIUM |

**Why Ant Design 5.x and NOT v6:**
- Ant Design 6.0 was released in early 2026 with React 19 focus and breaking changes. The project is on React 18.3 -- staying on Ant Design 5.x avoids a React version upgrade.
- v5 is battle-tested and still receiving patches. Upgrade to v6 later when React 19 migration happens.

**Why NOT shadcn/ui:**
- shadcn/ui requires Tailwind CSS (not in the project). Adding Tailwind + Radix + shadcn is a larger migration than adding Ant Design.
- shadcn/ui has weaker data table components. This project is data-table-heavy (social security records, employee lists, export previews). Ant Design's Table component with virtual scroll, column pinning, and row selection is far ahead.
- shadcn/ui excels at marketing sites and SaaS products with custom design. This is an internal admin tool that needs density and functionality over aesthetics.
- No Chinese ecosystem support -- Ant Design has native zh-CN locale, date pickers with Chinese calendar, etc.

**Why NOT MUI (Material UI):**
- Google's Material Design language feels foreign in a Chinese enterprise context where Feishu/DingTalk aesthetics dominate.
- MUI's data grid (DataGrid Pro) is paid for advanced features. Ant Design's Table is free and more feature-rich.

### Animation & Premium Feel

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| motion | 12.x | Page transitions, micro-interactions, scroll animations | Renamed from framer-motion in 2025. Import from `motion/react`. The industry standard React animation library. Works alongside Ant Design without conflict. | HIGH |
| @ant-design/cssinjs | (bundled) | Theme tokens, CSS variables | Ant Design 5's built-in theming system. Use CSS variables for the "Feishu-inspired but more refined" look. Custom theme tokens, not a separate CSS framework. | HIGH |

**Design strategy for "Feishu-inspired + premium":**
1. Use Ant Design as the base component layer (functional, clean)
2. Create a custom Ant Design theme with Feishu-like color tokens (blues, clean whites, subtle shadows)
3. Add motion for page transitions, card hover effects, scroll-triggered reveals
4. Custom CSS for the "background + scroll" design details mentioned in requirements

**What NOT to use:**
- Tailwind CSS -- Adding a utility-first CSS framework alongside Ant Design's CSS-in-JS creates two conflicting styling paradigms. Pick one. Ant Design wins here for component richness.
- Aceternity UI / Magic UI / Motion Primitives -- These are Next.js-oriented component collections. They assume Tailwind + shadcn. Don't mix ecosystems.
- GSAP -- Overkill for UI micro-interactions. motion handles everything needed here. GSAP is for timeline-heavy marketing animations.
- Lottie -- Only needed for complex vector animations (loading spinners with brand elements). Not needed for this project's scope.

### REST API Documentation

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| FastAPI Swagger UI | (built-in) | Interactive API explorer at /docs | Already included with FastAPI. Zero config. Developers test endpoints directly. | HIGH |
| FastAPI ReDoc | (built-in) | Clean API reference at /redoc | Already included. Better for stakeholder/external review -- single-page, readable layout. | HIGH |
| Pydantic response models | (existing) | OpenAPI schema generation | Already using Pydantic. Ensure ALL endpoints have explicit `response_model` for auto-generated schemas. | HIGH |

**No additional API documentation tool needed.** FastAPI's built-in Swagger + ReDoc is the standard. Adding Scalar or Stoplight is unnecessary complexity for an internal tool.

### Supporting Libraries

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| APScheduler | 3.10+ | Scheduled Feishu sync jobs | Bidirectional sync on a cron schedule (e.g., every 30 min). Lightweight, no external queue needed. | MEDIUM |
| tenacity | 9.0+ | Retry logic for Feishu API | Feishu API has rate limits. Tenacity provides exponential backoff. | HIGH |
| dayjs | 1.11+ | Date formatting (frontend) | Lightweight date library, Ant Design uses it internally. Consistent date handling. | HIGH |
| ahooks | 3.8+ | React hooks collection | useRequest, useDebounceFn, useVirtualList -- battle-tested hooks from Ant Design ecosystem. Chinese developer ecosystem standard. | MEDIUM |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| JWT | PyJWT | python-jose | Deprecated, no releases since 2021, security issues |
| JWT | PyJWT | authlib | Full OAuth2 server, overkill for JWT signing |
| Auth framework | Custom FastAPI deps | fastapi-users | Over-abstracted for 3-role system, conflicts with existing models |
| Feishu SDK | lark-oapi (official) | pylark | Community maintained, less reliable than official |
| UI framework | Ant Design 5 | shadcn/ui | Requires Tailwind migration, weak data tables, no zh-CN |
| UI framework | Ant Design 5 | MUI | Material Design feels off in Chinese enterprise, paid DataGrid |
| UI framework | Ant Design 5 | Ant Design 6 | React 19 focus, project is on React 18.3 |
| Animation | motion 12 | GSAP | Overkill for UI micro-interactions |
| Animation | motion 12 | react-spring | Less ecosystem support, motion is the standard |
| Scheduler | APScheduler | Celery | Celery needs Redis/RabbitMQ broker -- too heavy for single-machine deploy |
| API docs | Built-in Swagger/ReDoc | Scalar | Unnecessary for internal tool |

---

## Installation

### Backend (add to requirements.txt)

```bash
# Auth
pip install PyJWT>=2.9.0 passlib[bcrypt]>=1.7.4

# Feishu integration
pip install lark-oapi>=1.5.3

# Supporting
pip install APScheduler>=3.10.0 tenacity>=9.0.0
```

### Frontend (add to package.json)

```bash
# UI framework
npm install antd @ant-design/icons @ant-design/pro-components

# Animation
npm install motion

# Supporting
npm install dayjs ahooks
```

### Remove from requirements.server.txt

```
# REMOVE: python-jose[cryptography]>=3.3.0  (deprecated, replace with PyJWT)
```

---

## Configuration Additions

Add to `.env` / `.env.example`:

```bash
# Auth
AUTH_SECRET_KEY=<random-secret>       # Already exists
AUTH_ALGORITHM=HS256
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours for internal tool
AUTH_ENABLED=true                      # Already exists

# Feishu
FEISHU_APP_ID=
FEISHU_APP_SECRET=
FEISHU_BITABLE_APP_TOKEN=
FEISHU_BITABLE_TABLE_ID=
FEISHU_SYNC_INTERVAL_MINUTES=30
FEISHU_OAUTH_ENABLED=false             # Enable when ready
```

---

## Version Compatibility Matrix

| Technology | Min Version | Tested With | Notes |
|------------|-------------|-------------|-------|
| Python | 3.10+ | 3.10+ | Type union syntax requirement |
| Node.js | 18+ | 18+ | Vite 6 requirement |
| React | 18.3 | 18.3.1 | Stay on 18 until Ant Design 6 migration |
| Ant Design | 5.20+ | 5.x latest | Do NOT upgrade to v6 yet |
| motion | 12.x | 12.38.0 | Import from `motion/react` |
| lark-oapi | 1.5+ | 1.5.3 | Official Feishu SDK |
| PyJWT | 2.9+ | 2.9.0 | Replaces python-jose |

---

## Sources

- [FastAPI JWT docs updated to PyJWT - PR #11589](https://github.com/fastapi/fastapi/pull/11589) - HIGH confidence
- [python-jose deprecation discussion](https://github.com/fastapi/fastapi/discussions/11345) - HIGH confidence
- [FastAPI OAuth2 JWT tutorial](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) - HIGH confidence
- [lark-oapi on PyPI](https://pypi.org/project/lark-oapi/) - HIGH confidence
- [Lark Bitable API overview](https://open.larkoffice.com/document/server-docs/docs/bitable-v1/bitable-overview) - HIGH confidence
- [larksuite/oapi-sdk-python on GitHub](https://github.com/larksuite/oapi-sdk-python) - HIGH confidence
- [Ant Design 6.0 release (why to stay on 5.x)](https://github.com/ant-design/ant-design/issues/55804) - HIGH confidence
- [Ant Design vs shadcn comparison](https://www.subframe.com/tips/ant-design-vs-shadcn) - MEDIUM confidence
- [Motion (ex-Framer Motion) upgrade guide](https://motion.dev/docs/react-upgrade-guide) - HIGH confidence
- [Motion npm page](https://www.npmjs.com/package/framer-motion) - HIGH confidence
