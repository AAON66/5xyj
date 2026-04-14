# Phase 19: 融合能力增强 - Research

**Researched:** 2026-04-09
**Domain:** 快速融合补充输入源 + 特殊规则持久化 + Tool/Salary 模板边界收口
**Confidence:** HIGH

## Summary

Phase 19 不是单纯“多两个字段”。现有代码已经有一部分承担额相关实现，但它停在 exporter 末端，前面的输入、持久化、批次级应用和前端配置入口都还不存在，因此现在的承担额能力本质上是占位而不是可用功能。

最关键的现状有 4 点：

1. `frontend/src/pages/SimpleAggregate.tsx` 和 `frontend/src/services/aggregate.ts` 当前只支持三类输入: 社保文件、公积金文件、员工主档；没有“个人承担额来源”或“特殊规则”入口。
2. `backend/app/exporters/tool_exporter.py` 已经预留了 `个人社保承担额` / `个人公积金承担额` 两列，但 `backend/app/exporters/export_utils.py` 中 `_resolved_personal_social_burden()` 与 `_resolved_personal_housing_burden()` 目前直接返回 `Decimal('0')`。
3. `backend/app/exporters/salary_exporter.py` 现在也输出承担额列，和 roadmap 成功标准“新字段仅影响 Tool 模板输出，Salary 模板保持不变”冲突，Phase 19 必须显式回收这条边界。
4. 系统还没有任何“特殊规则”持久化模型或 API；现有最接近的持久化模式是 `SyncConfig` 这种带 JSON 配置的表，但它服务于飞书同步，不适合作为融合规则最终形态。

**Primary recommendation:** 以“规则持久化与 API -> 额外输入源归一化 -> 聚合/导出编排 -> 前端配置与复用”拆成 4 个 plans。这样可以先把长期数据模型和边界立住，再让运行期批次和 UI 依附同一套服务，而不是把规则散落到 exporter 或前端 local state 里。

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FUSE-01 | 融合增加个人社保承担额和个人公积金承担额（支持 Excel 上传或飞书文档同步输入） | 需要新增补充输入源接入层，并把承担额作为 batch/export overlay 注入 Tool 模板 |
| FUSE-03 | 快速融合支持特殊规则配置（选人+选字段+覆盖值，规则可保存复用） | 需要新增持久化规则模型、CRUD API、批次应用入口和前端规则编辑 UX |

## Project Constraints

- 双模板导出仍是主链路，不允许为 Phase 19 破坏现有 Salary/Tool 双输出。
- Salary 模板是已稳定链路，Phase 19 必须把承担额能力限定在 Tool 模板，不得继续污染 Salary 输出。
- 规则要可追溯，不能只在前端组装后直接丢给 exporter。
- 飞书输入路径可以复用既有 `SyncConfig` / `feishu_sync_service` 能力，但不能把“全量 pull 到 NormalizedRecord”当成快速融合的唯一方案。
- 当前测试和运行环境是本地 SQLite + pytest + frontend lint/build/e2e，方案必须能在这套环境下自动验证。

## Current Codebase Findings

### 1. 快速融合 API 还没有“补充输入源”概念

**Observed in:**
- `frontend/src/services/aggregate.ts`
- `backend/app/api/v1/aggregate.py`
- `backend/app/services/aggregate_service.py`

现有 aggregate request 仅接受:
- `files`
- `housing_fund_files`
- `employee_master_file`
- `employee_master_mode`
- `batch_name`

这意味着承担额来源无论来自 Excel 还是飞书，都还没有 transport contract。Phase 19 不能只改 exporter；必须先扩 API/input model。

**Implication:** 需要为 aggregate 新增“额外融合输入”契约，至少支持:
- 一个可选的 burden Excel 上传
- 一个可选的 Feishu 配置引用或同步源引用
- 一个可选的特殊规则集合或应用策略

### 2. exporter 已有承担额列，但目前是硬编码零值

**Observed in:**
- `backend/app/exporters/tool_exporter.py`
- `backend/app/exporters/salary_exporter.py`
- `backend/app/exporters/export_utils.py`
- `backend/tests/test_template_exporter.py`
- `backend/tests/test_api_compatibility.py`

当前状态是:
- Tool 模板列 22/23 已预留承担额
- Salary 模板末尾也仍然保留承担额列
- burden resolve helper 永远返回 `0`
- 相关测试也把“默认 0”当成正确行为

**Implication:** Phase 19 必须做两个方向的调整:
1. 把 burden 值从“推断/占位”改成“显式来源 + 可覆盖”。
2. 重写 salary exporter regression contract，让 Salary 模板恢复原稳定结构，只保留既有字段。

### 3. 飞书同步基础设施可复用，但不能直接照搬

