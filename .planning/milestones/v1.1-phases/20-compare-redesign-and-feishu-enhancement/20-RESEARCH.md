# Phase 20: 对比重做与飞书完善 - Research

**Researched:** 2026-04-09
**Domain:** diff 风格月度对比重做 + 飞书运行时配置前端化
**Confidence:** HIGH

## Summary

Phase 20 的难点不在“把页面换个样子”，而在于当前 compare 和 feishu 两条链路都只做到了半截：

1. `frontend/src/pages/PeriodCompare.tsx` 和 `frontend/src/pages/Compare.tsx` 已有左右值和差异字段数据，但 UI 仍是统计卡 + 表格/卡片组合，不是 roadmap 要求的左右 Excel diff 视图。
2. `backend/app/services/compare_service.py` 已经能按身份键产出 `left/right/different_fields`，而且 `compare_periods()` 也已经支持 `page/page_size`，说明后端基础并不差；真正缺的是面向 diff viewer 的窗口化合同，以及前端真正使用服务端分页而不是一次性把 500 行都塞进 DOM。
3. `frontend/src/pages/FeishuSettings.tsx` 目前只能管理 `SyncConfig`，并读取“凭证是否已配置”的状态；但 `backend/app/core/config.py` 里的飞书开关和凭证仍完全来自环境变量，前端根本没有可写目标。
4. `backend/app/api/v1/feishu_settings.py` 里的 `PUT /feishu/settings/credentials` 只做在线校验、不做持久化；与此同时，`frontend/src/hooks/useFeishuFeatureFlag.ts` 走的是 `/system/features`，后端又额外暴露了 `/feishu/settings/features`，配置来源已经出现分叉迹象。

**Primary recommendation:** 将 Phase 20 拆成 4 个 plans：

1. compare 数据契约收口
2. 共享 diff viewer + compare 页面重做
3. 飞书运行时配置持久化与统一后端入口
4. 飞书前端配置页/同步页闭环与 e2e

这样可以先把“能不能改、改了谁生效”的后端边界立住，再让 compare/feishu 前端分别落在稳定合同之上。

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| COMP-01 | 月度对比改为代码 diff 风格（左右 Excel 表格样式 + 差异单元格高亮） | 现有 compare API 已提供左右侧值和差异字段，补齐窗口化合同与共享 viewer 后即可落地 |
| FEISHU-01 | 飞书相关配置（凭证、同步设置等）可在前端页面直接修改 | 当前缺失可持久化运行时配置层；需新增后端设置服务与前端配置流 |

## Project Constraints

- 保持 React + FastAPI + SQLite 技术栈不变，不引入新的重量级虚拟列表或配置中心依赖。
- Compare 改造不能破坏现有 batch compare export 和 period compare 结果语义。
- 500+ 员工对比流畅度必须通过“服务端分页 + 前端共享 diff viewer”解决，不能再一次性渲染整批表格明细。
- 飞书凭证前端可改，不代表 secret 可以回显；任何读取接口都必须只返回脱敏/状态信息。
- 飞书运行时配置要兼容现有环境变量部署方式，推荐“数据库覆盖优先，环境变量回退兜底”。

## Current Codebase Findings

### 1. Compare 数据已经具备 diff 基础，但前端没有把它变成 workbook 视图

**Observed in:**
- `backend/app/services/compare_service.py`
- `backend/app/schemas/compare.py`
- `frontend/src/services/compare.ts`
- `frontend/src/pages/Compare.tsx`
- `frontend/src/pages/PeriodCompare.tsx`

当前 compare payload 已经包含：
- `fields`
- `rows[*].left.values`
- `rows[*].right.values`
- `different_fields`
- 各类计数器

这意味着“差异高亮”所需的数据已经存在。问题在于：
- `PeriodCompare.tsx` 仍使用 summary table + expandable detail table
- `Compare.tsx` 仍是过滤卡 + 行内上下左右值渲染
- 两页都没有“冻结身份列 + 左右面板同步滚动 + 顶部列头对齐”的共享组件

**Implication:** Phase 20 不需要重写 compare 核心算法，但需要补一层更适合 workbook diff 的前后端合同和共享组件。

### 2. 500+ 员工性能问题更多是前端使用方式问题，而不是 compare service 无法分页

**Observed in:**
- `backend/app/api/v1/compare.py`
- `backend/app/services/compare_service.py`
- `frontend/src/pages/PeriodCompare.tsx`

`compare_periods()` 已支持 `page` / `page_size`，但当前前端固定请求 `page=0&pageSize=500`，然后：
- 在浏览器中做二次搜索
- 渲染 expandable nested tables
- 不复用页面级窗口信息

**Implication:** 最稳妥的 Phase 20 路径是：
- 后端补齐页码/总页数/returned_row_count 等窗口元数据
- 搜索与 `diff_only` 下推到后端
- 前端 viewer 只渲染当前窗口的 rows，并用分页/切页控制 500+ 数据量

### 3. 飞书“前端可改配置”当前在后端层面根本不成立

**Observed in:**
- `backend/app/core/config.py`
- `backend/app/api/v1/system.py`
- `backend/app/api/v1/feishu_settings.py`
- `backend/app/services/feishu_client.py`
- `frontend/src/pages/FeishuSettings.tsx`

当前飞书运行时信息来源是：
- `Settings.feishu_sync_enabled`
- `Settings.feishu_oauth_enabled`
- `Settings.feishu_app_id`
- `Settings.feishu_app_secret`

这些都来自 `BaseSettings` 的环境变量装载。前端能做的只有：
- 看 feature flags
- 看 credentials configured 状态
- 管理 `SyncConfig`

但无法：
- 修改 app id / secret
- 修改 feishu sync / oauth 开关
- 保存后让 OAuth、sync、field discovery 走同一套新值

