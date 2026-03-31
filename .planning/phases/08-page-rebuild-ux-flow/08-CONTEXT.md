# Phase 8: Page Rebuild & UX Flow - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

在 Phase 7 的 Ant Design 5 基础上，实现角色感知导航、响应式布局适配、中文本地化完善、以及上传到导出的端到端工作流引导。所有页面在不同分辨率下正常展示，所有文案完全中文化，操作流程无死角。

</domain>

<decisions>
## Implementation Decisions

### 角色导航差异化
- **D-01:** 保持现有方式——同一个 MainLayout 侧边栏，根据角色过滤菜单项（buildMenuItems 逻辑）。不做分角色布局
- **D-02:** 员工角色登录后直接跳转到 /employee/query 查询页，不需要工作台首页
- **D-03:** 用户访问无权限页面时静默跳转回该角色的默认页面（当前 RoleRoute 已有此行为，保持不变）

### 响应式布局
- **D-04:** 屏幕宽度 ≤1440px 时侧边栏自动折叠为图标模式（64px），利用现有 Sider collapsible 功能加断点触发
- **D-05:** 表格列溢出时使用 Ant Table scroll={{ x: true }} 水平滚动，固定左侧关键列（姓名/工号）

### 中文本地化
- **D-06:** 使用 Ant Design ConfigProvider locale={zhCN} 解决组件内置文案（分页、日期选择器等），业务文案继续硬编码中文。不引入 i18n 框架
- **D-07:** 在前端 API 客户端层统一拦截错误，根据 HTTP 状态码和后端 error code 映射为中文错误提示。后端继续返回英文 error code

### 上传到导出工作流
- **D-08:** 在"快速融合""处理看板""校验匹配""导出结果"四个页面顶部显示统一的 Ant Steps 组件（上传 → 解析 → 校验 → 导出），高亮当前所在步骤，点击可跳转
- **D-09:** Steps 组件利用 status 属性反馈步骤状态：完成=绿色对号，进行中=蓝色旋转，有警告=橙色感叹号，失败=红色叉号

### Claude's Discretion
- 具体断点数值的微调（1440px 是否需要微调）
- Steps 组件的具体样式调整（水平/垂直、size 大小）
- 错误码映射表的具体条目设计
- 各页面 Table 固定列的具体选择

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 现有前端代码
- `frontend/src/App.tsx` — 路由结构和 RoleRoute 角色守卫，Phase 8 需保留并优化
- `frontend/src/layouts/MainLayout.tsx` — 当前 Ant Layout + Sider + Menu 布局，响应式断点需加在这里
- `frontend/src/layouts/MainLayout.module.css` — 布局样式
- `frontend/src/pages/Workspace.tsx` — HR/Admin 工作台页面
- `frontend/src/pages/SimpleAggregate.tsx` — 快速融合页，Steps 引导条需加在此处
- `frontend/src/pages/Dashboard.tsx` — 处理看板页
- `frontend/src/pages/Results.tsx` — 校验匹配页
- `frontend/src/pages/Exports.tsx` — 导出结果页
- `frontend/src/services/api.ts` — API 客户端，错误拦截中文化需改这里

### 项目要求
- `.planning/REQUIREMENTS.md` — UI-05 到 UI-08 需求定义
- `.planning/ROADMAP.md` — Phase 8 目标和成功标准

### Phase 7 上下文
- `.planning/phases/07-design-system-ui-foundation/07-CONTEXT.md` — 飞书主题、Ant Design 组件规范等已决策内容

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MainLayout.tsx`: 已有 Ant Sider collapsible + buildMenuItems 角色过滤，响应式只需加断点
- `App.tsx`: 已有完整的 RoleRoute + ProtectedRoute 体系，角色路由基本就绪
- `Workspace.tsx`: 已有 admin/hr 两套工作台配置
- `useAuth` hook: 提供 user.role，导航过滤和路由守卫都在消费它
- `useAggregateSession` hook: 聚合进度状态，Steps 引导条可直接读取此状态

### Established Patterns
- Ant Design 5 组件库（Phase 7 引入）
- 飞书蓝 #3370FF 主色、#F5F6F7 背景
- ConfigProvider componentSize="small" 紧凑模式
- React Router v6 路由结构

### Integration Points
- `MainLayout.tsx` — 响应式断点、侧边栏自动折叠逻辑
- `App.tsx ConfigProvider` — 添加 locale={zhCN}
- `services/api.ts` — 错误拦截中文化
- 四个工作流页面（SimpleAggregate/Dashboard/Results/Exports）— Steps 引导条

</code_context>

<specifics>
## Specific Ideas

- Steps 引导条使用 Ant Steps 组件，size="small"，水平排列，与页面标题同行或紧邻其下
- 错误码映射可以用一个 errorMessages.ts 常量文件集中管理
- 侧边栏断点可以用 window.matchMedia 或 Ant Sider 的 breakpoint prop

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-page-rebuild-ux-flow*
*Context gathered: 2026-03-31*