**Observed in:**
- `backend/app/models/sync_config.py`
- `backend/app/api/v1/feishu_settings.py`
- `backend/app/services/feishu_sync_service.py`

现有 Feishu 能力已经提供:
- 同步配置持久化 (`SyncConfig`)
- 字段映射 JSON
- 拉取/推送逻辑

但问题也很明确:
- `pull_records_from_feishu()` 是把数据写回 `NormalizedRecord`，属于系统主数据同步，不是“单次快速融合补充源”
- pull 逻辑给 `NormalizedRecord` 塞 sentinel `batch_id/source_file_id`，这更像过渡实现，不适合直接变成 Phase 19 的运行期依赖

**Implication:** 最稳妥的 Phase 19 路径不是“先 pull 到 normalized_records 再聚合”，而是:
- 复用 `SyncConfig` 作为 Feishu source config 的配置入口
- 新增一个 batch 级 adapter，把 Feishu rows 映射为承担额补充输入
- 在 aggregate runtime 中以内存/临时 DTO 的形式合入，而不是污染常规导入表

### 4. 特殊规则需要独立持久化模型，而不是塞进 raw_payload

**Observed in:**
- `backend/app/models/normalized_record.py`
- `backend/app/models/sync_config.py`
- `frontend/src/pages/SimpleAggregate.tsx`

系统目前没有适合“选员工 + 选字段 + 覆盖值 + 可复用”的持久化对象。

`raw_payload` 不适合承载这类规则，因为:
- 它是记录级 provenance，不是长期配置
- 无法单独 CRUD
- 不能自然支撑“后续融合复用”

**Implication:** 应新增独立规则模型。推荐最小结构:
- `FusionRule`
  - `id`
  - `employee_scope_type` (`employee_id` / `id_number`)
  - `employee_scope_value`
  - `field_name`
  - `override_value`
  - `is_active`
  - `note`
  - `created_by`
  - timestamps

如需成组复用，可再加轻量 `FusionRuleSet`；但如果 phase 目标只要求“保存并在后续复用”，默认全局 active rule library 已足够，不必一开始引入复杂版本化。

### 5. 验证基础已经足够，不需要为 Phase 19 重新发明测试骨架

**Observed in:**
- `backend/tests/test_aggregate_api.py`
- `backend/tests/test_template_exporter.py`
- `backend/tests/test_aggregate_service.py`
- `frontend/tests/e2e/responsive.spec.ts`

已有能力包括:
- aggregate API 端到端测试
- dual-template exporter regression
- exporter header contract 测试
- frontend Playwright E2E 框架

**Implication:** Phase 19 的自动化验证可以直接建立在现有测试基础上，重点新增:
- burden Excel source merge tests
- mocked Feishu source adapter tests
- special rule persistence / apply tests
- salary/tool template boundary regression tests
- quick aggregate UI rule editor / source selector e2e

## Recommended Architecture

### A. 数据边界

将 Phase 19 分成 3 层:

1. **Persistent rule layer**
   - 保存可复用特殊规则
   - 提供 CRUD / list / activate/deactivate

2. **Batch input layer**
   - 负责把 burden Excel 或 Feishu source 归一化为统一结构
   - 统一结构建议至少包含:
     - `employee_id`
     - `id_number`
     - `personal_social_burden`
     - `personal_housing_burden`
     - `source_kind`
     - `source_ref`

3. **Export overlay layer**
   - 在 aggregate runtime/export 阶段，根据员工键把 burden source + FusionRule 覆盖到导出上下文
   - 只把 overlay 应用到 Tool 模板
   - Salary 模板继续只用原有字段

### B. 员工匹配策略

承担额输入和特殊规则都必须使用可解释匹配:

优先级建议:
1. `employee_id`
2. `id_number`
3. 拒绝仅按姓名静默命中

如果补充输入无法稳定匹配员工:
- 记录 warning / issue
- 不静默套用到错误人

### C. 前端入口建议

最合适的前端入口仍然是 `SimpleAggregate`，而不是新页面，因为用户心智是“在快速融合里补额外信息并导出”。

推荐 UI 结构:
- 一个新的“承担额来源”卡片
  - `不使用`
  - `上传 Excel`
  - `选择飞书配置`
- 一个新的“特殊规则”卡片或 Drawer
  - 当前已选规则列表
  - 新增规则表单: 选员工、选字段、填覆盖值
  - 保存为可复用规则

如果规则数量较多，再在 Settings 下补一个管理页；但 Phase 19 不需要先做完整后台管理系统。

## Salary / Tool Boundary Contract

这是 Phase 19 最重要的技术边界:

- `tool_exporter.py`
  - 接受显式 burden overlay
  - 继续输出承担额两列

- `salary_exporter.py`
  - 移除承担额列
  - 恢复为只承载原有稳定薪酬模板字段

