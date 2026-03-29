# Phase 5: Employee Portal - Research

**Researched:** 2026-03-28
**Domain:** 员工自助门户（后端 Schema 扩展 + 前端页面改造 + 数据隔离加固）
**Confidence:** HIGH

## Summary

Phase 5 的核心工作是将现有的员工自助查询功能从"简易查询"升级为"安全门户"。当前代码已具备完整的员工验证流程（工号+身份证号+姓名 -> 30分钟 token）和基础查询功能（`lookup_employee_self_service`），但存在三个关键缺口：

1. **后端 Schema 缺失险种明细字段**：`EmployeeSelfServiceRecordRead` 仅返回汇总金额（total_amount, company_total_amount, personal_total_amount）和公积金字段，缺少养老/医疗/失业/工伤/生育等各险种明细和缴费基数。而 `NormalizedRecord` 模型已包含所有这些字段，只需在 Schema 和转换函数中补充。

2. **前端页面需从"查询表单+列表"改造为"概览+可展开明细"模式**：当前 `EmployeeSelfServicePage.tsx`（238行）是无需登录的查询入口，显示汇总金额网格。需要改造为：员工验证后进入概览首页（个人信息+最新月份汇总），下方按月倒序列出历史记录，每条可展开查看各险种拆分。

3. **数据隔离需加固**：当前 self-service/query 端点不要求认证（任何人可调用），且接受前端传入的 person_name/id_number 参数。需新增一个 token 绑定的端点，强制从 token 中的 employee_id 提取身份，不接受前端传入的 ID。

**Primary recommendation:** 分三个阶段实施 -- 先扩展后端 Schema 和服务层，再改造前端页面，最后加固数据隔离并编写安全测试。

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** 默认显示汇总金额（单位合计/个人合计/总额），点击可展开查看各险种明细
- **D-02:** 展开后显示：养老(单位/个人)、医疗(单位/个人)、失业(单位/个人)、工伤(单位)、生育(单位)，加缴费基数
- **D-03:** 后端 EmployeeSelfServiceRecordRead schema 需新增各险种明细字段（pension_company, pension_personal, medical_company, medical_personal, unemployment_company, unemployment_personal, injury_company, maternity_amount）和 payment_base
- **D-04:** lookup_employee_self_service 服务需从 NormalizedRecord 中读取这些字段并填充到返回结果
- **D-05:** 公积金与社保在同一页面并列展示，不分 tab
- **D-06:** 每月记录同时包含社保明细和公积金明细（housing_fund_personal, housing_fund_company, housing_fund_total）
- **D-07:** 当前 schema 已有公积金字段，无需新增
- **D-08:** 所有月份按时间倒序排列（最新月份在前），不分页不筛选
- **D-09:** 每条记录显示：月份、地区、公司、汇总金额，可展开看险种明细
- **D-10:** 后端所有员工查询端点必须强制使用 token 中的 employee_id，不接受前端传入的 ID 参数
- **D-11:** 服务层增加二次校验：即使 API 被篡改，查询条件也必须绑定到当前 token 用户
- **D-12:** 新增测试验证：用 employee A 的 token 尝试查询 employee B 的数据，必须返回 403
- **D-13:** 员工验证后进入概览首页：显示个人信息（姓名、工号、公司、脱敏身份证号）+ 最新月份的缴费汇总
- **D-14:** 概览首页下方是按月份倒序的历史记录列表，可展开查看各险种明细
- **D-15:** 无需独立的"历史明细"页面，概览和历史在同一页面
- **D-16:** 员工登录后无社保记录时，显示友好提示"暂无社保缴费记录，请联系 HR 确认"，不显示空表格
- **D-17:** Token 过期时前端显示"登录已过期，请重新验证"提示，2 秒后自动跳回验证页
- **D-18:** 不支持自动续期（30 分钟是有意设计的安全限制）
- **D-19:** 本阶段不实现导出/打印功能，延后到 Phase 11

