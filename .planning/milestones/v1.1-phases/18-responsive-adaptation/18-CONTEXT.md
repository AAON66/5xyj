# Phase 18: 全页面响应式适配 - Context

**Gathered:** 2026-04-09
**Status:** Ready for planning

<domain>
## Phase Boundary

在不新增功能的前提下，把现有 Web 系统完整适配到手机、平板和不同窗口尺寸下可用。重点覆盖移动端导航壳层、数据页筛选交互、员工自助查询的手机优先布局，以及上传/校验/导出等长流程页面的主操作可达性。

</domain>

<decisions>
## Implementation Decisions

### 移动端导航与 Header
- **D-01:** 手机端主导航使用 `Drawer + 顶部汉堡按钮`，不沿用桌面端常驻 `Sider`
- **D-02:** 手机端 Header 只保留页标题，隐藏面包屑，优先让出横向空间给导航触发和核心操作
- **D-03:** 用户点击 `Drawer` 内的菜单项后，路由跳转完成即自动关闭 `Drawer`

### 数据页筛选区
- **D-04:** 手机端筛选器统一收进由“筛选”按钮打开的 `Drawer`，不在表格上方默认展开全部筛选控件
- **D-05:** 手机端筛选 `Drawer` 底部提供统一的“应用筛选 / 清空”操作；修改筛选值时不立即触发表格刷新
- **D-06:** 桌面端保留当前页内内联筛选布局，平板/手机才切换到 `Drawer` 模式，不把所有尺寸统一成 `Drawer`

### 员工自助查询移动端布局
- **D-07:** `EmployeeSelfService` 在手机端改为卡片流布局，顺序为“个人/当月汇总在前，历史记录在后”，不保留桌面表格感优先
- **D-08:** 历史记录默认只展开最新月份，其余月份默认收起，由用户按需展开
- **D-09:** 手机端“社保明细”和“公积金明细”采用上下堆叠的两张卡片，不做 Tabs 切换

### 长流程页面主操作
- **D-10:** `SimpleAggregate`、`Results`、`Exports` 等长流程页面在手机端使用底部 `sticky action bar`
- **D-11:** 底部固定区只保留一个主动作；次要动作继续放在页内或折叠菜单中，不并排堆多个固定按钮

### the agent's Discretion
- 手机/平板/桌面的具体断点数值，只要与现有 `<=1440px` 自动折叠策略和已有 AntD Grid 断点体系一致
- `Drawer` 宽度、汉堡按钮样式、页标题文案截断方式
- 数据页中哪些次要控件需要额外做间距压缩或行内重排
- `sticky action bar` 的具体视觉样式、阴影、是否显示辅助说明
- 哪些低优先级列可以仅在非关键页面上用 `responsive` 做额外隐藏，只要不破坏“关键列固定 + 横向滚动可见”的主规则

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 范围与验收
- `.planning/ROADMAP.md` — Phase 18 的目标、依赖和 4 条成功标准
- `.planning/REQUIREMENTS.md` — `UX-03` 的正式需求映射
- `.planning/PROJECT.md` — v1.1 里程碑目标、Web-only 约束、不可扩 scope 的边界

### 前置阶段已锁定的约束
- `.planning/phases/07-design-system-ui-foundation/07-CONTEXT.md` — `Layout + Sider + Header` 基础壳层、紧凑后台风格、组件统一原则
- `.planning/phases/07-design-system-ui-foundation/07-UI-SPEC.md` §Responsive Breakpoints — 早期断点基线和“平板隐藏侧栏/汉堡入口”的历史约束
- `.planning/phases/08-page-rebuild-ux-flow/08-CONTEXT.md` — `<=1440px` 自动折叠、表格横向滚动、固定左列、WorkflowSteps 的既有决定
- `.planning/phases/08-page-rebuild-ux-flow/08-UI-SPEC.md` §2, §4 — 表格响应式合同和工作流步骤组件合同
- `.planning/phases/14-style-tokens-dark-mode/14-CONTEXT.md` — Header 中主题切换按钮位置、深色 `Sider` 保持不变、token 化约束
- `.planning/phases/15-menu-reorganize-settings-nav/15-CONTEXT.md` — 当前菜单分组结构与 `localStorage` 持久化策略
- `.planning/phases/05-employee-portal/05-CONTEXT.md` — 员工自助查询单页结构、最新月份优先、历史展开查看的业务模型
- `.planning/phases/06-data-management/06-CONTEXT.md` — 数据管理页的现有筛选/表格/URL 持久化边界

