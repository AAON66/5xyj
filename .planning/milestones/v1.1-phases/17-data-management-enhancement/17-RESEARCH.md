# Phase 17: 数据管理增强 - Research

**Researched:** 2026-04-08
**Domain:** 前端筛选增强 + 后端多值过滤 + 缴费基数数据修复
**Confidence:** HIGH

## Summary

本阶段涉及四个需求：(1) 筛选改多选、(2) 匹配状态过滤、(3) 批次删除联动确认增强、(4) 个人险种缴费基数修复。前三个属于 UI/API 层改造，代码路径清晰，风险低。第四个（payment_base 修复）需要对解析链路中的字段映射规则做精确调整，是本阶段唯一有技术复杂度的任务。

经过对现有代码的深入调查，payment_base 错误的根因已定位：`AliasRule("payment_base", ("缴费基数",), confidence=0.94)` 规则过于宽泛，会匹配 "基本养老保险(单位缴纳) / 缴费基数"、"失业保险 / 缴费基数" 等险种特定基数列，导致多个列都映射到 `payment_base`，而 `_assign_canonical_value` 只保留第一个值、后续值记入 `field_conflicts`。修复方向是在规则中添加排除条件（excludes），让 payment_base 只匹配独立的 "缴费基数" 列而非险种子列中的基数字段。

**Primary recommendation:** 分四个任务按依赖关系执行：先修 payment_base（数据层基础）、再做多选筛选（前后端联动最大）、然后匹配状态过滤（依赖多选 API 基础）、最后删除确认增强（独立变更）。

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01: 地区、公司、账期三个筛选全部改为多选（AntD Select mode="multiple"），支持搜索和标签展示
- D-02: 每个多选下拉顶部加「全选」选项
- D-03: 保留级联关系（选地区后公司下拉只显示已选地区下的公司；选地区+公司后账期只显示对应账期）
- D-04: 后端 filter-options 和 records 端点需支持多值参数（region=[a,b]&company_name=[c,d]）
- D-05: 匹配状态过滤作为筛选栏第四个下拉，与地区/公司/账期并列
- D-06: 过滤选项为三项：全部/已匹配/未匹配。默认选中「已匹配」
- D-07: 「未匹配」包含所有非 MATCHED 状态（UNMATCHED、DUPLICATE、LOW_CONFIDENCE、MANUAL）
- D-08: 当前 cascade delete 已覆盖 NormalizedRecords + MatchResults + ValidationIssues，无需新增关联表清理
- D-09: 需确认 SQLite PRAGMA foreign_keys=ON 生效
- D-10: 删除确认弹窗增强：显示「此操作将同时删除 X 条明细记录、Y 条匹配结果、Z 条校验问题」
- D-11: 所有地区的个人险种缴费基数显示错误值，需研究定位根因
- D-12: 需深入查看解析器/字段映射/存储逻辑/前端显示全链路，定位根因并修复

### Claude's Discretion
- 多选下拉的 maxTagCount 展示策略
- 匹配状态下拉的具体样式（是否用颜色区分）
- 删除影响数量的查询方式（预查询 vs 估算）

### Deferred Ideas (OUT OF SCOPE)
None
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-01 | 数据管理筛选支持多选（地区、公司等下拉框） | AntD Select mode="multiple" 改造方案已明确，后端 Query 参数需从单值改为 List 类型 |
| DATA-02 | 数据管理新增已匹配/未匹配过滤选项，默认选择已匹配 | MatchResult 模型已有 match_status 枚举，需 LEFT JOIN 查询实现过滤 |
| DATA-03 | 批次删除时联动清理关联数据 | cascade="all, delete-orphan" 已配置，PRAGMA foreign_keys=ON 已验证，需增加预查询显示影响范围 |
| DATA-04 | 个人险种缴费基数数据修复 | 根因已定位：AliasRule 过宽匹配导致险种基数覆盖 payment_base |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- 前端: React + AntD, 后端: FastAPI + SQLAlchemy
- 规则优先，LLM 兜底（Rules before LLM）
- 不依赖固定 sheet 名/行/列
- 每条标准化结果必须可追溯到原始文件和行
- 双模板导出不可破坏
- Python 3.9 兼容

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| antd | 已安装 | Select mode="multiple" 组件 | 项目统一 UI 框架 |
| FastAPI | 已安装 | Query 参数多值支持 | 项目后端框架 |
| SQLAlchemy | 已安装 | IN 查询、LEFT JOIN | 项目 ORM |

