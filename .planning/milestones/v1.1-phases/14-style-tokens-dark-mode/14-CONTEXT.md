# Phase 14: 样式 Token 化与暗黑模式 - Context

**Gathered:** 2026-04-05
**Status:** Ready for planning

<domain>
## Phase Boundary

将前端约 33 处硬编码内联颜色替换为 Ant Design 主题 token，引入暗黑模式切换能力，偏好持久化到 localStorage。不涉及新功能、不涉及整体设计改版，只做 token 化 + 暗模适配。

</domain>

<decisions>
## Implementation Decisions

### Token 替换策略
- **D-01:** 建立语义色常量模块 `frontend/src/theme/semanticColors.ts`，导出 { BRAND, SUCCESS, ERROR, WARNING, TEXT_TERTIARY, HIGHLIGHT_BG } 等语义名。内部通过 AntD token 提供动态值
- **D-02:** 主接口为 `useSemanticColors()` hook：在组件内调用 `theme.useToken()` 后返回语义色对象，暗模切换时自动重渲染
- **D-03:** Table columns 等组件外的定义位置使用独立的 `chartColors.ts` 模块（常量导出 + `getChartColors(isDark)` 函数版本），防止 hook 限制
- **D-04:** AntD 内置 token 能直接映射的不新建语义色：`#999` → `colorTextTertiary`，`#fafafa/#f5f5f5` → `colorFillQuaternary`，`#F0F5FF` → `colorPrimaryBg`
- **D-05:** 无对应 AntD token 的自定义色（如 `#FFF7E6` 黄色高亮背景）归为语义色常量 `HIGHLIGHT_BG`，内部映射为 `colorWarningBg`
- **D-06:** Card 状态边框色封装为独立 hook `useCardStatusColors()`，返回 { successBorder, errorBorder, warningBorder }，避免多页面重复解包 useSemanticColors
- **D-07:** 跨期对比 (Phase 11) 的差异高亮色直接复用 useSemanticColors：增加=WARNING，减少=ERROR，新增=BRAND

### 暗黑模式切换
- **D-08:** 切换按钮放在 MainLayout Header 右上角用户菜单旁，使用太阳/月亮图标
- **D-09:** 初次加载默认跟随系统偏好，通过 `matchMedia('(prefers-color-scheme: dark)')` 检测
- **D-10:** 用户手动切换后，将选择持久化到 localStorage，覆盖系统偏好
- **D-11:** 切换动画：瞬间切换，不加过渡动画（AntD ConfigProvider 本身是瞬间生效）
- **D-12:** localStorage 键名：`theme-mode`，值为 `'light' | 'dark'`
- **D-13:** FOUC 预防：在 `index.html` <head> 中插入同步脚本，在 React 启动前读取 localStorage 并给 `<html>` 加 `data-theme` 属性

### 暗黑模式下的品牌色
- **D-14:** 使用 AntD `theme.darkAlgorithm` 自动计算暗模版本的主色，无需手动定义新色值
- **D-15:** 语义色（success/warning/error）在暗模下交由 darkAlgorithm 自动适配，不手动调整亢度
- **D-16:** Layout.Sider（侧边栏）始终保持深色（`#1F2329`），亮模和暗模统一，这是飞书风格的标志性特征
- **D-17:** Alert 组件暗模背景采用 AntD darkAlgorithm 的默认深色半透明样式
- **D-18:** Table hover 效果暗模下使用 AntD darkAlgorithm 自动计算

### 自定义组件暗模支持
- **D-19:** Login 页面的 `#F5F6F7` 背景改为 `useSemanticColors().colorBgLayout`（跟随 AntD Layout 主背景，暗模自动变深）
- **D-20:** FeishuFieldMapping 页面的所有硬编码色全部 token 化：`#FFFFFF` → `colorBgContainer`，`#3370FF` → `colorPrimary`，`#1F2329` → `colorText`
- **D-21:** Workspace/Portal 页面的 `#3370FF` 图标色改为 `useSemanticColors().BRAND`，暗模下由 darkAlgorithm 自动提亮

