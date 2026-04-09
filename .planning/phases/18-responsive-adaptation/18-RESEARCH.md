# Phase 18: 全页面响应式适配 - Research

**Researched:** 2026-04-09
**Domain:** MainLayout 移动壳层 + 数据页筛选抽屉 + 宽表格响应式 + 员工自助页手机优先 + 长流程页底部主操作
**Confidence:** HIGH

## Summary

Phase 18 不是“把几个页面缩窄一点”，而是把现有 Web-only 后台在移动端和平板端真正做成可操作的系统壳层。现有代码已经具备一部分响应式基础，例如 `MainLayout.tsx` 里有 `useResponsiveCollapse(1440)`，不少页面也已使用 Ant Design `Row/Col` 的 `xs/sm/md/lg` 断点，但核心缺口仍然明显：

1. `MainLayout` 只有“收起 sider”，没有 `<768px` 的 `Drawer` 导航、汉堡按钮、导航后自动关闭逻辑。
2. `EmployeeSelfService.tsx` 仍以桌面表格历史视图为主，不符合 D-07/D-08/D-09 的手机优先卡片流。
3. `DataManagement.tsx`、`Employees.tsx`、`AuditLogs.tsx` 等筛选型页面依然默认内联展示全部筛选控件，没有“草稿态 + 应用筛选/清空”的右侧抽屉模式。
4. `SimpleAggregate.tsx`、`Results.tsx`、`Exports.tsx` 的主操作还停留在页内按钮区，移动端缺少 sticky action bar。
5. 多个表格页虽已局部使用 `scroll.x` 或固定列，但没有形成统一合同，也没有对剩余页面做系统性 sweep。

**Primary recommendation:** 按“共享壳层 → 最高价值移动页 → 筛选型数据页 → 长流程页 → 全站 sweep”拆成 5 份执行计划。这样既能优先拿下最关键的交互壳层，又能把后续页面适配建立在统一断点和复用组件之上，避免每页各自发明一套响应式逻辑。

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01: 手机端主导航必须改为 `Drawer + 顶部汉堡按钮`，不能沿用常驻 `Sider`
- D-02: 手机端 Header 仅保留页标题，隐藏面包屑
- D-03: 点击移动端 `Drawer` 菜单项后，路由跳转完成即自动关闭
- D-04: 手机端筛选器统一进入 `Drawer`，不在表格上方默认展开全部筛选控件
- D-05: 手机端筛选 `Drawer` 底部只有“应用筛选 / 清空”，修改筛选值时不得立刻刷新
- D-06: 桌面端保留当前内联筛选布局，平板/手机才切换成 `Drawer`
- D-07: `EmployeeSelfService` 手机端改为卡片流，顺序为“个人/当月汇总在前，历史记录在后”
- D-08: 历史记录默认只展开最新月份，其余月份默认收起
- D-09: 手机端“社保明细”和“公积金明细”必须上下堆叠，不做 Tabs
- D-10: `SimpleAggregate`、`Results`、`Exports` 手机端使用底部 `sticky action bar`
- D-11: 底部固定区只保留一个主动作，次要动作留在页内

### the agent's Discretion
- 断点数值只要与现有 `<=1440px` 自动折叠策略和 AntD Grid 断点一致即可
- 汉堡按钮、抽屉宽度、标题截断、sticky bar 阴影和辅助说明的具体实现
- 低优先级列在哪些“非关键页面”可以通过 `responsive` 做额外隐藏

### Deferred Ideas
- 不做移动端原生 App
- 不重做桌面端工作流和桌面端导航信息架构
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UX-03 | 全页面响应式自适应（手机端 + 平板 + 不同窗口尺寸，所有数据页面逐一适配） | 现有代码已定位共享壳层、员工自助页、筛选型数据页、长流程页和剩余宽表格页面的改造入口，可直接拆计划执行 |
</phase_requirements>

## Project Constraints

