# Phase 13: 基础准备与部署适配 - Research

**Researched:** 2026-04-04
**Domain:** Python 3.9 兼容性、技术债清理、审计日志增强、前端小修复
**Confidence:** HIGH

## Summary

Phase 13 是 v1.1 的首个阶段，目标是让系统能在 Python 3.9 云服务器上稳定运行，同时清理 v1.0 遗留的技术债。核心工作分四大块：(1) Python 3.9 兼容性修复（移除 `slots=True`、锁定依赖版本上界）；(2) 技术债清理（常量合并、废弃组件删除、依赖清理）；(3) 审计日志 IP 解析增强（支持反向代理场景）；(4) 快速融合页面小修复（文件计数显示、主档默认值智能切换）。

所有决策已在 CONTEXT.md 中锁定，无需探索替代方案。经验证，当前使用的所有核心依赖（FastAPI 0.115.0、Pydantic 2.10.3、pandas 2.2.3、SQLAlchemy 2.0.36、openpyxl 3.1.5）均兼容 Python 3.9，但必须锁定版本上界以防自动升级到不兼容版本。

**Primary recommendation:** 按 D-01 到 D-18 的决策序号分组执行，优先完成 Python 3.9 兼容性修复（阻断部署），然后并行推进技术债清理和前端修复。

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** 移除所有 `@dataclass(slots=True)` 装饰器（10+ 文件）
- **D-02:** 确保所有文件有 `from __future__ import annotations`（当前大部分已有）
- **D-03:** 依赖版本锁定：`fastapi>=0.115.0,<0.130.0`，`pandas>=2.2.3,<2.3.0`，确保兼容 3.9
- **D-04:** 不存在 `match/case` 和 `isinstance(x, A|B)` 运行时用法（已验证安全）
- **D-05:** 增强 `get_client_ip()`：增加 `X-Real-IP` 作为备选头
- **D-06:** 添加 trusted proxy 配置项到 settings
- **D-07:** 输出 nginx 反向代理配置示例文档
- **D-08:** 当审计日志检测到全部 IP 为 127.0.0.1 时，在前端审计日志页面显示提示
- **D-09:** 添加 `xlrd>=2.0.0` 到 `requirements.txt`
- **D-10:** 清理 `requirements.server.txt`：移除 `python-jose` 和 `passlib`，考虑合并为单一 requirements 文件
- **D-11:** 移除未使用依赖：`psycopg2-binary`、`asyncpg`、`loguru`
- **D-12:** 合并 `REGION_LABELS` 到单一位置（`backend/app/mappings/regions.py`）
- **D-13:** 合并 `FILENAME_NOISE`、`DATE_PATTERN`、`_infer_company_name_from_filename` 到共享工具模块
- **D-14:** 合并 `ID_NUMBER_PATTERN`、`NON_MAINLAND_ID_NUMBER_PATTERN` 到共享 validators/constants 模块
- **D-15:** 删除 v1.0 遗留 5 个废弃组件文件：AppShell, GlobalFeedback, PageContainer, SectionState, SurfaceNotice
- **D-16:** 修复自助查询端点 `/employees/self-service/query` 缺少认证的安全隐患
- **D-17:** 上传文件计数：社保和公积金上传区域各自显示 "N 个文件"，底部汇总显示总文件数
- **D-18:** 员工主档默认值：智能切换——服务器有主档数据时默认 `existing`，没有时自动回退到 `none`

