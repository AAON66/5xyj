# Phase 7: Design System & UI Foundation - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

将现有所有页面从手写 CSS 迁移到 Ant Design 5.x 组件库，建立飞书风格的视觉主题（卡片化布局、专业配色、流畅动画）。所有 11 个页面一次性重写，不做渐进式迁移。

</domain>

<decisions>
## Implementation Decisions

### 迁移策略
- **D-01:** 一次性重写所有页面，不做渐进式迁移，避免新旧混合的视觉不一致
- **D-02:** 现有渐变背景和网格纹理效果全部替换为飞书风格的纯净浅灰背景

### 布局与导航
- **D-03:** 使用 Ant Design Layout + Sider + Menu 替换现有自定义侧边栏
- **D-04:** 侧边栏支持折叠功能（折叠后只显示图标），飞书标配行为
- **D-05:** 页面顶部增加 Header 栏，显示面包屑导航 + 右侧用户头像/登出

### 视觉风格
- **D-06:** 飞书蓝系配色方案——主色 #3370FF（飞书品牌蓝），背景 #F5F6F7 浅灰，卡片纯白
- **D-07:** 紧凑高效的信息密度——小卡片边距、表格行高较小、信息密度高，适合数据密集型后台系统

### 动画与交互
- **D-08:** 页面切换时内容区域做轻微淡入淡出（fade + 微小位移），不导致整页重载感
- **D-09:** 表格和卡片加载时使用 Ant Skeleton 骨架屏，渐变为实际内容

### 图标与空状态
- **D-10:** 使用 @ant-design/icons 官方图标库（outlined/filled/twotone 三种风格）
- **D-11:** 空状态页面使用 Ant Empty 组件自带插图

### 表格组件
- **D-12:** 统一使用 Ant Table（size='small' 紧凑模式），自带排序/筛选/分页/加载状态

### 消息反馈
- **D-13:** 操作成功/失败用 Ant message（顶部轻提示），重要通知用 Ant notification（右上角卡片）
- **D-14:** 替换现有 GlobalFeedback 自定义组件

### 表单组件
- **D-15:** 统一使用 Ant Form + Form.Item + Input/Select/DatePicker，自带校验、布局、错误提示

### 文件上传
- **D-16:** 用 Ant Upload.Dragger 替换现有自定义拖拽上传区域

### 弹窗组件
- **D-17:** 确认/警告弹窗用 Ant Modal，复杂表单编辑（如员工编辑）用 Ant Drawer。飞书标配模式

### Claude's Discretion
- Ant Design ConfigProvider theme token 的具体数值调优
- 各页面具体的 Ant 组件选型细节（如 Statistic、Descriptions、Tag 等）
- CSS-in-JS vs CSS Modules 的样式方案选择
- 响应式断点的具体设置

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 现有前端代码
- `frontend/src/components/AppShell.tsx` — 现有侧边栏导航结构，迁移时需保留导航项和角色过滤逻辑
- `frontend/src/components/PageContainer.tsx` — 现有页面容器组件，需被 Ant Layout Content 替换
- `frontend/src/components/SectionState.tsx` — 现有加载/空/错误状态组件，需被 Skeleton/Empty/Result 替换
- `frontend/src/components/GlobalFeedback.tsx` — 现有消息反馈组件，需被 Ant message/notification 替换
- `frontend/src/styles.css` — 现有全局样式，需全面重写
- `frontend/src/App.tsx` — 路由结构和角色守卫，迁移时需保留逻辑

### 项目要求
- `.planning/REQUIREMENTS.md` — UI-01 到 UI-04 需求定义
- `.planning/ROADMAP.md` — Phase 7 目标和成功标准

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `AppShell.tsx`: 导航项列表和角色过滤逻辑（roles 数组属性）可直接迁移到 Ant Menu items
- `useAuth` hook: 认证状态管理，布局组件继续使用
- `services/*.ts`: 所有 API 客户端函数无需修改，只改页面层
- `ApiFeedbackProvider`: 需评估是否可以直接替换为 Ant App.useApp() 提供的 message/notification

### Established Patterns
- React Router v6 路由结构（Routes/Route/Navigate）
- useSearchParams URL 状态持久化（DataManagement 页面）
- useEffect + let active = true 清理模式
- services/ 目录下的 API 客户端函数（axios + apiClient 封装）

### Integration Points
- `App.tsx` 路由注册 — 所有页面组件的导入位置
- `AppShell.tsx` 导航菜单 — 角色过滤逻辑需迁移
- `AuthProvider` — 认证上下文不变，布局组件消费
- `frontend/package.json` — 需添加 antd、@ant-design/icons 依赖

</code_context>

<specifics>
## Specific Ideas

- 飞书蓝 #3370FF 作为主色调，参考飞书后台管理界面的整体气质
- 紧凑模式（Ant ConfigProvider componentSize="small"）贯穿全局
- 侧边栏折叠时只显示图标，展开时显示图标+文字

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-design-system-ui-foundation*
*Context gathered: 2026-03-30*