- 仅做 Web 响应式，不能扩展成原生移动端项目
- 继续使用 React 18 + Ant Design 5 + 现有主题 token 体系
- 不新增后端/数据库改造作为本阶段前提
- 不破坏已有 RBAC 导航过滤、`localStorage` 偏好持久化和运行时页面功能
- 响应式改造不能通过隐藏关键业务列来“假适配”，关键列必须依靠横向滚动保留

## Current Codebase Findings

### 1. Shared shell is the main dependency

**Observed in `frontend/src/layouts/MainLayout.tsx`:**
- 已有 `useResponsiveCollapse(1440)`，但没有 `<768px` 的 drawer 分支
- Header 永远显示 `Breadcrumb`，移动端没有腾出空间给页面标题和主操作
- `Content` 使用固定 `height: calc(100vh - 56px)` + `overflowY: auto`，适合桌面，但移动端 sticky bar 需要额外底部 padding
- 菜单搜索已经存在，但仅渲染在 sider 内部，移动场景没有合适承载位置
- 导航仍复用一套 `MENU_GROUPS`/`buildMenuItems`，这很好，意味着移动导航应该复用同一份角色过滤与菜单源，而不是新建第二套配置

**Implication:** 所有页面级适配都应建立在统一的 `isMobile / isTablet / isCompactDesktop` 判断和新的移动导航壳层之上，否则每页会重复写 `window.innerWidth` 分支。

### 2. EmployeeSelfService is the highest-value mobile page

**Observed in `frontend/src/pages/EmployeeSelfService.tsx`:**
- 当前结构是：个人资料卡 + 当月统计卡 + `Table + expandable row`
- 历史记录使用表格展开行，不符合 D-07 / D-08 / D-09
- 明细部分虽然已是两张 `Card`，但外层依旧依赖表格的展开机制，不是移动优先的卡片流

**Implication:** 该页应独立成单独 plan，直接实现“资料卡 -> 本月汇总 -> 历史月份 accordion/card -> 每月内两张堆叠明细卡”的移动分支，并保留 `>=768px` 的现有桌面布局。

### 3. Filter-heavy pages need a draft-state drawer pattern

**Observed in `frontend/src/pages/DataManagement.tsx`:**
- 地区/公司/账期/匹配状态/搜索框全部内联渲染
- 过滤值与 URL searchParams 紧耦合，现状是用户改动筛选控件就直接写 URL
- 表格已经有一部分 `fixed: 'left'` + `scroll.x`，说明宽表格基础不差，但“筛选区占满首屏”的问题依旧存在

**Observed in `frontend/src/pages/Employees.tsx` and `frontend/src/pages/AuditLogs.tsx`:**
- 两页都有典型的“筛选 + 统计 + 宽表格”结构
- `Employees.tsx` 已经引入 `Drawer`，但用于编辑表单，不是筛选抽屉
- `AuditLogs.tsx` 还是纯内联筛选，移动端横向挤压明显

**Implication:** 需要一个统一的筛选抽屉模式，最少要把 `DataManagement / Employees / AuditLogs` 纳入同一计划，要求：
- `< 992px` 时只显示一个筛选触发按钮
- 抽屉内编辑的是 draft state，不立刻请求数据
- 只有点击“应用筛选”才同步到 URL / 查询参数
- “清空”直接恢复默认筛选

### 4. Workflow pages need a shared sticky primary action

**Observed in `frontend/src/pages/SimpleAggregate.tsx`:**
- 顶部操作区同时摆放“开始聚合并导出 / 取消当前聚合 / 清除当前记录 / 进入高级页面”
- 页面主体是左右两列长内容，手机端极易导致主按钮离首屏过远

**Observed in `frontend/src/pages/Results.tsx` and `frontend/src/pages/Exports.tsx`:**
- 主按钮分别位于批次选择卡片中，且 `Results` 同时并排展示两个动作
- 这与 D-10 / D-11 冲突，移动端必须只固定“下一步主动作”

**Implication:** 应新增一个共享的 `MobileStickyActionBar` 组件，由三个长流程页面在 `<768px` 分支下复用；桌面和平板继续保留现有页内按钮，不改变桌面操作密度。

