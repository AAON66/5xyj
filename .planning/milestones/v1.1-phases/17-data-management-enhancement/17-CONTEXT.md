# Phase 17: 数据管理增强 - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning

<domain>
## Phase Boundary

HR 可用更灵活的筛选和删除操作高效管理社保数据。包括：多选筛选（地区/公司/账期）、匹配状态过滤（已匹配/未匹配）、批次删除联动确认增强、个人险种缴费基数数据修复。

</domain>

<decisions>
## Implementation Decisions

### 多选筛选交互
- **D-01:** 地区、公司、账期三个筛选全部改为多选（AntD Select mode="multiple"），支持搜索和标签展示
- **D-02:** 每个多选下拉顶部加「全选」选项，方便一键勾选所有地区/公司/账期
- **D-03:** 保留级联关系：选了地区后，公司下拉只显示已选地区下的公司；选了地区+公司后，账期只显示对应的账期。与现有单选级联行为一致，只是改为多选
- **D-04:** 后端 filter-options 和 records 端点需支持多值参数（region=[a,b]&company_name=[c,d]）

### 匹配状态过滤
- **D-05:** 匹配状态过滤作为筛选栏的第四个下拉，与地区/公司/账期并列
- **D-06:** 过滤选项为三项：全部 / 已匹配 / 未匹配。默认选中「已匹配」
- **D-07:** 「未匹配」包含所有非 MATCHED 状态（UNMATCHED、DUPLICATE、LOW_CONFIDENCE、MANUAL）

### 批次删除联动
- **D-08:** 当前 cascade delete 已覆盖 NormalizedRecords + MatchResults + ValidationIssues，无需新增关联表清理
- **D-09:** 需确认 SQLite PRAGMA foreign_keys=ON 生效（STATE.md 已记录此风险）
- **D-10:** 删除确认弹窗增强：显示「此操作将同时删除 X 条明细记录、Y 条匹配结果、Z 条校验问题」，让用户知道影响范围

### 缴费基数修复
- **D-11:** 所有地区的个人险种缴费基数显示错误值，具体原因待研究阶段调查
- **D-12:** 研究阶段需深入查看解析器（parsers/）、字段映射（mappings/）、存储逻辑（services/）、前端显示（DataManagement.tsx）全链路，定位根因并修复

### Claude's Discretion
- 多选下拉的 maxTagCount 展示策略（标签过多时折叠显示）
- 匹配状态下拉的具体样式（是否用颜色区分）
- 删除影响数量的查询方式（预查询 vs 估算）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 前端核心文件
- `frontend/src/pages/DataManagement.tsx` — 数据管理页面，当前筛选/表格/Tab 全部实现
- `frontend/src/services/dataManagement.ts` — 数据管理 API 客户端（如果存在）

### 后端核心文件
- `backend/app/api/v1/data_management.py` — 数据管理 API 端点（records, filter-options, summary）
- `backend/app/services/data_management_service.py` — 数据管理服务层
- `backend/app/models/import_batch.py` — ImportBatch 模型（cascade delete 关系）
- `backend/app/models/normalized_record.py` — NormalizedRecord 模型（payment_base 字段）
- `backend/app/models/match_result.py` — MatchResult 模型（match_status 枚举）

### 解析与映射（缴费基数修复）
- `backend/app/parsers/` — 各地区解析器目录
- `backend/app/mappings/` — 字段映射配置
- `backend/app/services/normalization_service.py` — 归一化服务（如果存在）

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- AntD Select 组件：项目已广泛使用，改 mode="multiple" 改动最小
- 级联筛选逻辑：DataManagement.tsx 已有完整的单选级联，需改造为多选级联
- cascade delete：ImportBatch 模型已配置 cascade="all, delete-orphan"
- MatchResult.match_status 枚举：MATCHED/UNMATCHED/DUPLICATE/LOW_CONFIDENCE/MANUAL

### Established Patterns
- URL 状态持久化：DataManagement.tsx 使用 searchParams 持久化筛选状态，多选需适配
- filter-options API：后端已有级联 filter 端点，需扩展支持多值参数

### Integration Points
- DataManagement.tsx 筛选区域需改造为多选
- data_management.py API 端点需支持多值 query 参数
- 删除批次的确认弹窗需增强（当前在哪个页面/组件待确认）

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 17-data-management-enhancement*
*Context gathered: 2026-04-08*
