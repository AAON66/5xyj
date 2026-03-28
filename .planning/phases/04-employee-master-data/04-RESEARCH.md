# Phase 4: Employee Master Data - Research

**Researched:** 2026-03-28
**Domain:** 员工主数据管理（模型扩展、批量导入、匹配策略、前端筛选）
**Confidence:** HIGH

## Summary

本阶段是一个增量改进阶段，绝大多数基础设施已经到位。后端 `employee_service.py`（683 行）已实现完整的 CRUD、批量导入、搜索功能；`matching_service.py` 已有基于 `id_number` 的匹配逻辑；前端 `Employees.tsx` 已有列表、分页、编辑、审计面板。

核心改动范围集中在四个方面：(1) EmployeeMaster 模型新增 `region` 字段 + Alembic 迁移；(2) 批量导入调整为失败行跳过而非中断 + 返回错误明细；(3) matching_service 新增 `employee_id` 维度匹配实现双维度并行；(4) 前端添加 region/company 下拉筛选。

**Primary recommendation:** 按"模型迁移 -> 后端服务调整 -> 匹配策略扩展 -> 前端完善"顺序实施，每一步都是对现有代码的小幅扩展，不需要引入新库。

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** EmployeeMaster 模型新增 `region` 字段（String，可选）
- **D-02:** region 值从固定选项列表中选择：广州、杭州、厦门、深圳、武汉、长沙（与当前已支持的 6 个地区一致）
- **D-03:** 新增地区需后台配置，前端从 API 获取可用地区列表
- **D-04:** 批量导入时 Excel 中的 region 列映射到此字段，未填写时设为 null
- **D-05:** 工号重复时覆盖更新（用新数据覆盖已有记录），不跳过也不报错
- **D-06:** 批量导入完成后前端显示统计：新增数 / 更新数 / 失败数 / 总行数
- **D-07:** 失败行（如缺少必填字段）跳过并汇总展示，不中断整个导入流程
- **D-08:** 社保数据与员工主数据采用双维度并行匹配：工号(employee_id) 和 身份证号(id_number) 任一命中即为匹配成功
- **D-09:** 未匹配的社保记录正常导入，标记为"未匹配"状态，HR 可后续手动处理
- **D-10:** 匹配结果需可追溯（记录匹配方式：工号匹配 / 身份证号匹配 / 未匹配）
- **D-11:** 员工列表页添加按地区(region)下拉筛选
- **D-12:** 员工列表页添加按公司(company_name)下拉筛选
- **D-13:** 员工列表页添加分页功能（服务端分页）
- **D-14:** 批量导入后展示导入结果反馈（新增/更新/失败统计）

### Claude's Discretion
- region 字段的数据库迁移方式
- 前端筛选组件的具体样式和布局
- 导入结果反馈的 UI 形式（弹窗 / 内嵌 / toast）
- 匹配结果记录的数据模型细节

### Deferred Ideas (OUT OF SCOPE)
None -- 讨论内容全部在 Phase 4 范围内。
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MASTER-01 | HR 可维护员工主数据（姓名/工号/身份证号/所属公司/地区） | 模型已有除 region 外所有字段；需新增 region 字段 + 迁移 + schema 同步 + 创建/编辑表单同步 |
| MASTER-02 | HR 可批量导入员工主数据 | 导入功能已实现（upsert 覆盖模式已有）；需调整失败行跳过逻辑 + region 列映射 + 错误明细返回 |
| MASTER-03 | 员工主数据支持搜索和筛选 | 搜索已实现（ilike 多字段）；分页已实现（服务端）；需新增 region/company_name 下拉筛选参数 |
| MASTER-04 | 导入的社保数据自动与员工主数据匹配 | matching_service 已有 id_number 匹配；需新增 employee_id 维度 + 匹配方式追溯 |
</phase_requirements>

## Standard Stack

### Core（已有，无需新增）
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy | 2.x | ORM + 模型定义 | 项目已使用 |
| Alembic | 1.14.0 | 数据库迁移 | 项目已使用，5 个迁移文件 |
| Pydantic | 2.x | Schema 校验 | FastAPI 标配 |
| pandas | - | Excel 解析 | 导入逻辑已用 |
| openpyxl | - | Excel 读写 | 项目已使用 |
| React | - | 前端框架 | 项目已使用 |
| axios | - | HTTP 客户端 | apiClient 已封装 |

