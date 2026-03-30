---
phase: 6
reviewers: [codex, claude]
reviewed_at: 2026-03-30T14:00:00+08:00
plans_reviewed: [06-01-PLAN.md, 06-02-PLAN.md]
---

# Cross-AI Plan Review — Phase 6

## Codex Review (OpenAI Codex CLI 0.116.0)

### Plan 06-01: Backend Infrastructure

#### Summary
This plan is directionally solid and mostly aligned with the Phase 6 goals: it covers the new `created_by` audit field, the main filtered record view, summary views, and a dashboard quality endpoint. The main weakness is that it compresses a lot of behavior into one wave without fully specifying query semantics, performance boundaries, and consistency with the project's existing validation pipeline. As written, it will probably produce working endpoints, but there is meaningful risk of ambiguous metrics, slow queries on larger datasets, and frontend/backend contract drift around filters, pagination, and summary shape.

#### Strengths
- Covers all core backend surfaces needed by the frontend in one coherent slice.
- Includes migration plus model update for `ImportBatch.created_by`, which is necessary for DATA-04.
- Keeps role protection explicit with `require_role("admin", "hr")`.
- Separates service layer from API layer, which should reduce route bloat.
- Includes test coverage for the major new areas instead of treating them as incidental.
- Duplicate/anomaly metrics are explicit rather than deferred to "future refinement".
- Nullable `created_by` with `SET NULL` correctly respects legacy records and user deletion.

#### Concerns
- `HIGH`: The duplicate rule `same person_name + billing_period within same batch` is likely too weak. It will create false positives for common names and false negatives when duplicates differ only by formatting. The project already has `id_number`, `social_security_number`, `employee_id`, and provenance fields; the plan underuses them.
- `HIGH`: Data quality metrics may diverge from the existing validation system. If Phase 2/4 already produce validation issues, introducing separate ad hoc quality counting logic risks inconsistent numbers between "validation" and "dashboard quality".
- `HIGH`: The plan does not specify whether summaries are computed over normalized records, matched employees, latest records only, or all records including duplicates. That ambiguity directly affects DATA-02.
- `MEDIUM`: Optional filters plus pagination are mentioned, but sort order is not. Without deterministic ordering, pagination can be unstable.
- `MEDIUM`: `get_filter_options` is underspecified for the cascading requirement.
- `MEDIUM`: Returning Pydantic models directly from the service layer can be convenient, but it tends to couple domain logic to transport shape.
- `MEDIUM`: The anomaly thresholds are hardcoded constants without a plan for configurability or region-specific exceptions.
- `MEDIUM`: No explicit mention of query efficiency.
- `LOW`: `created_by` injection "from auth token" is correct, but the plan does not mention how imports created by background jobs or scripts are handled.
- `LOW`: No explicit handling of null or malformed billing periods in filtering and grouping.

#### Suggestions
- Define summary semantics explicitly (which records count, how duplicates are handled).
- Strengthen duplicate detection (prefer `id_number` or `social_security_number`, with fallback to `person_name + company_name + billing_period`).
- Specify filter endpoint behavior (region unscoped, company scoped by region, period scoped by region+company).
- Add explicit default sorting for every list endpoint.
- Make anomaly thresholds configurable or move to a settings module.
- Add tests for edge cases (empty results, invalid filter combos, null payment_base, pagination stability).
- Prefer SQL aggregation over Python post-processing.

#### Risk Assessment: MEDIUM

---

### Plan 06-02: Frontend Implementation

#### Summary
This is a practical and appropriately scoped frontend plan. It maps well to the user decisions: standalone page, URL-persisted cascading filters, two-tab structure, expandable detail rows, summary toggle, dashboard enhancement, and imports audit info. The main risk is dependency on backend API shape that is not yet specified tightly enough.

#### Strengths
- Directly reflects the confirmed UX decisions rather than improvising a new structure.
- Keeps the new functionality in a dedicated page, which matches D-01 and limits disruption to existing pages.
- URL query param persistence is the right choice for refresh safety and shareable state.
- Reuses existing `SectionState` instead of introducing new UI abstractions.
- Avoids component-library creep, which matches the phase constraint.
- Single expanded row at a time is a sensible complexity cap.

#### Concerns
- `HIGH`: The plan depends heavily on backend filter semantics, summary payload shapes, and pagination contracts that are not yet nailed down.
- `HIGH`: Cascading filters with URL persistence need explicit reset rules. Stale query params can easily become invalid.
- `MEDIUM`: Pagination reset behavior is not specified for filter/tab changes.
- `MEDIUM`: Expansion state survival across pagination/filter changes is implicit.
- `MEDIUM`: No mention of horizontal overflow handling for wide tables.
- `MEDIUM`: Billing period formatting assumes consistent raw period format from backend.
- `MEDIUM`: Dashboard quality section has no drill-through to affected batches.
- `LOW`: Role-based nav filtering should remain backed by backend guards.
- `LOW`: Human verification checkpoint is vague.

#### Suggestions
- Lock the API contract before frontend implementation.
- Define URL state rules explicitly (which changes clear which params).
- Persist tab and summary dimension in query params too.
- Add frontend handling for "selected filter value no longer valid".
- Plan for table ergonomics (sticky headers, horizontal scroll).
- Make Dashboard batch rows clickable to import detail page.
- Define human verification checkpoint concretely.

#### Risk Assessment: MEDIUM

---