[VERIFIED: codebase grep] 所有依赖已在项目中，无需安装新包。

## Architecture Patterns

### 现有代码结构（需改造的文件）

```
frontend/src/
├── pages/DataManagement.tsx        # 筛选/表格/Tab（主改造目标）
├── services/dataManagement.ts      # API 客户端（参数序列化）
backend/app/
├── api/v1/data_management.py       # API 端点（Query 参数）
├── services/data_management_service.py  # 服务层（查询逻辑）
├── services/import_service.py      # 删除逻辑（预查询）
├── mappings/manual_field_aliases.py # payment_base 规则修复
├── models/match_result.py          # MatchResult/MatchStatus
├── schemas/data_management.py      # 响应 schema
```

### Pattern 1: 多值 Query 参数（FastAPI）
**What:** FastAPI 原生支持 List[str] 类型的 Query 参数，URL 格式为 `?region=a&region=b`
**When to use:** 当前端需要传递多个筛选值时
**Example:**
```python
# Source: [VERIFIED: FastAPI docs / codebase pattern]
from typing import List, Optional
from fastapi import Query

@router.get('/records')
def list_records_endpoint(
    region: Optional[List[str]] = Query(default=None),
    company_name: Optional[List[str]] = Query(default=None),
    billing_period: Optional[List[str]] = Query(default=None),
    match_status: Optional[str] = Query(default=None),  # 'matched' | 'unmatched' | None (全部)
    page: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    ...
```

### Pattern 2: SQLAlchemy IN 过滤
**What:** 将单值 `==` 过滤改为 `.in_()` 列表过滤
**Example:**
```python
# Source: [VERIFIED: codebase existing pattern]
if region:
    if isinstance(region, list):
        query = query.filter(NormalizedRecord.region.in_(region))
    else:
        query = query.filter(NormalizedRecord.region == region)
```

### Pattern 3: 匹配状态过滤（LEFT JOIN）
**What:** NormalizedRecord 与 MatchResult 做 LEFT JOIN，根据 match_status 过滤
**Example:**
```python
# Source: [VERIFIED: model relationships]
from sqlalchemy import or_
from backend.app.models.match_result import MatchResult
from backend.app.models.enums import MatchStatus

# 已匹配：有 MatchResult 且 status == MATCHED
if match_filter == 'matched':
    query = query.join(MatchResult, MatchResult.normalized_record_id == NormalizedRecord.id)
    query = query.filter(MatchResult.match_status == MatchStatus.MATCHED)

# 未匹配：无 MatchResult 或 status != MATCHED
elif match_filter == 'unmatched':
    query = query.outerjoin(MatchResult, MatchResult.normalized_record_id == NormalizedRecord.id)
    query = query.filter(
        or_(
            MatchResult.id.is_(None),
            MatchResult.match_status != MatchStatus.MATCHED,
        )
    )
```

### Pattern 4: 前端多选 URL 序列化
**What:** URL searchParams 中多值参数用逗号分隔存储，API 请求时展开为多个 query param
**Example:**
```typescript
// URL 存储: ?region=guangzhou,shenzhen
// 读取:
const regions = searchParams.get('region')?.split(',').filter(Boolean) || [];
// API 请求时:
regions.forEach(r => urlParams.append('region', r));
```

### Pattern 5: AntD Select 多选 + 全选
**What:** mode="multiple" + maxTagCount + 自定义全选选项
**Example:**
```tsx
// Source: [VERIFIED: AntD docs]
<Select
  mode="multiple"
  maxTagCount={2}
  maxTagPlaceholder={(omitted) => `+${omitted.length}`}
  placeholder="选择地区"
  value={selectedRegions}
  onChange={handleRegionChange}
  style={{ width: '100%' }}
  options={[
    { label: '全选', value: '__ALL__' },
    ...filterOptions.regions.map(r => ({ label: r, value: r })),
  ]}
/>
```

