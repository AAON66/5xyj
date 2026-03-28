# Phase 3: Security Hardening - Research

**Researched:** 2026-03-28
**Domain:** FastAPI 安全加固（认证补全、频率限制、审计日志、PII 脱敏）
**Confidence:** HIGH

## Summary

本阶段是纯安全加固阶段，不涉及新业务功能开发。Phase 2 已完成 PyJWT 认证体系、RBAC 角色控制和员工验证端点的频率限制。Phase 3 需要在此基础上完成四项工作：(1) 确认所有 PII 端点已受保护，查漏补缺；(2) 为登录端点添加频率限制；(3) 建立审计日志系统；(4) 实现身份证号脱敏。

项目使用 SQLite + SQLAlchemy 作为数据层，FastAPI 作为 Web 框架，Pydantic 作为序列化层。所有安全功能都应在现有架构模式内实现，不需要引入新的外部依赖。

**主要建议:** 审计日志使用 SQLAlchemy 模型 + service 层函数实现（非 middleware），脱敏在 Pydantic schema 序列化层处理，登录频率限制复用现有 RateLimiter 类。

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Phase 2 已为所有路由添加 require_role，此阶段查漏补缺确认无遗漏
- **D-02:** auth_enabled=false 时所有保护跳过（开发模式兼容）
- **D-03:** 员工验证端点已有频率限制（Phase 2 实现：5次/15分钟锁定）
- **D-04:** 登录端点也应添加频率限制（同一 IP 或用户名 5次失败/15分钟锁定）
- **D-05:** 记录范围：登录/登出、数据导出、数据导入/融合、用户管理（创建/编辑/禁用）
- **D-06:** 管理员可在系统界面查看审计日志，支持按时间和操作类型筛选
- **D-07:** 日志存储在数据库（新建 AuditLog 模型），包含：操作类型、操作人、时间、IP、详情
- **D-08:** 日志只读，不可删除和修改
- **D-09:** 脱敏规则：显示前3后4，中间用 * 替代（例：310***1234）
- **D-10:** 导出 Excel 时显示完整身份证号（导出是为了做账，需要完整数据）
- **D-11:** 管理员和 HR 在系统界面看到完整身份证号，员工看到脱敏版本
- **D-12:** 脱敏在 API 响应层处理，不改变数据库存储

### Claude's Discretion
- AuditLog 模型具体字段设计
- 审计日志界面的分页和筛选实现方式
- 脱敏函数的具体实现位置（schema 层 vs middleware 层）
- 登录频率限制是否复用 Phase 2 的 rate_limiter

### Deferred Ideas (OUT OF SCOPE)
None — 讨论内容全部在 Phase 3 范围内。
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SEC-01 | 所有包含 PII 数据的端点必须要求认证 | 路由审计发现 auth、system 路由公开；auth 公开合理，system 需评估；其余已受保护 |
| SEC-02 | 员工查询端点有频率限制（防止身份证号枚举） | 已有 RateLimiter 类可复用于登录端点，员工验证已实现 |
| SEC-03 | 关键操作记录审计日志（登录/导出/数据修改） | 新建 AuditLog 模型 + audit_service，在各端点显式调用 |
| SEC-04 | 身份证号在非必要场景下脱敏显示 | Pydantic computed field / model_validator 实现角色感知脱敏 |
</phase_requirements>

## Standard Stack

### Core（已有，无需新增安装）

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 项目已有 | Web 框架，middleware 和依赖注入 | 已是项目技术栈 |
| SQLAlchemy | 项目已有 | ORM，新建 AuditLog 模型 | 已是项目技术栈 |
| Pydantic | 项目已有 | Schema 序列化层，脱敏在此处处理 | 已是项目技术栈 |
| PyJWT | 项目已有 | 令牌验证 | Phase 2 已采用 |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| RateLimiter（自有） | N/A | 内存频率限制 | 登录端点复用 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| 内存 RateLimiter | slowapi / redis | 单进程部署无需 Redis；如未来多实例部署需迁移 |
| 数据库审计日志 | 文件日志 / ELK | 数据库方案支持前端查询，符合 D-06 要求 |

**无需安装新依赖。** 本阶段所有功能基于现有技术栈实现。

## Architecture Patterns

### 推荐项目结构变更

```
backend/app/
├── models/
│   └── audit_log.py          # 新增：AuditLog 模型
├── schemas/
│   └── audit_log.py          # 新增：审计日志 API schema
├── services/
│   └── audit_service.py      # 新增：审计日志写入服务
├── api/v1/
│   └── audit.py              # 新增：审计日志查询端点
├── utils/
│   └── masking.py            # 新增：脱敏工具函数
```

### Pattern 1: AuditLog 模型设计

**What:** 新建只追加的审计日志表，记录所有安全关键操作
**When to use:** 登录、导出、数据导入/融合、用户管理操作

```python
# backend/app/models/audit_log.py
from backend.app.models.base import Base, UUIDPrimaryKeyMixin, CreatedAtMixin

class AuditLog(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "audit_logs"

    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # 操作类型: login, logout, export, import, aggregate, user_create, user_update, user_disable
    actor_username: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor_role: Mapped[str] = mapped_column(String(20), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # detail 存 JSON 字符串，包含操作相关的额外信息
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
```