### Claude's Discretion
- 概览首页的具体布局（卡片式 vs 列表式）
- 险种明细的展开/折叠动画
- 无数据状态的图标/插画选择
- Token 过期提示的具体 UI 实现

### Deferred Ideas (OUT OF SCOPE)
- 导出/打印个人社保明细 -- 延后到 Phase 11（智能与完善）
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PORTAL-01 | 员工可查看个人社保明细（按月份） | 后端 Schema 扩展 + _to_self_service_record 填充险种字段 + 前端展开明细 UI |
| PORTAL-02 | 员工可查看个人公积金明细（按月份） | Schema 已有公积金字段，前端并列展示即可 |
| PORTAL-03 | 员工可查看历史缴费记录（多期浏览） | 已有 billing_period 排序逻辑，前端改为倒序列表+展开 |
| PORTAL-04 | 员工只能看到自己的数据，无法访问他人信息 | 新增 token 绑定端点 + 服务层二次校验 + 403 测试 |
| PORTAL-05 | 查询结果展示缴费基数、单位/个人各险种金额 | D-02/D-03 定义的字段列表，NormalizedRecord 已有全部字段 |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 项目已有 | 后端 API 框架 | 项目基础设施 |
| Pydantic | 项目已有 | Schema 定义和验证 | FastAPI 标配 |
| SQLAlchemy | 项目已有 | ORM 查询 | 项目基础设施 |
| React | 18.3.x | 前端 UI | 项目基础设施 |
| react-router-dom | 6.30.x | 路由 | 项目已用 |
| axios | 1.8.x | HTTP 请求 | 项目已用 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| PyJWT | 项目已有 | Token 生成/验证 | 员工 token 验证 |
| pytest | 项目已有 | 后端测试 | 数据隔离测试 |

### Alternatives Considered
无需引入新依赖。所有功能均可用现有技术栈实现。

## Architecture Patterns

### 现有代码结构（不变）
```
backend/app/
├── api/v1/employees.py      # self-service 端点（需新增 token 绑定端点）
├── api/v1/auth.py            # employee-verify 端点（已完成）
├── schemas/employees.py      # EmployeeSelfServiceRecordRead（需扩展字段）
├── services/employee_service.py  # lookup_employee_self_service（需扩展）
├── models/normalized_record.py   # NormalizedRecord（已有全部字段）
├── core/auth.py              # AuthUser, verify_access_token
├── dependencies.py           # require_authenticated_user, require_role
└── utils/masking.py          # mask_id_number

frontend/src/
├── pages/EmployeeSelfService.tsx  # 主页面（需大幅改造）
├── services/employees.ts         # API 调用（需新增接口）
├── services/authSession.ts       # token 读写
└── services/api.ts               # axios 拦截器（已有 401 自动清除 session）
```

### Pattern 1: 后端 Schema 扩展
**What:** 在 `EmployeeSelfServiceRecordRead` 中新增险种明细字段和 payment_base
**When to use:** D-03 要求
**Example:**
```python
# backend/app/schemas/employees.py
class EmployeeSelfServiceRecordRead(BaseModel):
    # ... 现有字段保持不变 ...
    payment_base: Optional[Decimal] = None
    pension_company: Optional[Decimal] = None
    pension_personal: Optional[Decimal] = None
    medical_company: Optional[Decimal] = None
    medical_personal: Optional[Decimal] = None
    unemployment_company: Optional[Decimal] = None
    unemployment_personal: Optional[Decimal] = None
    injury_company: Optional[Decimal] = None
    maternity_amount: Optional[Decimal] = None
```

### Pattern 2: Token 绑定查询端点
**What:** 新增 `/employees/self-service/my-records` 端点，从 token 中提取 employee_id，不接受前端传参
**When to use:** D-10/D-11 要求
**Example:**
```python
# backend/app/api/v1/employees.py
@router.get('/self-service/my-records')
def employee_portal_records_endpoint(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_role("employee")),
):
    # user.username 就是 employee_id（employee-verify 时 sub=payload.employee_id）
    result = lookup_employee_portal(db, employee_id=user.username)
    return success_response(result.model_dump(mode='json'))
```