### Alternatives Considered
无。本阶段不需要引入任何新库。

## Architecture Patterns

### 现有代码结构（复用）
```
backend/app/
├── models/employee_master.py       # 模型：新增 region 字段
├── schemas/employees.py            # Schema：同步 region
├── services/employee_service.py    # 服务：调整导入 + 筛选
├── services/matching_service.py    # 匹配：新增 employee_id 维度
├── api/v1/employees.py             # 端点：新增筛选参数
backend/alembic/versions/           # 迁移：新增 0006

frontend/src/
├── pages/Employees.tsx             # 列表页：添加筛选下拉
├── pages/EmployeeCreate.tsx        # 创建页：添加 region 字段
├── services/employees.ts           # API 服务：同步接口类型
```

### Pattern 1: 模型字段扩展（Alembic 迁移）
**What:** 通过 Alembic 迁移脚本为 employee_master 表添加 region 列
**When to use:** 任何模型新增字段
**Example:**
```python
# backend/alembic/versions/20260328_0006_add_employee_region.py
# 遵循现有命名规则：日期_序号_描述.py

def upgrade() -> None:
    op.add_column("employee_master", sa.Column("region", sa.String(50), nullable=True, index=True))

def downgrade() -> None:
    op.drop_column("employee_master", "region")
```

### Pattern 2: 批量导入容错（失败行跳过）
**What:** 当前 `_parse_employee_row` 对缺少必填字段的行抛出 `EmployeeImportError` 导致整个导入中断。需要改为收集错误、跳过失败行、继续处理后续行。
**When to use:** D-07 要求失败行不中断导入
**Example:**
```python
# 当前代码（会中断）:
if not employee_id or not person_name:
    raise EmployeeImportError(f"Employee master row {row_number} is missing employee_id or person_name.")

# 改为（跳过 + 收集）:
errors: list[str] = []
if not employee_id or not person_name:
    errors.append(f"第 {row_number} 行缺少工号或姓名，已跳过。")
    continue  # 跳过该行
```

### Pattern 3: 双维度匹配扩展
**What:** 在 matching_service._match_preview_record 中，id_number 匹配之前增加 employee_id 精确匹配
**When to use:** D-08 双维度并行匹配
**Example:**
```python
def _match_preview_record(record, employees):
    values = record.values
    record_employee_id = _normalize(values.get('employee_id'))
    id_number = _normalize_id_number(values.get('id_number'))

    # 维度1: employee_id 精确匹配
    if record_employee_id:
        eid_matches = [e for e in employees if e.employee_id == record_employee_id]
        result = _resolve_candidates(..., match_basis='employee_id_exact', confidence=1.0)
        if result:
            return result

    # 维度2: id_number 精确匹配（现有逻辑保留）
    if id_number:
        ...
```

### Pattern 4: 服务端筛选参数扩展
**What:** list_employee_masters 函数和 API 端点添加 region/company_name 可选参数
**When to use:** D-11, D-12 下拉筛选
**Example:**
```python
def list_employee_masters(
    db: Session,
    *,
    query: Optional[str] = None,
    region: Optional[str] = None,        # 新增
    company_name: Optional[str] = None,  # 新增
    active_only: bool = False,
    limit: Optional[int] = None,
    offset: int = 0,
) -> EmployeeMasterListRead:
    statement = db.query(EmployeeMaster)
    if region:
        statement = statement.filter(EmployeeMaster.region == region)
    if company_name:
        statement = statement.filter(EmployeeMaster.company_name == company_name)
    ...
```

### Pattern 5: 地区列表 API
**What:** 新增一个端点返回可用地区列表，前端从此 API 获取（D-03）
**When to use:** 前端下拉选项需要与后端保持一致
**Example:**
```python
# 可以是简单的配置常量 + 端点
SUPPORTED_REGIONS = ["广州", "杭州", "厦门", "深圳", "武汉", "长沙"]

@router.get('/regions')
def list_regions():
    return success_response(SUPPORTED_REGIONS)
```

