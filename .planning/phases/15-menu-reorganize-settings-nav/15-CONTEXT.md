# Phase 15: 菜单重组与设置导航 - Context

**Gathered:** 2026-04-07
**Status:** Ready for planning

<domain>
## Phase Boundary

将当前 MainLayout.tsx 中扁平排列的 14 个菜单项重组为多级分组结构，低频功能收入子菜单。新增统一设置页，支持搜索框快速定位设置项。菜单折叠状态跨页面导航和刷新保持。

</domain>

<decisions>
## Implementation Decisions

### 菜单分组方案
- **D-01:** 按使用频率分为三组：「常用」「数据分析」「管理」
- **D-02:** 「快速融合」独立置顶，不归入任何分组，始终可见一键直达
- **D-03:** 常用组包含：处理看板、批次管理、校验匹配、导出结果
- **D-04:** 数据分析组包含：月度对比、跨期对比、异常检测、映射修正
- **D-05:** 管理组包含：员工主档、数据管理、审计日志、API 密钥、飞书同步/设置
- **D-06:** 「常用」组默认展开，「数据分析」和「管理」组默认折叠

### 设置页
- **D-07:** 新建单页 /settings 路由，用卡片分区显示各类设置（账号安全、飞书集成、API 密钥、系统日志等）
- **D-08:** 设置页顶部放置搜索框，输入关键词后隐藏不匹配的卡片，匹配的卡片高亮关键词，清空搜索恢复全部
- **D-09:** 审计日志、API 密钥、飞书设置仍保留各自独立页面，设置页中对应卡片提供「前往」链接跳转

### 折叠状态持久化
- **D-10:** 菜单分组展开/折叠状态使用 localStorage 持久化，键名 `menu-open-keys`，与 Phase 14 的 `theme-mode` 保持一致的存储策略
- **D-11:** 刷新页面或跨页面导航时从 localStorage 恢复展开状态

### Claude's Discretion
- 设置页卡片的具体排列顺序和视觉样式
- 搜索高亮的具体动画效果
- 员工角色（employee）的菜单是否需要分组（当前只有一个「员工查询」）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in decisions above

### Key source files
- `frontend/src/layouts/MainLayout.tsx` — 当前菜单定义（ALL_NAV_ITEMS + buildMenuItems），Sider 和 Header 布局
- `frontend/src/theme/useThemeMode.ts` — localStorage 持久化模式参考（theme-mode 键）

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MainLayout.tsx:ALL_NAV_ITEMS` — 已有的 14 项菜单定义，包含 key/icon/label/roles
- `MainLayout.tsx:buildMenuItems` — 按角色过滤菜单的函数，需要扩展为支持分组
- Ant Design `Menu` 组件已在使用，原生支持 `type: 'group'` 和 `children` 子菜单
- `useThemeMode` hook — localStorage 读写模式可参考

### Established Patterns
- Phase 14 的 localStorage 持久化模式：键名简短、ThemeModeProvider 在 mount 时读取
- Ant Design `Menu` 的 `openKeys` / `onOpenChange` 控制分组展开

### Integration Points
- `MainLayout.tsx` 是唯一需要修改菜单的文件
- `App.tsx` 需要添加 /settings 路由
- 设置页是新页面，不影响现有页面

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

*Phase: 15-menu-reorganize-settings-nav*
*Context gathered: 2026-04-07*