### Claude's Discretion
- Python 3.9 Pydantic v2 边界情况的具体修复方式
- 常量合并的具体文件路径和模块命名
- nginx 配置文档的放置位置
- 审计日志 IP 提示的具体 UI 样式

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INFRA-01 | 系统适配 Python 3.9 运行环境（移除 slots=True、确保类型注解兼容、依赖版本锁定） | D-01 ~ D-04：31 处 `slots=True` 需移除，15 个 `__init__.py` 缺少 future annotations（但均无类型注解，安全），依赖版本上界已确认 |
| INFRA-02 | 清理 v1.0 遗留技术债（废弃组件删除、缺失测试补充） | D-09 ~ D-16：8 项技术债全部有明确修复路径 |
| INFRA-03 | 审计日志获取真实客户端 IP 地址 | D-05 ~ D-07：`get_client_ip()` 扩展方案明确，nginx 配置示例需新建 |
| INFRA-04 | 审计日志内容增强（更完整的操作记录和上下文信息） | D-08：前端审计日志页面添加 127.0.0.1 提示 |
| FUSE-02 | 快速融合页面显示已上传文件计数 | D-17：在 `SimpleAggregate.tsx` 的 Dragger 组件下方添加计数文案 |
| FUSE-04 | 员工主档默认选择使用服务器已有主档 | D-18：`employeeMasterMode` 初始值改为依据 `existingEmployeeMasterCount` 动态设置 |
</phase_requirements>

## Standard Stack

### Core (已有，版本锁定)
| Library | Version Constraint | Purpose | Python 3.9 Compatible |
|---------|-------------------|---------|----------------------|
| fastapi | >=0.115.0,<0.130.0 | Web 框架 | 0.130.0 起放弃 3.9 |
| pydantic | >=2.10.3,<2.13.0 | 数据校验 | 3.9 是最低支持版本 |
| pydantic-settings | >=2.6.1,<2.12.0 | 配置管理 | 2.12.0 起放弃 3.9 |
| pandas | >=2.2.3,<3.0.0 | 数据处理 | 3.0.0 起放弃 3.9（需要 3.11+） |
| sqlalchemy | >=2.0.36,<2.1.0 | ORM | 2.1.0 起放弃 3.9 |
| openpyxl | >=3.1.5 | Excel 读写 | 纯 Python，全兼容 |
| uvicorn | >=0.32.0 | ASGI 服务器 | 3.9+ |

### 新增依赖
| Library | Version | Purpose |
|---------|---------|---------|
| xlrd | >=2.0.0 | .xls 旧格式文件支持（已使用但缺失声明） |

### 待移除依赖
| Library | Reason |
|---------|--------|
| psycopg2-binary | 未使用，系统只用 SQLite |
| asyncpg | 未使用，系统只用 SQLite |
| loguru | 未使用，系统使用 stdlib logging |
| python-jose (server.txt) | 未使用，auth 是自定义 HMAC 方案 |
| passlib (server.txt) | 未使用，auth 用 pwdlib |

## Architecture Patterns

### D-01: `slots=True` 移除模式

**发现:** 代码库中共 31 处 `@dataclass(slots=True)`，分布在 13 个文件中。

**修改方式:** 直接移除 `slots=True` 参数，保留 `@dataclass` 或改为 `@dataclass(frozen=True)` 如果原来同时有 `frozen=True`。

```python
# Before (Python 3.10+)
@dataclass(slots=True)
class HeaderMatch:
    field_name: str
    confidence: float

# After (Python 3.9 compatible)
@dataclass
class HeaderMatch:
    field_name: str
    confidence: float
```

**影响文件清单（31 处）:**
- `parsers/header_extraction.py` (3 处)
- `parsers/workbook_discovery.py` (2 处)
- `exporters/export_utils.py` (2 处)
- `validators/non_detail_row_filter.py` (3 处)
- `services/region_detection_service.py` (3 处)
- `services/housing_fund_service.py` (2 处)
- `services/matching_service.py` (1 处)
- `services/header_normalizer.py` (2 处)
- `services/validation_service.py` (2 处)
- `services/employee_service.py` (2 处)
- `services/batch_runtime_service.py` (3 处)
- `services/normalization_service.py` (4 处)
- `services/llm_mapping_service.py` (1 处)
- `services/batch_export_service.py` (1 处)
- `services/compare_service.py` -- 在 CONTEXT 中提到但 grep 未找到，需确认

### D-02: `from __future__ import annotations` 覆盖情况

**发现:** 107 个 Python 文件中 92 个已有该导入。缺失的 15 个全部是 `__init__.py` 文件、`enums.py` 和 `router.py`。