### 5. Remaining pages still need a structured sweep

**Observed in `frontend/src/pages/Imports.tsx`, `ImportBatchDetail.tsx`, `Dashboard.tsx`:**
- 都是“头部操作 + 统计卡片 + 一到多个宽表格”结构
- `Dashboard`/`Imports` 已有部分 `Row/Col` 断点，但按钮区和表格容器仍偏桌面
- `ImportBatchDetail` 存在描述卡 + header mapping inline editor + preview table，多区域在手机端会堆叠失衡

**Implication:** 这些页面不一定都要大改，但必须有一个“剩余页面响应式审计计划”，覆盖：
- `Dashboard`
- `Imports`
- `ImportBatchDetail`
- `Compare`
- `PeriodCompare`
- `Mappings`
- `FeishuSync`
- `FeishuSettings`
- `Users`
- 以及所有剩余带宽表格的页面

## Standard Patterns To Reuse

### Pattern 1: Single source of truth for breakpoints

- 使用 AntD Grid breakpoints 或轻量自定义 hook，统一暴露：
  - `isMobile: < 768px`
  - `isTablet: 768px - 991px`
  - `isCompactDesktop: 992px - 1440px`
- 不要在每个页面重新写裸 `window.innerWidth`

### Pattern 2: One navigation config, two shells

- 保持 `MENU_GROUPS`、`TOP_ITEM`、`buildMenuItems`、`useMenuOpenKeys` 为唯一菜单源
- 桌面/平板继续用 `Sider`
- 手机端改为同一套 `Menu` 挂载在 `Drawer`
- 菜单点击仍走 `navigate(key)`，再在 route change 后关闭 drawer

### Pattern 3: Draft filter state on mobile/tablet

- Applied state 继续来自 URL / 查询参数
- Draft state 在抽屉中单独维护
- `onClose` 回滚 draft 到当前 applied state
- `onApply` 一次性写回 URL/search params

### Pattern 4: Wide table contract, not “hide everything”

- 关键列固定左侧：姓名 / 工号 / 批次名称 / 模板类型 / 记录标识
- 表体负责横向滚动，页面继续负责纵向滚动
- 只有低优先级元数据允许 `responsive: ['lg']`
- 不能为了适配窄屏隐藏当前状态、账期、金额汇总、主操作列

### Pattern 5: Shared sticky primary CTA

- 仅 `<768px` 启用
- 固定底部只保留一个主按钮
- 次要按钮继续留在内容区
- 页面主体需补底部 padding，避免内容被遮挡

## Recommended Plan Shape

1. **Plan 01: Shared shell and responsive primitives**
   - `MainLayout`
   - 新的断点 hook / mobile sticky action bar / workflow steps 小屏样式

2. **Plan 02: Employee self-service mobile-first layout**
   - `EmployeeSelfService`
   - 资料卡、当月汇总、历史月份折叠、两张堆叠明细卡

3. **Plan 03: Filter-heavy data pages**
   - `DataManagement`
   - `Employees`
   - `AuditLogs`
   - 统一筛选抽屉和宽表格行为

4. **Plan 04: Long-flow pages**
   - `SimpleAggregate`
   - `Results`
   - `Exports`
   - `Imports`
   - `ImportBatchDetail`

5. **Plan 05: Remaining page sweep**
   - `Dashboard`
   - `Compare`
   - `PeriodCompare`
   - `Mappings`
   - `FeishuSync`
   - `FeishuSettings`
   - 其余 residual pages

## Common Pitfalls

### Pitfall 1: Rebuilding navigation logic separately for mobile
- **What goes wrong:** 新建第二套移动菜单数组，导致角色过滤、feishu feature flag、菜单搜索与桌面分叉
- **How to avoid:** 继续复用 `TOP_ITEM`、`MENU_GROUPS`、`buildMenuItems` 和 `allNavItems`