**设计要点:**
- 只用 `CreatedAtMixin`，不用 `TimestampMixin`（审计日志不应有 updated_at）
- `detail` 字段存 JSON 字符串，避免为不同操作类型建不同表
- `success` 字段记录操作是否成功（登录失败也要记录）
- 无 `ON DELETE CASCADE`，审计日志独立于其他表

### Pattern 2: 审计服务层

**What:** 纯函数式审计日志写入，在端点代码中显式调用
**Why not middleware:** 审计需要知道业务语义（操作类型、资源 ID），middleware 层只知道 HTTP 动词和路径，无法准确判断

```python
# backend/app/services/audit_service.py
def log_audit(
    db: Session,
    action: str,
    actor_username: str,
    actor_role: str,
    ip_address: Optional[str] = None,
    detail: Optional[dict] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    success: bool = True,
) -> None:
    entry = AuditLog(
        action=action,
        actor_username=actor_username,
        actor_role=actor_role,
        ip_address=ip_address,
        detail=json.dumps(detail, ensure_ascii=False) if detail else None,
        resource_type=resource_type,
        resource_id=resource_id,
        success=success,
    )
    db.add(entry)
    db.commit()
```

**调用点:**
- `auth.py` login_endpoint — 登录成功/失败
- `auth.py` employee_verify_endpoint — 员工验证成功/失败
- `aggregate.py` — 导入/融合操作
- `users.py` — 用户创建/编辑/禁用
- `batch_export_service.py` 或导出端点 — 数据导出

### Pattern 3: 身份证号脱敏

**What:** 基于角色的 API 响应脱敏
**Rule:** 前3后4，中间 `*` 替代（D-09）

```python
# backend/app/utils/masking.py
def mask_id_number(id_number: Optional[str]) -> Optional[str]:
    """将身份证号脱敏为 310***1234 格式"""
    if not id_number or len(id_number) < 7:
        return id_number
    return id_number[:3] + '*' * (len(id_number) - 7) + id_number[-4:]
```

**脱敏位置（推荐）:** 在返回 API 数据的 schema 或端点逻辑中，根据当前用户角色决定是否脱敏。

方案选择 — 推荐 **端点层处理**（非 schema validator）：
- Schema validator 无法感知当前请求的用户角色
- 在端点函数中，根据 `user.role == 'employee'` 决定是否调用 `mask_id_number`
- 管理员/HR 返回完整号码，员工返回脱敏版本
- 导出场景始终使用完整号码（导出逻辑不经过 API schema）

### Pattern 4: 登录频率限制

**What:** 复用现有 `RateLimiter` 类为登录端点添加限制
**Key:** 按用户名 + IP 双维度限制（D-04）

```python
# 在 auth.py 中
_login_rate_limiter = RateLimiter(max_failures=5, lockout_seconds=900)

# login_endpoint 中：
rate_key = f"login:{payload.username}"
if _login_rate_limiter.is_locked(rate_key):
    raise HTTPException(status_code=429, detail="Too many failed attempts.")

# 登录失败时：
_login_rate_limiter.record_failure(rate_key)

# 登录成功时：
_login_rate_limiter.reset(rate_key)
```

### Anti-Patterns to Avoid
- **审计日志放在 middleware:** middleware 无法区分业务操作类型，不适合精确审计
- **脱敏改数据库存储:** 违反 D-12，数据库必须存完整号码
- **schema 层自动脱敏:** Pydantic model 无法感知当前用户角色，会导致管理员也看到脱敏数据
- **审计日志记录完整请求/响应体:** 过度记录，浪费存储，且可能泄露敏感信息

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 频率限制 | 新的限制器 | 复用 `RateLimiter` 类 | 已有线程安全实现，Phase 2 验证通过 |
| IP 地址提取 | 手动解析 headers | `request.client.host` | FastAPI/Starlette 标准 API |
| JSON 序列化 | 自定义格式 | `json.dumps` | 审计详情存 JSON 字符串即可 |

**关键洞察:** 本阶段所有功能都在现有框架能力范围内，不需要引入新库。

## Common Pitfalls

### Pitfall 1: CORS 配置仍为 allow_origins=['*']
**What goes wrong:** STATE.md 明确记录 "CORS allow_origins=['*'] hardcoded for dev -- must restrict in Phase 3"
**Why it happens:** Phase 2 遗留问题
**How to avoid:** 将 CORS origins 改为从 settings 读取 `backend_cors_origins`，开发环境保留 `*`，生产环境配置具体域名
**Warning signs:** main.py 中 `allow_origins=["*"]` 硬编码

### Pitfall 2: 审计日志 commit 与业务 commit 冲突
**What goes wrong:** 审计日志 commit 和业务操作在同一事务中，业务失败时审计也回滚
**Why it happens:** 共用同一个 db session
**How to avoid:** 审计日志应在业务操作成功后单独 commit；登录失败等场景，审计日志需独立事务
**Warning signs:** 审计日志在 try 块内 commit