**关键评估:** 这 15 个文件均不包含 `str | Path` 或 `list[str]` 等需要 future annotations 的语法。`enums.py` 只用标准 Enum 继承，`router.py` 只有 import 和 `include_router` 调用，`__init__.py` 文件要么为空要么只有简单 import。

**建议:** 为一致性仍然全部补上，但这不是功能性修复，优先级低于 D-01。

### D-12: REGION_LABELS 合并

**发现:** 4 个文件引用 `REGION_LABELS`：
- `backend/app/services/region_detection_service.py` -- 规范源（line 20）
- `backend/app/services/import_service.py` -- 重复定义
- `backend/app/services/aggregate_service.py` -- 从 region_detection_service 导入
- `backend/app/exporters/export_utils.py` -- 重复定义（实际在 `template_exporter.py`）

**合并方案:** 新建 `backend/app/mappings/regions.py`，将 `REGION_LABELS` 定义在此处，所有文件统一 `from backend.app.mappings.regions import REGION_LABELS`。

### D-13: 文件名工具函数合并

**发现:** `FILENAME_NOISE`、`DATE_PATTERN`、`_infer_company_name_from_filename` 在 `import_service.py` 和 `aggregate_service.py` 中重复。

**合并方案:** 新建 `backend/app/utils/filename_utils.py`，将这三个定义移入，两个 service 统一导入。

### D-14: ID 号正则合并

**发现:** `ID_NUMBER_PATTERN` 和 `NON_MAINLAND_ID_NUMBER_PATTERN` 在 `matching_service.py` 和 `template_exporter.py` 中重复。

**合并方案:** 新建 `backend/app/validators/constants.py` 或放入现有 `backend/app/validators/` 模块中。

### D-15: 废弃组件删除

**发现:** 5 个组件文件确认存在且需删除：
- `frontend/src/components/AppShell.tsx`
- `frontend/src/components/GlobalFeedback.tsx`
- `frontend/src/components/PageContainer.tsx`
- `frontend/src/components/SectionState.tsx`
- `frontend/src/components/SurfaceNotice.tsx`

**关联更新:** `frontend/src/components/index.ts` 当前导出了 `PageContainer`、`SectionState`、`SurfaceNotice`，删除组件后必须同步更新 barrel export。`AppShell` 和 `GlobalFeedback` 未在 barrel export 中但需检查是否有其他文件直接 import。

### D-16: 自助查询端点认证修复

**发现:** `/employees/self-service/query` 端点位于 `employees` router 内。该 router 在 `router.py:43` 通过 `dependencies=[Depends(require_role("admin", "hr"))]` 保护，因此该端点实际上已要求 admin 或 HR 角色才能访问。

**问题本质:** 这不是"缺少认证"的问题，而是端点设计意图不匹配 -- 自助查询应该让员工角色也能使用，但当前 router 级别限制了只有 admin/HR 可访问。

**修复方案:** 给该端点添加显式的 `_user=Depends(require_authenticated_user)` 参数，使其至少在端点级别有认证。考虑到 router 级别的 `require_role` 已经限制了访问，若要让 employee 角色也能调用，需要将此端点移到不同的 router（如 `employee_portal`），或在 router 级别放宽此特定路由。

**建议:** 保持在 employees router 内，但在端点级别添加 `require_authenticated_user` 依赖注入，与其他端点保持一致。router 级别的 `require_role("admin", "hr")` 已提供足够安全性。这样修复了代码一致性问题。

### D-05 ~ D-08: 审计日志 IP 增强

**当前实现 (`request_helpers.py`):**
```python
def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
```

**增强方案:**
```python
def get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For and X-Real-IP headers."""
    settings = get_settings()

    # X-Forwarded-For: client, proxy1, proxy2
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # Take the first IP (client IP)
        ip = forwarded.split(",")[0].strip()
        if settings.trusted_proxies and _is_request_from_trusted_proxy(request, settings):
            return ip
        # If not from trusted proxy, ignore header to prevent spoofing
        # Fall through to X-Real-IP or direct connection

    # X-Real-IP: single IP set by nginx
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    return request.client.host if request.client else "unknown"
```

**Settings 新增字段:**
```python
trusted_proxies: list[str] = Field(default_factory=lambda: ['127.0.0.1', '::1'])
```