### Pattern 3: 前端 Token 过期检测
**What:** 利用现有 `isAuthSessionExpired` + axios 401 拦截器，加上倒计时跳转
**When to use:** D-17/D-18 要求
**Example:**
```typescript
// 前端检测到 401 或 session 过期时
useEffect(() => {
  if (isExpired) {
    const timer = setTimeout(() => navigate('/login'), 2000);
    return () => clearTimeout(timer);
  }
}, [isExpired]);
```

### Pattern 4: 可展开记录卡片
**What:** 每条月度记录默认显示汇总，点击展开显示险种明细网格
**When to use:** D-01/D-09 要求
**Example:**
```typescript
function RecordCard({ record }: { record: EmployeeSelfServiceRecord }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <article>
      <header onClick={() => setExpanded(!expanded)}>
        {/* 月份、地区、公司、汇总金额 */}
      </header>
      {expanded && (
        <div className="insurance-details">
          {/* 各险种明细网格 */}
        </div>
      )}
    </article>
  );
}
```

### Anti-Patterns to Avoid
- **前端传入 employee_id 查询:** 绝对不能让前端参数决定查询哪个员工的数据，必须从 token 提取
- **复用旧的 self-service/query 端点:** 该端点不需要认证，应保留给"无登录查询"场景，门户使用新端点
- **在前端做数据过滤:** 安全边界必须在后端，前端只负责展示

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Token 验证 | 自定义 token 解析 | `require_role("employee")` + `AuthUser.username` | 已有完整的依赖注入链 |
| 身份证号脱敏 | 自写正则 | `mask_id_number()` from `utils/masking.py` | Phase 3 已实现 |
| API 认证拦截 | 手动添加 header | `attachApiInterceptors` 的 `readAuthSession` 逻辑 | 已在 api.ts 中自动附加 Bearer token |
| 401 自动清除 session | 自写拦截器 | api.ts 的 response interceptor | 已处理 401 -> clearAuthSession |
| 金额格式化 | 自写工具函数 | 现有 `formatMoney()` | EmployeeSelfService.tsx 已有 |
| 日期格式化 | 自写工具函数 | 现有 `formatDateTime()` | EmployeeSelfService.tsx 已有 |

**Key insight:** 这个阶段 90% 的基础设施已就绪，核心工作是"扩展字段 + 改造 UI + 加固安全"，而不是从零构建。

## Common Pitfalls

### Pitfall 1: employee-verify token 的 sub claim
**What goes wrong:** 误以为 token sub 是 username 或 person_name，实际是 employee_id
**Why it happens:** `employee_verify_endpoint` 调用 `issue_access_token(sub=payload.employee_id, role="employee")`，而 `verify_access_token` 将 sub 解析为 `AuthUser.username`
**How to avoid:** 门户端点中 `user.username` 就是 `employee_id`，直接用于数据库查询条件
**Warning signs:** 查询结果为空或返回错误员工的数据

### Pitfall 2: 旧查询端点不应被移除
**What goes wrong:** 改造时误删 `/employees/self-service/query` 端点
**Why it happens:** 以为门户端点替代了旧端点
**How to avoid:** 旧端点是"无需登录的快速查询"，门户端点是"登录后的安全查询"，两者并存
**Warning signs:** EmployeeSelfServicePage 的无登录查询功能失效

### Pitfall 3: Decimal 序列化
**What goes wrong:** Pydantic Decimal 字段序列化为字符串而非数字
**Why it happens:** `model_dump(mode='json')` 对 Decimal 的处理
**How to avoid:** 前端 `EmployeeSelfServiceRecord` 类型已定义为 `string | number | null`，`formatMoney` 已处理两种情况，保持一致即可
**Warning signs:** 前端显示 NaN 或 undefined