## Claude Review (Claude Code 2.1.87, independent session)

### Plan 06-01: Backend Infrastructure

#### Summary
扎实的后端基础设施计划，覆盖了从数据库迁移到API端点的完整链路。任务分解清晰，依赖关系合理。主要风险在于数据质量检测的阈值策略过于简单，以及汇总查询在数据量增长后的性能隐患。

#### Strengths
- Alembic迁移对 `created_by` 使用 nullable + SET NULL，正确处理了遗留数据（D-15）和用户删除场景
- 服务层直接返回Pydantic模型，减少了转换层的样板代码
- 所有端点统一使用 `require_role("admin", "hr")` 守卫，权限模型清晰
- 过滤/分页/汇总拆分为独立服务函数，职责单一，易于测试
- 测试覆盖分为三个文件，关注点分离好

#### Concerns
- **HIGH** — 异常金额阈值硬编码（`payment_base < 1000 or > 50000`）。不同地区的缴费基数差异很大，深圳和长沙的合理范围完全不同。这会产生大量误报或漏报。
- **HIGH** — 重复检测仅按 `person_name + billing_period` 在同一批次内判断。同名不同人会误判为重复；跨批次的真正重复完全检测不到。
- **MEDIUM** — 汇总查询在 SQLite 上对全表做 GROUP BY + SUM，记录量超过数万条时性能会显著下降。缺少索引策略说明。
- **MEDIUM** — `get_filter_options` 没有说明是否根据已选过滤条件做级联约束（D-02要求级联过滤）。
- **LOW** — 缺少对 `created_by` 注入的时序说明。

#### Suggestions
- 异常阈值应改为可配置（按地区或全局配置），或者采用统计方法（如同批次均值 ± 2σ）
- 重复检测应使用 `id_number + billing_period` 作为主键
- 为 `normalized_records` 表添加复合索引
- `get_filter_options` 应支持带条件参数的级联约束
- 明确 `created_by` 的注入位置

#### Risk Assessment: MEDIUM

---

### Plan 06-02: Frontend Implementation

#### Summary
前端计划结构完整，覆盖了级联过滤、双Tab布局、行展开、URL持久化等核心交互。手写CSS Tab Bar的决策符合Phase 7约束。主要风险在于交互细节的完备性和与后端级联过滤的协调。

#### Strengths
- URL query params 持久化过滤状态，刷新安全，可分享链接
- 双Tab + 二级切换的信息架构清晰
- 复用现有 `SectionState` 组件，避免重复造轮子
- 导航项按角色过滤可见性，与后端权限守卫形成双层防护
- Dashboard质量区块增强现有页面（D-10），避免用户认知成本增加

#### Concerns
- **HIGH** — 级联过滤的实现细节不清。如果后端不支持级联约束，前端需要自行过滤，可能导致用户看到不相关的选项。
- **MEDIUM** — 分页仅有 prev/next + page size，缺少总记录数和总页数显示。
- **MEDIUM** — 行展开没有说明是否需要额外API请求。
- **MEDIUM** — 手写CSS Tab Bar缺少键盘导航和 ARIA 属性。
- **LOW** — Dashboard批次明细表如果批次数量很多需要分页限制。

#### Suggestions
- 明确级联过滤策略：推荐后端支持带条件的 `filter-options`
- 分页应显示"共 X 条记录，第 Y/Z 页"
- 明确行展开的数据来源（建议列表API已返回完整数据，展开时用隐藏字段渲染）
- Dashboard批次明细表限制显示最近10-20条

#### Risk Assessment: MEDIUM

---

## Consensus Summary

### Agreed Strengths
（2个评审器均认同）

1. **架构分层清晰** — 后端服务层/API层分离，前端复用现有组件，职责划分得当
2. **权限模型正确** — `created_by` 的 nullable + SET NULL 处理，`require_role` 守卫，角色过滤导航
3. **URL 持久化正确选择** — 使用 query params 实现刷新安全和可分享链接
4. **范围控制得当** — 没有引入新组件库，没有 scope creep 到 Phase 7

### Agreed Concerns
（2个评审器均提出，优先级最高）

1. **🔴 重复检测逻辑过弱** — 仅按 `person_name + billing_period` 在单批次内判断，应优先使用 `id_number`，且需支持跨批次检测
2. **🔴 异常金额阈值不够灵活** — 硬编码的 1000-50000 范围不适用于所有地区，应改为可配置或统计方法
3. **🔴 级联过滤的前后端契约不清** — 两个计划都未明确 `filter-options` API 是否接受已选条件作为参数来实现级联约束
4. **🟡 汇总查询性能隐患** — 全表 GROUP BY + SUM 缺少索引策略和性能基线
5. **🟡 分页排序未指定** — 无确定性排序可能导致分页不稳定
6. **🟡 汇总语义模糊** — 未明确汇总是基于全部记录、已匹配记录还是去重后记录

### Divergent Views
（评审器之间的差异意见）

1. **ARIA 无障碍** — Claude 提出手写 Tab Bar 缺少 `role="tablist"` / `role="tab"` 属性，Codex 未提及
2. **行展开数据来源** — Claude 关注是否需要额外 API 请求，Codex 未深入此点
3. **服务层返回 Pydantic 模型** — Codex 认为这会耦合 domain/transport，Claude 认为这减少样板代码
4. **批次明细表分页** — Claude 建议限制显示条数，Codex 建议添加 drill-through 链接到导入详情页