**nginx 配置示例文档位置:** `docs/nginx-reverse-proxy.md` (新建 `docs/` 目录)

### D-17: 文件计数显示

**当前状态:** `SimpleAggregate.tsx` 中 `socialFiles` 和 `housingFundFiles` 是 `File[]` 状态，已有 `.length` 可直接用于计数。

**实现位置:** 在每个 `<Dragger>` 组件下方（约 line 423 和 line 445）添加文件计数 `<Text>`，在文件选择卡片底部添加总计。

```tsx
{/* 社保文件计数 */}
{socialDisplayList.length > 0 && (
  <Text type="secondary">{socialDisplayList.length} 个文件</Text>
)}

{/* 底部汇总 */}
<Text type="secondary">
  共 {socialDisplayList.length + housingDisplayList.length} 个文件
  （社保 {socialDisplayList.length} | 公积金 {housingDisplayList.length}）
</Text>
```

### D-18: 员工主档默认值智能切换

**当前状态:** `employeeMasterMode` 初始值为 `'none'`（line 177）。`existingEmployeeMasterCount` 通过 API 异步获取。

**实现方案:** 在获取员工主档数量的 `useEffect` 回调中，根据结果设置默认值：

```tsx
useEffect(() => {
  let active = true;
  setLoadingEmployeeMasters(true);
  fetchEmployeeMasters({ activeOnly: true })
    .then((payload) => {
      if (active) {
        setExistingEmployeeMasterCount(payload.total);
        // D-18: 智能默认值
        if (payload.total > 0) {
          setEmployeeMasterMode('existing');
        }
      }
    })
    .catch(() => { if (active) setExistingEmployeeMasterCount(0); })
    .finally(() => { if (active) setLoadingEmployeeMasters(false); });
  return () => { active = false; };
}, []);
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| IP 地址解析 | 自定义 header 解析 + 信任验证 | 扩展现有 `get_client_ip()` + 配置化 trusted_proxies | 已有基础实现，只需增强 |
| 依赖版本兼容性检查 | 手动追踪每个库的 Python 版本支持 | pip 版本约束 + CI 矩阵 | pip resolver 自动处理 |

## Common Pitfalls

### Pitfall 1: slots=True 移除后的 `__dict__` 行为变化
**What goes wrong:** 移除 `slots=True` 后 dataclass 实例会有 `__dict__` 属性，内存使用略增。如果代码中有检查 `hasattr(obj, '__dict__')` 的逻辑，行为会改变。
**Why it happens:** `slots=True` 阻止 `__dict__` 创建，移除后恢复默认行为。
**How to avoid:** 全局搜索 `__dict__` 和 `__slots__` 引用，确认无代码依赖此行为。
**Warning signs:** 测试中出现 AttributeError 或意外的序列化结果。

### Pitfall 2: requirements 合并时漏掉 server 特有依赖
**What goes wrong:** `requirements.server.txt` 中的 `PyJWT` 和 `pwdlib[bcrypt]` 是服务器实际使用的依赖，与 `python-jose` 和 `passlib` 不同。合并时如果误删有用依赖会导致生产环境崩溃。
**Why it happens:** `requirements.server.txt` 同时包含有用（`PyJWT`、`pwdlib`）和无用（`python-jose`、`passlib`）的依赖。
**How to avoid:** 逐一核对 `requirements.server.txt` 中每个包在代码中的实际使用情况，只移除确认未使用的。
**Warning signs:** import error 在部署时出现。

### Pitfall 3: barrel export 更新遗漏
**What goes wrong:** 删除组件文件后忘记更新 `frontend/src/components/index.ts`，导致构建失败。
**Why it happens:** barrel export 中的 re-export 指向已删除文件。
**How to avoid:** 删除组件后立即更新 index.ts，并运行 `npm run build` 验证。
**Warning signs:** TypeScript 编译错误 "Module not found"。

### Pitfall 4: trusted_proxies 配置默认值不当
**What goes wrong:** 如果 `trusted_proxies` 默认为空列表，现有的反向代理部署会突然忽略 `X-Forwarded-For`，导致 IP 全变成代理 IP。
**Why it happens:** 安全加固过度，破坏了向后兼容性。
**How to avoid:** 默认包含 `['127.0.0.1', '::1']` 作为常见本地代理地址。
**Warning signs:** 审计日志中 IP 地址突然变化。

### Pitfall 5: 前端 employeeMasterMode 默认值竞态
**What goes wrong:** 如果 API 请求慢，用户可能在默认值设置前就手动选择了模式，然后 API 回调覆盖了用户选择。
**Why it happens:** `setEmployeeMasterMode('existing')` 在异步回调中执行，可能覆盖用户已做的手动选择。
**How to avoid:** 添加一个 ref 标记用户是否已手动操作，如果已手动操作则跳过自动设置。
**Warning signs:** 用户选择被重置。

### Pitfall 6: `from __future__ import annotations` 与 Pydantic v2 的交互
**What goes wrong:** Pydantic v2 在某些边界情况下对 `from __future__ import annotations` 的处理可能有 bug，特别是在 `model_validator` 和 `computed_field` 中。
**Why it happens:** Pydantic v2 需要在运行时 evaluate 字符串化的注解，某些复杂类型可能解析失败。
**How to avoid:** 当前代码已经在使用 `from __future__ import annotations` + Pydantic v2，且运行正常。只需确保新增的 `__init__.py` 文件不会引入问题（这些文件几乎没有类型注解）。
**Warning signs:** `PydanticUserError` 在模型初始化时。

## Code Examples

### IP 解析增强（D-05, D-06）
```python
# backend/app/utils/request_helpers.py
from __future__ import annotations