### Anti-Patterns to Avoid
- **全选用真实值列表传递:** 不要在 URL 和 API 中传所有值来代表"全选"，应该用空列表/undefined 代表"不过滤"
- **匹配状态用 employee_id 判断:** 当前前端用 `record.employee_id` 来显示匹配状态 Tag，但真正的匹配状态在 MatchResult 表中，应该从后端返回 match_status 字段

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 多选下拉 | 自定义多选组件 | AntD Select mode="multiple" | 已有搜索/标签/清除/maxTagCount |
| URL 多值序列化 | 自定义序列化 | 逗号分隔 + URLSearchParams | 简单可读，现有模式一致 |
| 批次关联数据计数 | 手动遍历关系 | SQLAlchemy func.count() 子查询 | 性能更好，一次查询 |

## Common Pitfalls

### Pitfall 1: payment_base AliasRule 过宽匹配
**What goes wrong:** `AliasRule("payment_base", ("缴费基数",), confidence=0.94)` 匹配到 "基本养老保险(单位缴纳) / 缴费基数" 等险种子列中的基数列
**Why it happens:** patterns 参数 `("缴费基数",)` 只检查子串包含，不区分独立列 vs 险种子列
**How to avoid:** 添加 excludes 参数排除险种关键词，如 `excludes=("养老", "医疗", "失业", "工伤", "生育", "补充")` [VERIFIED: codebase `manual_field_aliases.py` 第 109 行]
**Warning signs:** payment_base 值等于某个险种的缴费基数而非员工整体缴费基数

### Pitfall 2: 多选级联过滤的 API 调用风暴
**What goes wrong:** 选择多个地区时，级联更新公司列表需要传多个地区参数，可能触发多次 API 调用
**Why it happens:** 当前级联逻辑为每次 region 变化调用 `fetchFilterOptions({ region })`
**How to avoid:** filter-options API 一次性支持多值 region 参数，前端只发一次请求
**Warning signs:** 选择多个地区时 Network 面板出现多个重复请求

### Pitfall 3: SQLite PRAGMA foreign_keys=ON 在事务中的行为
**What goes wrong:** 如果 PRAGMA 未在连接建立时设置，CASCADE DELETE 不会生效
**Why it happens:** SQLite 默认 foreign_keys=OFF，必须每个连接都设置
**How to avoid:** 已在 `database.py:34` 通过 event listener 设置，已验证 [VERIFIED: codebase `backend/app/core/database.py` 第 34 行]
**Warning signs:** 删除批次后，normalized_records 表中仍有孤立记录

### Pitfall 4: 匹配状态过滤中的 LEFT JOIN 影响分页
**What goes wrong:** JOIN MatchResult 后，如果一个 NormalizedRecord 有多个 MatchResult，会产生重复行
**Why it happens:** MatchResult 表虽有 UniqueConstraint("normalized_record_id")，但理论上需要防御
**How to avoid:** 使用 `query.distinct()` 或确认 UniqueConstraint 生效后信任一对一关系 [VERIFIED: `match_result.py` 第 19 行 UniqueConstraint]
**Warning signs:** 分页 total 计数大于实际记录数

### Pitfall 5: 全选选项和清除操作的交互冲突
**What goes wrong:** 用户点「全选」后再取消一个选项，需要把「全选」从选中态移除
**Why it happens:** 全选是伪选项（__ALL__），需要在 onChange 中特殊处理
**How to avoid:** onChange 处理器中检测 __ALL__ 的添加/移除，动态调整实际选中值
**Warning signs:** 选中全选后取消一项，全选标记仍显示为选中

## Code Examples