### Pitfall 4: 路由保护不到位
**What goes wrong:** 员工门户页面在未登录状态可访问
**Why it happens:** 当前 `/employee/query` 不在 `ProtectedRoute` 下
**How to avoid:** 门户页面需放在 `ProtectedRoute` + `RoleRoute({ allowedRoles: ['employee'] })` 下
**Warning signs:** 未登录直接访问门户 URL 能看到内容

### Pitfall 5: 展开状态管理
**What goes wrong:** 展开一条记录后滚动位置跳动，或多条同时展开导致性能问题
**Why it happens:** 纯 CSS 高度变化没有过渡
**How to avoid:** 使用简单的条件渲染（`{expanded && <div>...</div>}`），不需要动画库
**Warning signs:** 用户体验生硬

## Code Examples

### 1. _to_self_service_record 扩展（后端核心改动）
```python
# backend/app/services/employee_service.py - _to_self_service_record 函数
def _to_self_service_record(record: NormalizedRecord, batch: ImportBatch) -> EmployeeSelfServiceRecordRead:
    return EmployeeSelfServiceRecordRead(
        # ... 现有字段 ...
        payment_base=record.payment_base,
        pension_company=record.pension_company,
        pension_personal=record.pension_personal,
        medical_company=record.medical_company,
        medical_personal=record.medical_personal,
        unemployment_company=record.unemployment_company,
        unemployment_personal=record.unemployment_personal,
        injury_company=record.injury_company,
        maternity_amount=record.maternity_amount,
        # ... 现有字段 ...
    )
```

### 2. Token 绑定查询服务（新建）
```python
# backend/app/services/employee_service.py - 新函数
def lookup_employee_portal(db: Session, employee_id: str) -> EmployeeSelfServiceRead:
    """Token 绑定的员工门户查询 -- employee_id 来自 token，不可伪造。"""
    employee = (
        db.query(EmployeeMaster)
        .filter(EmployeeMaster.employee_id == employee_id)
        .filter(EmployeeMaster.active == True)  # noqa: E712
        .first()
    )
    if employee is None:
        raise EmployeeSelfServiceNotFoundError("Employee not found.")

    # 用 employee_id 精确查询，而非 person_name + id_number
    rows = (
        db.query(NormalizedRecord, ImportBatch)
        .join(ImportBatch, ImportBatch.id == NormalizedRecord.batch_id)
        .outerjoin(MatchResult, MatchResult.normalized_record_id == NormalizedRecord.id)
        .filter(
            or_(
                MatchResult.employee_master_id == employee.id,
                NormalizedRecord.employee_id == employee.employee_id,
                and_(
                    NormalizedRecord.person_name == employee.person_name,
                    NormalizedRecord.id_number == employee.id_number,
                ),
            )
        )
        .order_by(ImportBatch.created_at.desc(), NormalizedRecord.created_at.desc())
        .all()
    )
    # ... 去重和组装 ...
```

### 3. 前端 TypeScript 接口扩展
```typescript
// frontend/src/services/employees.ts
export interface EmployeeSelfServiceRecord {
  // ... 现有字段 ...
  payment_base: string | number | null;
  pension_company: string | number | null;
  pension_personal: string | number | null;
  medical_company: string | number | null;
  medical_personal: string | number | null;
  unemployment_company: string | number | null;
  unemployment_personal: string | number | null;
  injury_company: string | number | null;
  maternity_amount: string | number | null;
}

// 新增门户 API 调用
export async function fetchPortalRecords(): Promise<EmployeeSelfServiceResult> {
  const response = await apiClient.get<ApiSuccessResponse<EmployeeSelfServiceResult>>(
    '/employees/self-service/my-records'
  );
  return response.data.data;
}
```