from fastapi import Request


def get_client_ip(request: Request, trusted_proxies: list[str] | None = None) -> str:
    """Extract client IP from request, respecting reverse proxy headers.
    
    Priority: X-Forwarded-For (first IP) > X-Real-IP > direct connection.
    Only trusts proxy headers if the direct connection is from a trusted proxy.
    """
    direct_ip = request.client.host if request.client else "unknown"
    
    # If no trusted proxies configured, trust all proxy headers (backward compat)
    trust_headers = trusted_proxies is None or direct_ip in (trusted_proxies or [])
    
    if trust_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
    
    return direct_ip
```

### nginx 反向代理配置示例（D-07）
```nginx
# /etc/nginx/conf.d/social-security-tool.conf
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### dataclass slots 移除（D-01）
```python
# Before
@dataclass(slots=True)
class HeaderMatch:
    field_name: str
    confidence: float

# After
@dataclass
class HeaderMatch:
    field_name: str
    confidence: float
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| FastAPI 全版本支持 3.9 | FastAPI 0.130.0 放弃 3.9 | 2026-02 | 必须锁定 <0.130.0 |
| pandas 全版本支持 3.9 | pandas 3.0.0 要求 3.11+ | 2026-01 | 必须锁定 <3.0.0 |
| pydantic-settings 支持 3.9 | 2.12.0 放弃 3.9 | 2026 | 必须锁定 <2.12.0 |
| SQLAlchemy 2.0 支持 3.9 | 2.1.0 要求 3.10+ | 2026 | 必须锁定 <2.1.0 |

## Open Questions

1. **`compare_service.py` 中的 `slots=True`**
   - What we know: CONTEXT.md 列出了该文件，但 grep 未找到匹配
   - What's unclear: 可能已在之前的修改中移除，或 CONTEXT 信息有误
   - Recommendation: 实现时再次确认，如果已无 `slots=True` 则跳过

2. **Python 3.9 CI 测试**
   - What we know: 开发机是 Python 3.14，无 pyenv/conda 可切换到 3.9
   - What's unclear: 是否需要在本地验证 3.9 兼容性
   - Recommendation: 依赖静态分析（grep slots=True, grep X|Y runtime usage）+ 依赖版本锁定，部署到服务器时做最终验证

3. **`requirements.server.txt` 合并还是保留**
   - What we know: D-10 说"考虑合并为单一 requirements 文件"
   - What's unclear: server.txt 中 `PyJWT` 和 `pwdlib[bcrypt]` 是否在主 requirements.txt 中已有
   - Recommendation: 检查两文件差异，将 server 独有但实际使用的依赖合并到主文件，删除 server 文件

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 |
| Config file | 无独立 pytest.ini（使用默认配置） |
| Quick run command | `pytest backend/tests/ -x -q` |
| Full suite command | `pytest backend/tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFRA-01 | slots=True 全部移除后不报错 | integration | `pytest backend/tests/ -x -q` | 现有测试覆盖 |
| INFRA-01 | 依赖版本约束正确 | manual | 检查 requirements.txt 内容 | N/A |
| INFRA-02 | 废弃组件删除后前端构建成功 | build | `cd frontend && npm run build` | N/A |
| INFRA-02 | xlrd 依赖声明 | unit | `python -c "import xlrd"` | N/A |
| INFRA-03 | X-Forwarded-For 解析正确 | unit | `pytest backend/tests/test_audit.py -x` | 需补充 |
| INFRA-03 | X-Real-IP 解析正确 | unit | `pytest backend/tests/test_audit.py -x` | 需新增 |
| INFRA-03 | trusted proxy 验证 | unit | `pytest backend/tests/test_audit.py -x` | 需新增 |
| INFRA-04 | 127.0.0.1 提示显示 | manual | 前端审计日志页面检查 | N/A |
| FUSE-02 | 文件计数显示 | manual | 前端页面检查 | N/A |
| FUSE-04 | 主档默认值智能切换 | manual | 前端页面检查 | N/A |