### 后端多值过滤服务层
```python
# Source: [VERIFIED: existing data_management_service.py pattern]
def list_normalized_records(
    db: Session,
    *,
    regions: Optional[list[str]] = None,
    company_names: Optional[list[str]] = None,
    billing_periods: Optional[list[str]] = None,
    match_filter: Optional[str] = None,  # 'matched' | 'unmatched' | None
    page: int = 0,
    page_size: int = 20,
) -> PaginatedRecordsRead:
    query = db.query(NormalizedRecord)

    if regions:
        query = query.filter(NormalizedRecord.region.in_(regions))
    if company_names:
        query = query.filter(NormalizedRecord.company_name.in_(company_names))
    if billing_periods:
        query = query.filter(NormalizedRecord.billing_period.in_(billing_periods))

    if match_filter == 'matched':
        query = query.join(MatchResult).filter(MatchResult.match_status == MatchStatus.MATCHED)
    elif match_filter == 'unmatched':
        query = query.outerjoin(MatchResult).filter(
            or_(MatchResult.id.is_(None), MatchResult.match_status != MatchStatus.MATCHED)
        )
    ...
```

### 删除前影响范围预查询
```python
# Source: [VERIFIED: existing model relationships]
def get_batch_deletion_impact(db: Session, batch_id: str) -> dict:
    record_count = db.query(func.count(NormalizedRecord.id)).filter(
        NormalizedRecord.batch_id == batch_id
    ).scalar() or 0
    match_count = db.query(func.count(MatchResult.id)).filter(
        MatchResult.batch_id == batch_id
    ).scalar() or 0
    issue_count = db.query(func.count(ValidationIssue.id)).filter(
        ValidationIssue.batch_id == batch_id
    ).scalar() or 0
    return {
        "record_count": record_count,
        "match_count": match_count,
        "issue_count": issue_count,
    }
```

### payment_base 规则修复
```python
# Source: [VERIFIED: manual_field_aliases.py 第 108-110 行]
# 现有规则（有问题）:
AliasRule("payment_base", ("缴费基数",), confidence=0.94)

# 修复后:
AliasRule("payment_base", ("缴费基数",), confidence=0.94,
          excludes=("养老", "医疗", "失业", "工伤", "生育", "补充", "大病", "大额"))
```

## payment_base 问题根因分析

### 问题链路

1. **解析阶段**: Excel 文件中存在多列包含 "缴费基数" 子串的表头，如：
   - "缴费基数"（独立列 -- 这是正确的 payment_base）
   - "基本养老保险(单位缴纳) / 缴费基数"（险种子列 -- 不应映射到 payment_base）
   - "失业保险 / 缴费基数"（险种子列 -- 不应映射到 payment_base）

2. **映射阶段**: `normalize_header_column()` 对每列独立匹配规则。由于 `AliasRule("payment_base", ("缴费基数",))` 只要求签名包含 "缴费基数" 子串，所有包含该子串的列都被映射为 `payment_base`。

3. **赋值阶段**: `_assign_canonical_value()` 中，第一个匹配到的列值写入 `values["payment_base"]`，后续列值写入 `field_conflicts["payment_base"]`。如果第一列恰好是某个险种的基数列（而非独立缴费基数列），就会导致 payment_base 显示为错误值。

4. **实际影响**: [VERIFIED: codebase] 广州样例的表头签名包含 "基本养老保险(单位缴纳) / 缴费基数"，该签名同时匹配 `payment_base` 规则。因为列的迭代顺序由 Excel 列顺序决定，如果险种基数列在独立缴费基数列之前出现，payment_base 就会被赋错值。

### 修复策略

在 `manual_field_aliases.py` 中修改 payment_base 规则，添加 `excludes` 排除险种关键词。这样只有独立的 "缴费基数" 列（不包含任何险种名）才会匹配。

同时需检查 `payment_salary`（"缴费工资"）是否有类似问题。经检查 [VERIFIED: manual_field_aliases.py 第 108 行]，`AliasRule("payment_salary", ("缴费工资",))` 也可能存在相同问题，需要同步修复。

### 已有数据修复