### 响应式专项研究
- `.planning/research/ARCHITECTURE.md` — `MainLayout` 现状、移动端 `Drawer` 缺口、逐页响应式集成点
- `.planning/research/FEATURES.md` — 响应式表格、Header 简化、受影响页面优先级
- `.planning/research/PITFALLS.md` — 避免在窄屏隐藏关键保险列、导航后关闭 `Drawer`、优先适配员工自助页
- `.planning/research/SUMMARY.md` — Phase 18 的阶段理由和需要规避的响应式风险

### 现有代码入口
- `frontend/src/layouts/MainLayout.tsx` — 当前 `Sider` / Header / Content 壳层、主题切换、菜单搜索、折叠逻辑
- `frontend/src/components/WorkflowSteps.tsx` — 上传到导出的步骤条组件
- `frontend/src/hooks/useMenuOpenKeys.ts` — 菜单展开状态的 `localStorage` 持久化模式
- `frontend/src/theme/index.ts` — Layout / Menu / Table 的主题 token 配置
- `frontend/src/pages/EmployeeSelfService.tsx` — 最高优先级移动端页面
- `frontend/src/pages/SimpleAggregate.tsx` — 长流程上传页面和主按钮交互
- `frontend/src/pages/DataManagement.tsx` — 最复杂的筛选 + 宽表格页面
- `frontend/src/pages/Imports.tsx` — 批次管理页面的筛选与表格基线
- `frontend/src/pages/Results.tsx` — 校验匹配页的宽表格与流程结果展示
- `frontend/src/pages/Exports.tsx` — 导出结果页与下载动作

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/layouts/MainLayout.tsx`: 已有 `useResponsiveCollapse(1440)`、菜单分组、主题切换、Header/Breadcrumb 壳层，是移动端 `Drawer` 和紧凑 Header 的首要改造点
- `frontend/src/components/WorkflowSteps.tsx`: 现成的上传到导出引导组件，Phase 18 只需做小屏可用性适配，不必重写流程引导
- `frontend/src/hooks/useMenuOpenKeys.ts`: 已经定义了菜单展开状态的持久化模式，移动导航应兼容而不是替换这套状态
- `frontend/src/pages/EmployeeSelfService.tsx`: 已有“最新汇总 + 历史记录 + 明细表”数据结构，适合转为卡片流而不是另建新 API
- `frontend/src/theme/index.ts`: Phase 14 已完成 token 化，响应式调整不应再引入新的硬编码颜色

### Established Patterns
- 页面布局已广泛使用 AntD `Row/Col` 的 `xs/sm/md/lg` 断点模式，Phase 18 应在这个模式内做逐页收敛
- 关键数据页已普遍采用 `Table scroll.x + fixed left` 的处理方式，Phase 18 重点是补齐覆盖面和手机交互，不是发明新的表格系统
- 路由路径保持平铺且稳定，菜单重组只改变视觉分组；响应式导航也应保持相同路由结构
- 偏好持久化当前统一走 `localStorage`（如 `theme-mode`、`menu-open-keys`、`sider-collapsed`），新交互应尽量复用同类策略

### Integration Points
- `MainLayout` 需要承接手机端 `Drawer`、Header 压缩、Content padding 调整，以及 route change 后自动关闭移动导航
- `EmployeeSelfService` 需要最高优先级的卡片化移动布局重排
- `SimpleAggregate`、`Results`、`Exports` 需要统一的手机端底部主操作模式
- `Imports`、`DataManagement`、`Employees` 等含多筛选条件的页面需要筛选 `Drawer` 和确认式应用逻辑
- 其余宽表格页面需要逐页审计：`Dashboard`、`ImportBatchDetail`、`Compare`、`FeishuSync`、`FeishuSettings`

</code_context>

<specifics>
## Specific Ideas

- 这次响应式适配优先考虑手机端“单手可达”和“首屏不被控件挤满”
- 桌面效率优先保留，不因为移动端适配去重做桌面筛选或桌面导航模式
- 员工自助查询是最高价值移动端页面，移动端应先让员工看清“本月结果”和“历史入口”，再看分项细节

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 18-responsive-adaptation*
*Context gathered: 2026-04-09*