### Anti-Patterns to Avoid
- **硬编码地区到前端:** 违反 D-03，地区列表必须从 API 获取
- **导入失败中断整批:** 违反 D-07，必须跳过失败行继续处理
- **只做 id_number 匹配:** 违反 D-08，必须同时支持 employee_id 维度

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 数据库迁移 | 手动 ALTER TABLE | Alembic migration | 项目已有 5 个迁移，保持一致 |
| Excel 解析 | 自己读单元格 | pandas + openpyxl (已有) | employee_service 已封装完整解析链 |
| API 响应封装 | 自定义 JSON 格式 | success_response() (已有) | 全项目统一模式 |

## Common Pitfalls

### Pitfall 1: 迁移后 audit snapshot 缺少 region
**What goes wrong:** `_build_audit` 中的 snapshot 字典没有包含 region 字段，导致审计记录丢失地区信息
**Why it happens:** snapshot 是手动构建的 dict，不会自动包含新字段
**How to avoid:** 在 `_build_audit` 函数中的 snapshot dict 添加 `"region": employee.region`
**Warning signs:** 审计记录的 snapshot 中没有 region 字段

### Pitfall 2: 导入 region 列别名未注册
**What goes wrong:** Excel 中的地区列无法被识别
**Why it happens:** HEADER_ALIASES 字典中没有 region 的条目
**How to avoid:** 在 HEADER_ALIASES 添加 `"region": {"region", "地区", "所属地区", "城市", ...}`
**Warning signs:** 导入后所有记录的 region 都是 null

### Pitfall 3: 匹配顺序导致 employee_id 匹配被跳过
**What goes wrong:** 如果 id_number 匹配先执行且成功，employee_id 匹配永远不会触发
**Why it happens:** 匹配函数是顺序执行、首个命中即返回的
**How to avoid:** D-08 说"任一命中即为匹配成功"，所以顺序无所谓，但 employee_id 应放在前面（工号匹配更直接可靠）。如果两个维度匹配到不同人，以 employee_id 为准。
**Warning signs:** match_basis 记录中从未出现 `employee_id_exact`

### Pitfall 4: EmployeeMasterRead schema 忘记同步 region
**What goes wrong:** API 返回的 employee 数据中没有 region 字段
**Why it happens:** Pydantic schema 和 _to_employee_read 转换函数没有更新
**How to avoid:** 同步更新 EmployeeMasterRead、EmployeeMasterCreateInput、EmployeeMasterUpdateInput、_to_employee_read、EmployeeImportRead items
**Warning signs:** 前端收到的员工数据中没有 region 字段

### Pitfall 5: 前端 company_name 筛选值来源
**What goes wrong:** 下拉选项列表为空或不准确
**Why it happens:** company_name 没有固定列表，需要从实际数据中聚合
**How to avoid:** 新增一个端点 `GET /employees/companies` 返回去重后的公司名列表（`SELECT DISTINCT company_name FROM employee_master WHERE company_name IS NOT NULL`）
**Warning signs:** 公司筛选下拉无选项

### Pitfall 6: 分页已实现但前端已有
**What goes wrong:** 重复实现分页逻辑
**Why it happens:** 没有仔细检查现有代码
**How to avoid:** 后端 list_employee_masters 已支持 limit/offset 服务端分页，前端 Employees.tsx 已有 pageIndex/pageSize/pagination UI。D-13 实际上已完成，只需确认前端筛选参数与新增筛选联动即可。
**Warning signs:** 新建多余的分页组件

## Code Examples

### 现有批量导入 upsert 逻辑（已实现 D-05）
```python
# employee_service.py L121-144 -- 工号重复时覆盖更新已经实现
existing = existing_records.get(row.employee_id)
if existing is None:
    # 新增
    ...
    created_count += 1
else:
    # 覆盖更新
    existing.person_name = row.person_name
    existing.id_number = row.id_number
    ...
    updated_count += 1
```

### 现有匹配策略（仅 id_number，需扩展）
```python
# matching_service.py L89-145 -- 当前匹配顺序：
# 1. id_number 精确 (confidence=1.0)
# 2. person_name + company_name (confidence=0.9, 仅在无 id_number 时)
# 3. person_name (confidence=0.6, 仅在无 id_number 时)
# 缺失: employee_id 精确匹配（D-08 要求）
```