### Pitfall 2: Drawer filters mutating live query state on every keystroke
- **What goes wrong:** 手机端筛选抽屉只是“视觉抽屉”，但实际上仍边改边触发 URL 和数据刷新
- **How to avoid:** 抽屉里维护 draft state，只有“应用筛选”才更新查询参数

### Pitfall 3: Using responsive hiding to remove critical business columns
- **What goes wrong:** 为了让表格看起来“干净”，把金额、状态、账期等关键列直接隐藏
- **How to avoid:** 关键列固定左侧并依赖横向滚动；只隐藏低优先级元数据

### Pitfall 4: Sticky action bar duplicates or conflicts with in-page buttons
- **What goes wrong:** 手机上同时看到顶部按钮区和底部固定区，形成双主按钮甚至重复提交
- **How to avoid:** `<768px` 时把主按钮迁移为 sticky bar，页内仅保留次要动作

### Pitfall 5: Employee self-service only shrinks the existing table
- **What goes wrong:** 只是给 `Table` 加 `scroll.x`，但用户在手机上仍要水平拖动历史记录才能看明细
- **How to avoid:** 手机端直接切换成卡片流和按月折叠，而不是继续坚持桌面表格形态

## Anti-Patterns To Avoid

- 不要引入新的响应式库；AntD breakpoint 和现有 hook 足够
- 不要在前端硬编码第二套菜单配置
- 不要把桌面端筛选也一刀切改成 drawer
- 不要把 sticky action bar 做成双按钮固定底栏
- 不要把“页面宽度适配”误当成“表格字体缩小”

## Validation Architecture

### Automated verification

- **Primary commands**
  - `cd /Users/mac/PycharmProjects/5xyj/frontend && npm run lint`
  - `cd /Users/mac/PycharmProjects/5xyj/frontend && npm run build`
- **Targeted file linting during execution**
  - `npm run lint -- src/layouts/MainLayout.tsx src/components/WorkflowSteps.tsx`
  - `npm run lint -- src/pages/EmployeeSelfService.tsx`
  - `npm run lint -- src/pages/DataManagement.tsx src/pages/Employees.tsx src/pages/AuditLogs.tsx`
  - `npm run lint -- src/pages/SimpleAggregate.tsx src/pages/Results.tsx src/pages/Exports.tsx src/pages/Imports.tsx src/pages/ImportBatchDetail.tsx`
  - `npm run lint -- src/pages/Dashboard.tsx src/pages/Compare.tsx src/pages/PeriodCompare.tsx src/pages/Mappings.tsx src/pages/FeishuSync.tsx src/pages/FeishuSettings.tsx`

### Manual verification that cannot be skipped

- Mobile `<768px`
  - drawer 菜单可打开，点击菜单后自动关闭
  - breadcrumb 消失，只保留标题
  - `EmployeeSelfService` 首屏先看到个人信息和当月汇总
  - `Results`/`Exports`/`SimpleAggregate` 只有一个 sticky 主按钮
- Tablet `768px - 991px`
  - `DataManagement` / `Employees` / `AuditLogs` 切换为筛选 drawer
  - 宽表格仍通过横向滚动访问关键列
- Desktop `>= 992px`
  - 仍保留内联筛选和现有桌面按钮布局
  - 不因移动适配破坏桌面效率

### Success conditions for planning

- 所有 D-01 ~ D-11 决策都能映射到至少一个 plan objective 和 task
- UX-03 在计划中拆成共享壳层、关键页面、剩余 sweep 三层，不留“最后再看”的灰区
- 计划显式要求 lint/build，并把人工 viewport 验证列为 mandatory

## Final Recommendation

Phase 18 不需要任何后端、数据库或新依赖前置条件，核心工作量都在前端结构化改造和页面 sweep。最重要的是先把 `MainLayout`、共享断点和 sticky action bar 这类“全局骨架”打牢，然后再推进员工自助页、筛选型数据页和长流程页；否则后续每一页都会重复判断移动端行为，计划执行质量会明显下降。
