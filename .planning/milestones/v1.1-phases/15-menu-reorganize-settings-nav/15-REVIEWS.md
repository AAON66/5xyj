---
phase: 15
reviewers: [codex]
reviewed_at: 2026-04-07T18:30:00+08:00
plans_reviewed: [15-01-PLAN.md, 15-02-PLAN.md]
---

# Cross-AI Plan Review — Phase 15

## Codex Review

### Plan 15-01: 菜单分组重构 + `openKeys` 持久化

#### Summary
方向是对的，且和 D-01 到 D-06 基本一致。把扁平菜单改成分组菜单，再补 `openKeys` 持久化，确实能解决"低频功能干扰日常操作"的核心问题。不过这份计划还漏了几个真正影响可用性的细节，尤其是"当前路由如何映射到菜单选中项"和"分组展开状态如何与侧栏折叠状态共存"。

#### Strengths
- 分波次拆分合理，先做导航骨架，再做 `/settings`，依赖顺序正确。
- `TOP_ITEM` 独立置顶，符合 D-02。
- 角色过滤和飞书开关都被纳入菜单构建逻辑，方向正确。
- `localStorage` 持久化 `openKeys` 能直接覆盖 D-10、D-11。
- 员工角色保持单入口，避免无意义分组，设计上是克制的。

#### Concerns
- **HIGH**: 计划没有处理"路由到菜单 key 的归一化"。当前菜单是直接用 `location.pathname` 作为 `selectedKeys`，而现有路由里有 `/imports/:batchId`、`/employees/new`、`/feishu-mapping/:configId` 这类子路由；如果不加 `resolveSelectedMenuKey`，这些页面进入后不会高亮父菜单，甚至可能让所属分组保持收起。
- **MEDIUM**: `openKeys` 是受控状态后，必须和当前 `Sider` 的响应式折叠逻辑兼容；否则窗口缩放或手动收起时，可能把用户展开状态冲掉，或者展开后恢复异常。
- **MEDIUM**: 计划只提了 `JSON.parse` 容错，没有明确提 `localStorage` 可用性和写入异常处理。项目现有本地存储访问已经有防御式写法，新 hook 最好保持同一标准。
- **LOW**: `menu-open-keys` 是全局 key，若同一浏览器先后切换 `admin/hr/employee`，或者飞书开关变化，旧值可能包含无效分组。计划里没有说明"按可见 group keys 做清洗"。

#### Suggestions
- 增加一个纯函数，显式把详情页路由映射回菜单父项，例如 `/imports/:batchId -> /imports`、`/employees/new -> /employees`。
- 将"持久化的 `openKeys`"和"当前路由必须展开的祖先 group"分开处理；不要让已访问页面藏在收起组里。
- 在 `useMenuOpenKeys` 里复用现有项目的本地存储防御模式，至少覆盖 `window` 不存在、读取失败、写入失败、非法数组值。
- Wave 1 就把菜单配置抽到独立模块，而不是继续堆在 MainLayout.tsx 里；这样 Wave 2 只增量加 `/settings`，不会再次重改布局文件。
- 补一组最少验证用例：首次加载默认展开、刷新后恢复、窗口折叠后恢复、角色切换、详情页高亮父菜单。

#### Risk Assessment
**MEDIUM**。主方向没有问题，但如果不补"子路由选中态"和"折叠状态协同"这两个点，菜单看起来会完成，实际导航体验仍然会有明显割裂。

---

### Plan 15-02: 统一设置页 + 路由注册 + 菜单入口

#### Summary
这份计划覆盖了 `/settings` 的主体结构，也考虑了角色过滤、独立页面跳转和飞书 feature flag，整体可落地。但它对 UX-05 的实现还不够精确: "搜索并快速导航到对应设置项" 现在更像"搜索并过滤卡片"。如果不补一个明确的导航动作，这个计划只能算部分达标。

#### Strengths
- 新增 `/settings` 路由并保留审计/API Key/飞书独立页面，符合 D-07、D-09。
- 搜索范围覆盖标题、描述、关键词，足够轻量，不会过度设计。
- `highlightText` 避开 `dangerouslySetInnerHTML`，XSS 风险控制得当。
- 角色过滤和 `RoleRoute` 双层保护是正确的。
- 飞书卡片受 feature flag 控制，和现有实现一致。

#### Concerns
- **HIGH**: 计划没有定义"导航"本身。过滤卡片和高亮关键词，不等于"快速定位并导航到对应设置项"；尤其对同页设置项，仍然需要用户自己扫卡片。这个点直接影响 Success Criteria 3。
- **MEDIUM**: 计划写"Menu entry in MainLayout admin group"，但路由又给了 `admin/hr`。如果这里指的是 admin-only 暴露，HR 会出现"有权限访问但菜单不可发现"的问题；如果指的是"管理组"，那需要写清楚。
- **MEDIUM**: `theme` 和 `account` 卡片有一点范围膨胀。当前顶部已经有主题切换，MainLayout.tsx 里也没有现成的 account route；如果这两张卡片只是占位，会稀释 Phase 15 的主目标。
- **LOW**: `highlightText` 如果用正则切分，必须转义特殊字符；否则 `(`、`+`、`[` 这类查询容易出现错误匹配或渲染异常。
- **LOW**: 计划没提 breadcrumb 文案和菜单标签映射；新增 `/settings` 后，最好同步补 `LABEL_MAP`，否则会退化成原始 segment 文本。

#### Suggestions
- 把"搜索"改成"搜索 + 明确导航"。最小实现可以是：搜索后自动滚动到首个匹配卡片，并给卡片聚焦/描边；独立页面卡片则保留"前往"按钮。
- 先按"真实存在的设置面"建卡片，避免为 `account` 这种尚无落点的内容引入占位设计。
- 明确 `/settings` 菜单入口属于共享的"管理"分组，而不是 admin-only 可见。
- 将搜索匹配和高亮逻辑抽成纯函数，至少覆盖空字符串、大小写、特殊字符、多个关键词、无结果五类场景。
- 把设置卡片元数据单独放到 config 中，角色、关键词、目标路由都从一处读取，避免页面渲染逻辑和权限逻辑分叉。

#### Risk Assessment
**MEDIUM**。页面框架本身不复杂，但如果不补足"真正的导航行为"并收紧范围，这个计划很容易做成一个可展示但不完全满足 UX-05 的设置目录页。

---

## Consensus Summary

> Only one external reviewer (Codex) was available. Consensus analysis requires 2+ reviewers.
> Below is a single-reviewer summary.

### Key Concerns (from Codex)

1. **子路由选中态缺失 (HIGH)** — `/imports/:batchId` 等详情页无法高亮父菜单项，导致导航割裂
2. **"导航"行为未定义 (HIGH)** — 设置页搜索只做了过滤和高亮，缺少自动滚动/聚焦等真正的导航动作
3. **Sider 折叠与 openKeys 协同 (MEDIUM)** — 响应式折叠可能冲掉用户的展开状态
4. **菜单入口角色可见性模糊 (MEDIUM)** — /settings 菜单项应明确对 admin 和 hr 都可见
5. **占位卡片范围膨胀 (MEDIUM)** — account 卡片无落点，theme 卡片与已有顶栏切换重复

### Suggested Improvements
- 新增 `resolveSelectedMenuKey` 函数处理子路由映射
- 搜索结果自动滚动到首个匹配卡片
- 收紧设置卡片范围，只保留有实际落点的卡片
- 同步补 LABEL_MAP 面包屑映射
- highlightText 对正则特殊字符做转义

### Divergent Views
N/A — 单一评审者