### 4. 数据隔离测试
```python
# backend/tests/test_employee_portal_api.py
def test_employee_cannot_access_other_employee_data():
    """D-12: 用 employee A 的 token 尝试查询 employee B 的数据，必须返回 403 或只返回 A 的数据"""
    # 1. 创建 employee A 和 B
    # 2. 用 A 的 token 调用 /self-service/my-records
    # 3. 验证返回的数据只属于 A
    # 4. 端点不接受任何可让 A 查 B 数据的参数
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| self-service/query 无需认证 | 门户端点强制 token 认证 | Phase 5 | 数据隔离从"可选"变"强制" |
| 只返回汇总金额 | 返回各险种明细 | Phase 5 | 员工可看到完整缴费拆分 |
| 前端无 token 过期处理 | 401 拦截 + 2秒后跳转 | Phase 5 | 安全体验提升 |

## Open Questions

1. **旧 self-service/query 端点是否保留？**
   - What we know: 当前它是无需登录的查询入口，EmployeeSelfServicePage 使用它
   - What's unclear: Phase 5 改造后是否还需要无登录查询
   - Recommendation: 保留旧端点不变（供可能的公开查询场景），新增门户端点。EmployeeSelfService 页面改造为使用门户端点（需登录）

2. **员工门户路由规划**
   - What we know: 当前 `/employee/query` 不在 ProtectedRoute 下
   - What's unclear: 改造后是否改 URL 还是保持 `/employee/query`
   - Recommendation: 保持 `/employee/query` URL 但将其移入 `ProtectedRoute` + `RoleRoute(['employee'])`，员工验证后自动跳转到该页面（现有 `DEFAULT_WORKSPACE_BY_ROLE.employee` 已设为此路径）

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.x |
| Config file | 无独立配置文件，使用默认发现 |
| Quick run command | `pytest backend/tests/test_employee_portal_api.py -x` |
| Full suite command | `pytest backend/tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PORTAL-01 | 社保明细按月显示（含各险种字段） | unit | `pytest backend/tests/test_employee_portal_api.py::test_portal_returns_insurance_breakdown -x` | Wave 0 |
| PORTAL-02 | 公积金明细按月显示 | unit | `pytest backend/tests/test_employee_portal_api.py::test_portal_returns_housing_fund -x` | Wave 0 |
| PORTAL-03 | 历史记录多期浏览 | unit | `pytest backend/tests/test_employee_portal_api.py::test_portal_returns_multiple_periods -x` | Wave 0 |
| PORTAL-04 | 数据隔离（403 测试） | unit | `pytest backend/tests/test_employee_portal_api.py::test_employee_cannot_access_others -x` | Wave 0 |
| PORTAL-05 | 缴费基数和各险种金额 | unit | `pytest backend/tests/test_employee_portal_api.py::test_portal_includes_payment_base_and_amounts -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest backend/tests/test_employee_portal_api.py -x`
- **Per wave merge:** `pytest backend/tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_employee_portal_api.py` -- 新文件，覆盖 PORTAL-01 ~ PORTAL-05
- [ ] 测试 fixtures: 复用 `test_employee_master_api.py` 中的 `build_test_context` 模式

## Sources

### Primary (HIGH confidence)
- 项目源码直接阅读:
  - `backend/app/schemas/employees.py` -- 确认当前 Schema 缺失字段
  - `backend/app/services/employee_service.py` -- 确认 `_to_self_service_record` 转换逻辑
  - `backend/app/models/normalized_record.py` -- 确认 NormalizedRecord 已有全部险种字段
  - `backend/app/api/v1/auth.py` -- 确认 employee-verify 的 token sub = employee_id
  - `backend/app/core/auth.py` -- 确认 AuthUser.username = token sub
  - `backend/app/dependencies.py` -- 确认 require_role 机制
  - `frontend/src/pages/EmployeeSelfService.tsx` -- 确认当前 UI 结构
  - `frontend/src/services/authSession.ts` -- 确认 token 过期检测逻辑
  - `frontend/src/services/api.ts` -- 确认 401 拦截器已有
  - `frontend/src/App.tsx` -- 确认路由结构

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - 无新依赖，全部使用现有技术栈
- Architecture: HIGH - 扩展模式清晰，所有源文件已审查
- Pitfalls: HIGH - 基于代码审查发现的实际问题

**Research date:** 2026-03-28
**Valid until:** 2026-04-28（项目内部代码，稳定性高）