### Sampling Rate
- **Per task commit:** `pytest backend/tests/ -x -q` + `cd frontend && npm run build`
- **Per wave merge:** `pytest backend/tests/ -v` + `cd frontend && npm run build`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_request_helpers.py` -- 覆盖 `get_client_ip()` 增强逻辑（X-Real-IP、trusted proxies）
- [ ] 前端 build 验证 -- 废弃组件删除后的编译检查

## Project Constraints (from CLAUDE.md)

以下规则直接影响本阶段实施：

1. **Data pipeline first** -- 本阶段不涉及数据管线修改，但常量合并（D-12~D-14）必须确保不破坏现有管线
2. **Rules before LLM** -- 不适用于本阶段
3. **No fixed-position parsing** -- 不适用于本阶段
4. **Keep provenance** -- 常量合并时不能丢失原始追溯能力
5. **Export both templates** -- 常量合并后必须验证双模板导出仍正常
6. **Testing Requirements:**
   - 涉及导入、识别、映射的修改必须用 2+ 地区样例验证（D-12~D-14 常量合并涉及导入和导出）
   - lint 通过 + build 成功

## Sources

### Primary (HIGH confidence)
- 代码库直接检查: `@dataclass(slots=True)` grep 结果（31 处）
- 代码库直接检查: `from __future__ import annotations` 覆盖率（92/107）
- 代码库直接检查: 废弃组件文件存在性确认
- 代码库直接检查: `REGION_LABELS` / `FILENAME_NOISE` / `ID_NUMBER_PATTERN` 重复位置
- [PyPI - pandas 2.2.3](https://pypi.org/project/pandas/2.2.3/) - Python 3.9 支持确认
- [PyPI - pydantic-settings](https://pypi.org/project/pydantic-settings/) - 版本兼容性
- [FastAPI Release Notes](https://fastapi.tiangolo.com/release-notes/) - 0.130.0 放弃 3.9

### Secondary (MEDIUM confidence)
- [Pydantic Docs](https://docs.pydantic.dev/latest/install/) - Python 3.9 最低支持
- [SQLAlchemy Download](https://www.sqlalchemy.org/download.html) - 2.1.0 放弃 3.9

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - 所有依赖版本兼容性均经 PyPI 和官方文档确认
- Architecture: HIGH - 所有修改点已通过代码库 grep 精确定位
- Pitfalls: HIGH - 基于对代码库的直接分析，非理论推测

**Research date:** 2026-04-04
**Valid until:** 2026-05-04 (稳定的基础设施修改，无快速变化的外部依赖)