### 现有分页实现（D-13 已基本完成）
```python
# employee_service.py L195-228 -- 后端分页已实现
if offset > 0:
    statement = statement.offset(offset)
if limit is not None:
    statement = statement.limit(limit)
```
```tsx
// Employees.tsx L87-89 -- 前端分页 UI 已实现
const [pageSize, setPageSize] = useState<number>(10);
const [pageIndex, setPageIndex] = useState(0);
// 分页按钮和页码展示在 L539-567
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 导入失败行抛异常中断 | 跳过失败行继续导入 | Phase 4 (本阶段) | D-07 要求 |
| 仅 id_number 匹配 | employee_id + id_number 双维度 | Phase 4 (本阶段) | D-08 要求 |

## Existing Code Gap Analysis

以下是对现有代码与 Phase 4 需求之间差距的精确分析：

### 已完成（无需改动或仅需微调）
| Feature | Status | Evidence |
|---------|--------|----------|
| CRUD 增删改查 | 已完成 | employee_service.py 完整实现 |
| Upsert 覆盖导入 (D-05) | 已完成 | L121-144 已有 upsert 逻辑 |
| 服务端分页 (D-13) | 已完成 | list_employee_masters 支持 limit/offset |
| 前端分页 UI (D-13) | 已完成 | Employees.tsx L539-567 |
| 导入结果统计返回 (D-06) | 已完成 | EmployeeImportRead schema 包含 created/updated/skipped/errors |
| 前端导入结果展示 (D-14) | 基本完成 | Employees.tsx L396-402 展示 importResult |
| 匹配结果追溯 (D-10) | 部分完成 | MatchResult.match_basis 已记录匹配方式 |

### 需新增或修改
| Feature | Gap | Effort |
|---------|-----|--------|
| region 字段 (D-01) | 模型/schema/服务/API/迁移/前端全链路 | 中 |
| region 导入映射 (D-04) | HEADER_ALIASES 缺少 region 条目 | 小 |
| 失败行跳过 (D-07) | _parse_employee_row 抛异常需改为收集 | 小 |
| employee_id 匹配 (D-08) | matching_service 缺少此维度 | 小 |
| region 筛选 (D-11) | API + 前端下拉 | 小 |
| company 筛选 (D-12) | API + 前端下拉 | 小 |
| 地区列表 API (D-03) | 不存在，需新建端点 | 小 |
| 公司列表 API (D-12) | 不存在，需新建端点 | 小 |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | backend/pytest.ini 或 pyproject.toml |
| Quick run command | `pytest backend/tests/test_employee_master_api.py -x` |
| Full suite command | `pytest backend/tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MASTER-01 | 创建/编辑员工含 region 字段 | unit | `pytest backend/tests/test_employee_master_api.py -x -k "region"` | 需扩展 |
| MASTER-02 | 批量导入含 region + 失败行跳过 | unit | `pytest backend/tests/test_employee_master_api.py -x -k "import"` | 需扩展 |
| MASTER-03 | 按 region/company 筛选 + 分页 | unit | `pytest backend/tests/test_employee_master_api.py -x -k "filter or list"` | 需扩展 |
| MASTER-04 | 双维度匹配 (employee_id + id_number) | unit | `pytest backend/tests/test_matching_service.py -x -k "employee_id"` | 需扩展 |

### Sampling Rate
- **Per task commit:** `pytest backend/tests/test_employee_master_api.py backend/tests/test_matching_service.py -x`
- **Per wave merge:** `pytest backend/tests/ -x`
- **Phase gate:** Full suite green + `npm run build` + `npm run lint`

### Wave 0 Gaps
- [ ] `backend/tests/test_employee_master_api.py` -- 需新增 region CRUD 测试、失败行跳过测试、筛选测试
- [ ] `backend/tests/test_matching_service.py` -- 需新增 employee_id 维度匹配测试

## Sources

### Primary (HIGH confidence)
- 项目源码直接审查：employee_service.py, matching_service.py, Employees.tsx, employees.ts
- 现有 Alembic 迁移文件（5 个迁移，命名和结构清晰）
- 现有 test 文件（test_employee_master_api.py, test_matching_service.py）

### Secondary (MEDIUM confidence)
- 无需外部资料，所有改动基于现有代码模式的增量扩展

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- 不引入新库，全部复用现有依赖
- Architecture: HIGH -- 所有模式直接从现有代码中提取
- Pitfalls: HIGH -- 基于代码审查发现的具体问题点

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable, code-based findings)