- `export_utils.py`
  - 不再把 burden helper 作为“从原始记录自动推断”的机制
  - 改为“读取 batch overlay / explicit rule result”

## Recommended Plan Shape

1. **Plan 01: Fusion rule persistence + CRUD API**
   - Alembic migration
   - 新模型 / schema / service / API
   - 支持规则保存、查询、启停、复用

2. **Plan 02: Burden source adapters for Excel + Feishu**
   - burden Excel 解析
   - Feishu config -> burden row adapter
   - 统一 employee-keyed DTO
   - provenance / unmatched diagnostics

3. **Plan 03: Aggregate pipeline integration + exporter boundary fix**
   - aggregate request/response contract 扩展
   - runtime 应用 burden source + special rules
   - Tool 模板接入 overlay
   - Salary 模板回退到无承担额结构

4. **Plan 04: SimpleAggregate UX + automated verification**
   - 前端承担额来源选择
   - 特殊规则编辑/复用入口
   - Playwright + pytest regression 覆盖

## Validation Architecture

### Core test layers

1. **Backend unit/service**
   - rule service CRUD
   - burden adapter parsing and matching
   - exporter overlay logic

2. **Backend API**
   - aggregate API accepts optional burden source / rule selection
   - rule CRUD API
   - Feishu adapter path with mocked client

3. **Regression export**
   - Tool 模板承担额列写入正确
   - Salary 模板列结构不包含承担额

4. **Frontend E2E**
   - quick aggregate can choose burden source
   - can add/save/reuse special rule
   - mobile/tablet still usable after adding new controls

### Suggested commands

- Quick backend: `cd /Users/mac/PycharmProjects/5xyj && pytest backend/tests/test_aggregate_api.py backend/tests/test_template_exporter.py backend/tests/test_aggregate_service.py -q`
- Quick frontend: `cd /Users/mac/PycharmProjects/5xyj/frontend && ./node_modules/.bin/eslint src/pages/SimpleAggregate.tsx src/services/aggregate.ts`
- Full suite: `cd /Users/mac/PycharmProjects/5xyj/backend && pytest && cd /Users/mac/PycharmProjects/5xyj/frontend && npm run lint && npm run build && npm run test:e2e`

### Nyquist focus

- Every plan should carry at least one automated verification step.
- No more than 2 consecutive tasks should rely only on read/grep verification.
- Feishu path must use mocked client responses; live tenant access is not required for phase completion.

## Common Pitfalls

### Pitfall 1: 把 burden 值继续做成 exporter 内部推断
- **What goes wrong:** 规则和来源不透明，数据不可追溯，测试只能验证“结果像对的”
- **How to avoid:** 使用显式 burden DTO + rule overlay，来源写入 provenance

### Pitfall 2: 直接复用 Feishu pull 写回 `NormalizedRecord`
- **What goes wrong:** 快速融合补充源污染主数据表，批次边界模糊
- **How to avoid:** 仅复用 config/field mapping，运行期以内存 adapter 合入

### Pitfall 3: 把特殊规则只存在前端 local state
- **What goes wrong:** 刷新丢失，无法复用，和 success criterion 3 冲突
- **How to avoid:** 后端持久化规则表，前端只做编辑与选择

### Pitfall 4: Tool 改好了但 Salary 没收口
- **What goes wrong:** phase 通过后仍然违反 roadmap success criterion 4
- **How to avoid:** 把 salary header/export regression 当成 blocking verify

### Pitfall 5: 用姓名做特殊规则命中键
- **What goes wrong:** 重名/改名导致错误覆盖
- **How to avoid:** 优先 employee_id / id_number，姓名仅作为展示辅助

## High-Signal Conclusions

1. Phase 19 的真实缺口不是“多两个列”，而是缺一条从输入源到 exporter 的完整 overlay 管道。
2. `tool_exporter` 已经为承担额预留好列位，最安全的实现方向是补输入和 overlay，而不是再改模板结构。
3. `salary_exporter` 当前状态和 roadmap 冲突，必须作为 Phase 19 的显式修复项纳入计划。
4. 特殊规则必须落独立持久化模型，不能塞进 `raw_payload` 或前端临时状态。
5. Feishu 能力应该复用配置与字段映射，不应该复用“写回 NormalizedRecord”的现有 pull 语义。
6. burden 输入与特殊规则都必须以 `employee_id/id_number` 为命中主键，不能按姓名静默套用。
7. 这期可以不引入复杂 rule-set/versioning，先做全局 active rule library 已能满足“保存并复用”。
8. aggregate API、template exporter tests、frontend Playwright 已经提供 Phase 19 所需的大部分验证骨架。
9. Feishu 路径可以用 mocked client 完成自动化验证，不需要等待真实租户联调。
10. 最合理的执行顺序是先后端模型与 adapter，再 aggregate/export 集成，最后前端接入与回归验证。