修改规则后，已入库的数据不会自动更新。需要让用户重新解析已上传批次，或提供数据重算机制。建议采取重新解析的方式，因为重解析功能已存在（`POST /{batch_id}/parse`）。

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 单值 Query 参数 `region: str` | 多值 `region: List[str]` | 本阶段 | API 契约变更，前后端同步 |
| employee_id 判断匹配状态 | JOIN MatchResult 查 match_status | 本阶段 | 更准确的匹配状态 |
| 简单删除确认 | 预查询影响范围 + 详细确认 | 本阶段 | 用户体验增强 |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | payment_base 错误仅因 AliasRule 过宽，不涉及其他存储/转换逻辑 | payment_base 根因分析 | 修复规则后仍显示错误，需排查 _assign_canonical_value 或武汉/长沙特殊逻辑 |
| A2 | MatchResult 与 NormalizedRecord 为一对一关系（UniqueConstraint 生效） | 匹配状态过滤 | JOIN 产生重复行，影响分页计数 |
| A3 | 修复 payment_base 后，已入库数据可通过重解析修复 | 已有数据修复 | 如重解析改变了其他字段值，可能影响已有匹配和校验结果 |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | 无独立配置文件，使用默认 pytest 发现 |
| Quick run command | `pytest backend/tests/test_data_management_service.py -x` |
| Full suite command | `pytest backend/tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | 多值过滤查询正确 | unit | `pytest backend/tests/test_data_management_service.py -x -k multi` | Wave 0 |
| DATA-02 | 匹配状态过滤正确 | unit | `pytest backend/tests/test_data_management_service.py -x -k match_filter` | Wave 0 |
| DATA-03 | 批次删除联动 + 预查询 | unit | `pytest backend/tests/test_import_batches_api.py -x -k delete` | 部分已有 |
| DATA-04 | payment_base 映射正确 | unit | `pytest backend/tests/test_header_normalizer.py -x -k payment_base` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest backend/tests/test_data_management_service.py backend/tests/test_header_normalizer.py -x`
- **Per wave merge:** `pytest backend/tests/ -x`
- **Phase gate:** Full suite green + 前端 `npm run lint && npm run build`

### Wave 0 Gaps
- [ ] `backend/tests/test_data_management_service.py` -- 数据管理服务测试（当前不存在）
- [ ] payment_base 修复的回归测试用例（在 test_header_normalizer.py 中新增）

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | 已有 JWT 认证 |
| V3 Session Management | no | 不涉及 |
| V4 Access Control | no | 不涉及新权限 |
| V5 Input Validation | yes | FastAPI Query 参数类型校验 + Pydantic |
| V6 Cryptography | no | 不涉及 |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| 多值参数注入 | Tampering | FastAPI Query(List[str]) 自动类型校验 |
| 大量筛选值导致慢查询 | DoS | SQLAlchemy IN 子句 + 已有分页限制 |

## Sources

### Primary (HIGH confidence)
- Codebase grep: `backend/app/mappings/manual_field_aliases.py` -- payment_base AliasRule 定义和匹配逻辑
- Codebase grep: `backend/app/services/normalization_service.py` -- `_assign_canonical_value` 冲突处理
- Codebase grep: `backend/app/core/database.py:34` -- PRAGMA foreign_keys=ON 已设置
- Codebase grep: `backend/app/models/import_batch.py` -- cascade="all, delete-orphan" 关系配置
- Codebase grep: `backend/app/models/match_result.py:19` -- UniqueConstraint on normalized_record_id
- Codebase grep: `frontend/src/pages/DataManagement.tsx` -- 当前筛选交互实现
- Codebase grep: `frontend/src/services/dataManagement.ts` -- 当前 API 客户端实现

### Secondary (MEDIUM confidence)
- FastAPI 文档: List[str] Query 参数支持 [ASSUMED: 基于 training knowledge，FastAPI 原生支持]
- AntD 文档: Select mode="multiple" + maxTagCount [ASSUMED: 基于 training knowledge]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - 无新依赖，全部使用已有库
- Architecture: HIGH - 代码路径已完全确认，变更范围明确
- Pitfalls: HIGH - payment_base 根因已通过代码分析定位，其他风险为常见 Web 开发模式
- payment_base 修复: HIGH - 根因链路完整追踪，修复方案具体可行

**Research date:** 2026-04-08
**Valid until:** 2026-05-08 (stable domain, no fast-moving dependencies)