**Implication:** Phase 20 必须引入持久化运行时配置层，否则 FEISHU-01 无法达成。

### 4. 飞书配置入口存在分叉，需要统一“有效配置”解析

**Observed in:**
- `backend/app/api/v1/system.py`
- `backend/app/api/v1/feishu_settings.py`
- `frontend/src/hooks/useFeishuFeatureFlag.ts`

当前前端 feature flags 读 `/system/features`，而 feishu settings API 又额外实现了 `/feishu/settings/features`。这会带来两个问题：
- 日后前端可能读到不同来源
- 配置更新后哪些页面刷新、哪些页面仍用旧值会变得不清晰

**Implication:** 应引入统一的 `effective feishu settings` service，由 `/system/features`、`/feishu/settings/*`、`feishu_auth`、`feishu_sync`、`feishu_client` 共同复用。

### 5. FeishuSettings 前端已经有一半骨架，但缺真正的 admin settings hub

**Observed in:**
- `frontend/src/pages/FeishuSettings.tsx`
- `frontend/src/pages/FeishuSync.tsx`
- `frontend/src/pages/FeishuFieldMapping.tsx`
- `frontend/src/services/feishu.ts`

现状：
- `FeishuSettings.tsx` 已有移动端 Drawer、SyncConfig CRUD 表格
- `FeishuSync.tsx` 已有推送/拉取/冲突处理和历史记录
- `FeishuFieldMapping.tsx` 已有字段映射画布

缺口：
- 没有“运行时开关 + 凭证”配置区
- 没有保存后刷新 flags 的共享 client/hook
- sync/settings 两页之间还是功能并列，不是完整配置闭环

**Implication:** Phase 20 更像“把现有分散能力收口成一个可配置工作台”，而不是从零做一个新模块。

## Recommended Architecture

### A. Compare: shared workbook diff contract

建议把 compare 页面重做建立在一个共享组件上：

- `CompareWorkbookDiff`
  - 左右双面板
  - 冻结身份列（姓名/工号/证件号）
  - sticky header
  - 同步横向/纵向滚动
  - changed/left_only/right_only 高亮

配套后端合同建议至少包含：
- `page`
- `page_size`
- `total_pages`
- `returned_row_count`
- `diff_only`
- `search_text`

这样 `PeriodCompare` 和 `Compare` 都能复用一套 viewer，而不是继续维护两套差异渲染逻辑。

### B. Feishu: database-backed effective settings with env fallback

建议新增轻量持久化模型，例如 `SystemSetting`：
- `key`
- `value`
- timestamps

作用：
- 保存 `feishu_app_id`
- 保存 `feishu_app_secret`
- 保存 `feishu_sync_enabled`
- 保存 `feishu_oauth_enabled`

读取策略：
1. 先读 DB override
2. DB 无值时回退环境变量

写入策略：
- 只允许 admin
- 更新凭证前先校验
- 读取时永不回显 secret

### C. Frontend settings hub

前端建议保留 `FeishuSettingsPage` 作为主入口，但升级为 3 段：

1. 功能开关
2. 应用凭证
3. 同步目标管理

`FeishuSyncPage` 保留执行与历史记录职责，但在配置缺失/功能关闭时给出回到 settings 的明确 CTA。

## Recommended Plan Shape

1. **Plan 01: Compare backend contract polish**
   - period compare 窗口元数据
   - `diff_only/search_text` 服务端过滤
   - compare API regression tests

2. **Plan 02: Shared diff viewer + compare UI rebuild**
   - `CompareWorkbookDiff` 共享组件
   - `PeriodCompare` workbook diff 重做
   - `Compare` 对齐同一视觉和交互合同

3. **Plan 03: Feishu runtime settings persistence + effective settings service**
   - `SystemSetting` / runtime settings service
   - feature flags / auth / sync / field discovery 共用新设置来源
   - admin-only masked credential API

4. **Plan 04: Feishu frontend settings hub + e2e**
   - settings 页可编辑开关与凭证
   - 保存后刷新 feature flags
   - sync/settings 浏览器级回归

## Common Pitfalls

### Pitfall 1: 只改 `PeriodCompare.tsx` 视觉，不补数据窗口合同
- **What goes wrong:** UI 看起来像 diff，但 500+ 行时仍把所有 rows 一次性塞给浏览器
- **How to avoid:** 先做 `PeriodCompareRead` 的窗口元数据与服务端过滤，再让 viewer 只渲染当前窗口

### Pitfall 2: 为了前端可改凭证，直接把 secret 回传给浏览器
- **What goes wrong:** 敏感信息泄露，且后续日志/错误消息也可能带出 secret
- **How to avoid:** 读取接口只返回 `configured`、`masked_app_id`、`secret_configured`；写入接口只接受新值，不回显 secret

### Pitfall 3: 新增 DB 配置后，OAuth/sync/client 仍各自读取环境变量
- **What goes wrong:** 页面显示“已更新”，但实际飞书 OAuth 或同步仍用旧配置
- **How to avoid:** 引入统一 `effective feishu settings` service，所有入口只从这一处读取

### Pitfall 4: Compare 页面各做一套 diff viewer
- **What goes wrong:** `Compare.tsx` 与 `PeriodCompare.tsx` 行为分叉，后续修一个页面会漏另一个
- **How to avoid:** 共享 `CompareWorkbookDiff`，页面只负责数据获取与筛选壳层

### Pitfall 5: 只做 settings 页面，不管 sync 页面缺配置时的引导
- **What goes wrong:** 用户能保存配置，但同步页仍沉默失败或只是空白
- **How to avoid:** `FeishuSyncPage` 对 disabled/missing credentials 明确给出状态提示和“去设置页”入口