### Pitfall 3: auth_enabled=false 时审计日志 actor 信息缺失
**What goes wrong:** 开发模式下 `default_authenticated_user()` 返回 `local-dev`，审计日志记录无意义
**Why it happens:** D-02 要求开发模式兼容
**How to avoid:** auth_enabled=false 时审计日志仍正常记录，actor 为 `local-dev`，这是可接受的
**Warning signs:** 审计日志在 auth_disabled 时崩溃

### Pitfall 4: 脱敏函数对短字符串异常
**What goes wrong:** 身份证号不足 7 位时切片出错
**Why it happens:** 测试数据或异常数据
**How to avoid:** 脱敏函数必须处理 None、空字符串、短字符串
**Warning signs:** 未对边界 case 做防守

### Pitfall 5: 审计日志查询端点未限制权限
**What goes wrong:** 非管理员可查看审计日志
**Why it happens:** 忘记添加 require_role
**How to avoid:** 审计日志查询端点必须限制为 admin 角色（D-06 明确"管理员可查看"）

### Pitfall 6: 前端未同步更新
**What goes wrong:** 后端添加了脱敏和审计日志 API，但前端没有对应的界面或处理
**Why it happens:** 只关注后端
**How to avoid:** 需要添加前端审计日志查看页面，以及确保前端正确处理脱敏后的身份证号显示

## Code Examples

### 审计日志查询端点

```python
# backend/app/api/v1/audit.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.dependencies import get_db

router = APIRouter(prefix='/audit-logs', tags=['audit'])

@router.get('')
def list_audit_logs(
    db: Session = Depends(get_db),
    action: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    query = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    if action:
        query = query.filter(AuditLog.action == action)
    # 时间筛选...
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return success_response({...})
```

### IP 地址获取

```python
# FastAPI Request 对象获取客户端 IP
def get_client_ip(request: Request) -> str:
    # 支持反向代理场景
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
```

### 路由注册

```python
# router.py 中新增审计日志路由
from backend.app.api.v1.audit import router as audit_router
api_router.include_router(audit_router, dependencies=[Depends(require_role("admin"))])
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| python-jose | PyJWT | Phase 2 | 已完成迁移，无需再改 |
| 无认证 | require_role RBAC | Phase 2 | 本阶段查漏补缺 |
| 无频率限制 | 内存 RateLimiter | Phase 2 | 员工验证已有，登录需新增 |

**Note:** 项目使用 SQLite，单进程部署，内存频率限制足够。如未来迁移到多实例部署，需改为 Redis。

## Open Questions

1. **前端审计日志页面路由位置**
   - What we know: 管理员侧边栏需要新增入口
   - What's unclear: 放在"系统管理"下还是独立顶级菜单
   - Recommendation: 放在系统管理 (System) 子菜单下，与用户管理并列

2. **审计日志保留策略**
   - What we know: D-08 要求只读不可删
   - What's unclear: 是否需要自动清理（如保留90天）
   - Recommendation: 当前阶段不实现自动清理，表数据量在可控范围内

3. **脱敏是否需要在 dashboard/aggregate 端点中也应用**
   - What we know: EmployeeMasterRead schema 返回 id_number，employees 端点已受 admin/hr 角色保护
   - What's unclear: 是否有其他 schema 也返回 id_number
   - Recommendation: 审查所有返回 id_number 的 schema，确保员工角色访问时脱敏

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | 无独立配置文件，使用默认 |
| Quick run command | `python -m pytest tests/ -x -q` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SEC-01 | PII 端点无 token 返回 401 | integration | `python -m pytest tests/test_security.py::test_pii_endpoints_require_auth -x` | Wave 0 |
| SEC-02 | 登录频率限制生效 | unit | `python -m pytest tests/test_security.py::test_login_rate_limit -x` | Wave 0 |
| SEC-03 | 关键操作产生审计日志 | integration | `python -m pytest tests/test_audit.py -x` | Wave 0 |
| SEC-04 | 员工角色看到脱敏身份证号 | unit | `python -m pytest tests/test_masking.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_security.py` — covers SEC-01, SEC-02
- [ ] `tests/test_audit.py` — covers SEC-03
- [ ] `tests/test_masking.py` — covers SEC-04
- [ ] pytest 需确认可通过 `python -m pytest` 运行（pip install pytest 如果缺失）

## Sources

### Primary (HIGH confidence)
- 项目源码直接审查：`backend/app/` 全部相关模块
- CONTEXT.md 用户决策 D-01 到 D-12
- STATE.md 项目状态和历史决策

### Secondary (MEDIUM confidence)
- FastAPI 官方文档（Request.client.host, middleware 模式）
- Pydantic v2 序列化模式（model_validator, computed_field）

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - 无需新依赖，全部基于现有代码
- Architecture: HIGH - 模式清晰，与现有代码风格一致
- Pitfalls: HIGH - 基于源码审查发现的实际问题（CORS、事务冲突等）

**Research date:** 2026-03-28
**Valid until:** 2026-04-28（稳定技术栈，30天有效）