### Claude's Discretion
- useSemanticColors hook 返回对象的具体字段命名
- chartColors 模块的具体导出接口
- useCardStatusColors hook 的实现细节
- index.html FOUC 脚本的具体代码
- 切换按钮的图标选型（@ant-design/icons 中的 SunOutlined/MoonOutlined 或自绘）
- 主题切换后保留的某些遗留色（如 Sider 深色的精细调优）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 主题系统
- `frontend/src/theme/index.ts` — 当前 AntD ThemeConfig 定义（飞书蓝主色 + 扩展 token）
- `frontend/src/main.tsx` — ConfigProvider 当前位置与配置

### 硬编码颜色分布
- `frontend/src/App.tsx` — 登录加载屏背景
- `frontend/src/layouts/MainLayout.tsx` — Header/Content 内联背景
- `frontend/src/pages/Login.tsx` — 全屏背景
- `frontend/src/pages/Dashboard.tsx`, `Employees.tsx`, `ImportBatchDetail.tsx`, `SimpleAggregate.tsx` — Card 状态边框
- `frontend/src/pages/Results.tsx`, `Exports.tsx`, `Mappings.tsx`, `AnomalyDetection.tsx`, `PeriodCompare.tsx` — Statistic valueStyle
- `frontend/src/pages/Compare.tsx`, `PeriodCompare.tsx`, `Imports.tsx`, `SimpleAggregate.tsx` — 内联文字/图标色
- `frontend/src/pages/Workspace.tsx`, `Portal.tsx` — 页面引导图标色
- `frontend/src/pages/FeishuFieldMapping.tsx`, `FeishuSync.tsx` — 飞书页面品牌色 + 高亮背景
- `frontend/src/pages/ApiKeys.tsx` — key 值展示区域背景

### Phase 7 设计基础
- `.planning/phases/07-design-system-ui-foundation/07-CONTEXT.md` — 飞书蓝配色规范、AntD 迁移决策

### 项目要求
- `.planning/REQUIREMENTS.md` — UX-01 (token 化)、UX-02 (暗黑模式持久化) 需求定义
- `.planning/ROADMAP.md` — Phase 14 成功标准

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/theme/index.ts`: 当前 ThemeConfig 已经完整配置飞书蓝 token，增加 darkAlgorithm 即可切换暗模
- `frontend/src/main.tsx`: 已有 ConfigProvider 封装，新增 algorithm 参数绑定 state 即可
- `theme.useToken()`: AntD 官方 hook，暗模切换时自动返回新 token 值

### Established Patterns
- Ant Design 5 主题 token 系统已全局应用
- 全局用 ConfigProvider 包裹 (main.tsx)
- React Context 管理全局状态（AuthProvider 已存在）
- useSearchParams 做 URL 状态持久化（DataManagement 已用）

### Integration Points
- `main.tsx`: ConfigProvider 需要接受动态 theme prop
- `MainLayout.tsx`: Header 右上角用户菜单区域添加切换按钮
- `index.html`: 新增 <head> 同步脚本防 FOUC
- 33+ 个硬编码颜色位置分布在 20+ 个文件，需逐一替换

</code_context>

<specifics>
## Specific Ideas

- 飞书 Lark 后台管理自身就是亮模主调的产品，Sider 始终深色是产品身份
- Linear/Notion 的暗模切换按钮在顶部导航栏，瞬间切换无动画
- AntD 5 的 darkAlgorithm 已经在飞书蓝这类中等饱和度主色上有良好表现

</specifics>

<deferred>
## Deferred Ideas

- 用户可自定义主题色 — 未来独立 phase
- 跟随系统偏好的实时响应（系统切换时 app 跟随） — 可选，当前只在初次加载时检测
- 更细粒度的颜色偏好（如对比度调节） — 未来无障碍 phase

</deferred>

---

*Phase: 14-style-tokens-dark-mode*
*Context gathered: 2026-04-05*
