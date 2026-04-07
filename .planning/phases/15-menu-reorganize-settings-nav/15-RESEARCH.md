# Phase 15: 菜单重组与设置导航 - Research

**Researched:** 2026-04-07
**Domain:** Ant Design Menu 多级分组 + React 前端设置页
**Confidence:** HIGH

## Summary

Phase 15 将当前 MainLayout.tsx 中扁平排列的 14+ 个菜单项重组为三个分组（常用、数据分析、管理），快速融合置顶，并新建 /settings 统一设置页。核心技术全部在已有依赖范围内：Ant Design 5 的 Menu 组件原生支持 SubMenu 分组、openKeys 受控模式；localStorage 持久化已有 Phase 14 的 `theme-mode` 模式可参考。

技术风险极低。主要工作量在于：(1) 重构 `ALL_NAV_ITEMS` 和 `buildMenuItems` 以支持分组结构；(2) 实现 openKeys 持久化 hook；(3) 新建 SettingsPage 组件含搜索过滤功能；(4) 在 App.tsx 添加 /settings 路由。无需引入任何新依赖。

**Primary recommendation:** 使用 Ant Design Menu 的 `children` 属性构建 SubMenu 分组，通过 `openKeys` + `onOpenChange` 受控模式配合 localStorage 实现折叠状态持久化。设置页使用 Ant Design Card + Input.Search 实现纯前端搜索过滤。

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** 按使用频率分为三组：「常用」「数据分析」「管理」
- **D-02:** 「快速融合」独立置顶，不归入任何分组，始终可见一键直达
- **D-03:** 常用组包含：处理看板、批次管理、校验匹配、导出结果
- **D-04:** 数据分析组包含：月度对比、跨期对比、异常检测、映射修正
- **D-05:** 管理组包含：员工主档、数据管理、审计日志、API 密钥、飞书同步/设置
- **D-06:** 「常用」组默认展开，「数据分析」和「管理」组默认折叠
- **D-07:** 新建单页 /settings 路由，用卡片分区显示各类设置
- **D-08:** 设置页顶部搜索框，输入关键词后隐藏不匹配卡片，匹配卡片高亮关键词
- **D-09:** 审计日志、API 密钥、飞书设置仍保留独立页面，设置页中对应卡片提供「前往」链接
- **D-10:** localStorage 持久化菜单展开状态，键名 `menu-open-keys`
- **D-11:** 刷新或跨页面导航时从 localStorage 恢复展开状态

### Claude's Discretion
- 设置页卡片的具体排列顺序和视觉样式
- 搜索高亮的具体动画效果
- 员工角色的菜单是否需要分组（当前只有一个「员工查询」）

### Deferred Ideas (OUT OF SCOPE)
None
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UX-04 | 左侧菜单多级折叠（低频功能收进子菜单） | Ant Design Menu SubMenu 分组 + openKeys 受控模式 + localStorage 持久化 |
| UX-05 | 设置页支持搜索并快速导航到对应设置项 | 新建 /settings 页面 + Card 分区 + Input.Search 过滤 + 关键词高亮 |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- 零新依赖策略 -- AntD 5 内置暗黑模式/响应式/多级菜单 [VERIFIED: STATE.md]
- React 前端 + FastAPI 后端架构
- 前端命令：`npm run lint`, `npm run build`, `npm run dev`
- 本阶段纯前端，不涉及后端

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| antd | ^5.29.3 | Menu SubMenu 分组、Card、Input.Search | 已在项目中使用，原生支持多级菜单 [VERIFIED: package.json] |
| react | ^18.3.1 | UI 框架 | 已在项目中使用 [VERIFIED: package.json] |
| react-router-dom | (已有) | /settings 路由 | 已在项目中使用 [VERIFIED: App.tsx imports] |

### Supporting
无需额外依赖。所有功能通过已有的 Ant Design 组件和浏览器 localStorage API 实现。

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| AntD Menu SubMenu | Menu ItemGroup (`type: 'group'`) | ItemGroup 没有折叠能力，不满足 UX-04 |
| localStorage | sessionStorage | sessionStorage 关闭标签页就丢失，不满足 D-11 |

## Architecture Patterns

### Recommended Project Structure
```
frontend/src/
├── layouts/
│   └── MainLayout.tsx          # 修改：菜单分组 + openKeys 持久化
├── hooks/
│   └── useMenuOpenKeys.ts      # 新建：菜单展开状态持久化 hook
├── pages/
│   └── Settings.tsx            # 新建：统一设置页
└── App.tsx                     # 修改：添加 /settings 路由
```

### Pattern 1: SubMenu 分组菜单结构
**What:** 使用 Ant Design Menu 的 `children` 属性构建嵌套分组，每个分组是一个 SubMenu 节点
**When to use:** 菜单项超过 8 个且有明确分类时
**Example:**
```typescript
// Source: Ant Design Menu docs - items 属性
// [VERIFIED: antd 5.x Menu API 使用 items 数组而非 JSX children]
const menuItems: MenuProps['items'] = [
  // 快速融合 - 置顶独立项
  {
    key: '/aggregate',
    icon: <UploadOutlined />,
    label: '快速融合',
  },
  // 常用分组 - SubMenu
  {
    key: 'group-common',
    icon: <AppstoreOutlined />,
    label: '常用',
    children: [
      { key: '/dashboard', icon: <DashboardOutlined />, label: '处理看板' },
      { key: '/imports', icon: <ImportOutlined />, label: '批次管理' },
      { key: '/results', icon: <CheckCircleOutlined />, label: '校验匹配' },
      { key: '/exports', icon: <ExportOutlined />, label: '导出结果' },
    ],
  },
  // 更多分组...
];
```

### Pattern 2: openKeys 受控模式 + localStorage 持久化
**What:** 通过 `openKeys` 和 `onOpenChange` 控制 SubMenu 展开状态，变化时写入 localStorage
**When to use:** 需要菜单展开状态跨页面导航和刷新保持时
**Example:**
```typescript
// 参考 ThemeModeProvider 的 localStorage 读写模式
const STORAGE_KEY = 'menu-open-keys';
const DEFAULT_OPEN_KEYS = ['group-common']; // D-06: 常用组默认展开

function useMenuOpenKeys() {
  const [openKeys, setOpenKeys] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) return JSON.parse(saved);
    } catch { /* ignore */ }
    return DEFAULT_OPEN_KEYS;
  });

  const handleOpenChange = useCallback((keys: string[]) => {
    setOpenKeys(keys);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(keys));
    } catch { /* ignore */ }
  }, []);

  return { openKeys, onOpenChange: handleOpenChange };
}
```

### Pattern 3: 设置页搜索过滤
**What:** 使用 Input.Search + 状态过滤渲染卡片列表，匹配项高亮关键词
**When to use:** 设置项超过 5 类需要快速定位时
**Example:**
```typescript
// 设置页卡片数据结构
interface SettingsSection {
  key: string;
  title: string;
  description: string;
  keywords: string[];  // 搜索匹配用
  link?: string;       // 「前往」跳转链接（如审计日志、API 密钥）
  content?: React.ReactNode;  // 内联设置内容
}

// 搜索过滤逻辑
const filtered = sections.filter(s =>
  !searchTerm ||
  s.title.includes(searchTerm) ||
  s.description.includes(searchTerm) ||
  s.keywords.some(k => k.includes(searchTerm))
);
```

### Pattern 4: 关键词高亮
**What:** 在搜索结果中将匹配的关键词文本用标记包裹高亮显示
**Example:**
```typescript
// 使用 antd Typography.Text mark 属性或自定义 <mark> 标签
function highlightText(text: string, keyword: string): React.ReactNode {
  if (!keyword) return text;
  const index = text.toLowerCase().indexOf(keyword.toLowerCase());
  if (index === -1) return text;
  return (
    <>
      {text.slice(0, index)}
      <mark style={{ background: token.colorWarningBg, padding: 0 }}>
        {text.slice(index, index + keyword.length)}
      </mark>
      {text.slice(index + keyword.length)}
    </>
  );
}
```

### Anti-Patterns to Avoid
- **使用 `type: 'group'` 代替 SubMenu:** ItemGroup 只是视觉分组标题，不支持折叠/展开，无法满足 UX-04 [VERIFIED: AntD docs - ItemGroup 无 collapsible 能力]
- **在 collapsed 模式下保留 SubMenu 层级:** 侧边栏收缩时 SubMenu 需要变为弹出菜单(popup)，AntD 已自动处理此行为，不要手动干预 [ASSUMED]
- **硬编码菜单项到 JSX:** 保持 `items` 数据驱动模式，便于角色过滤和动态添加飞书菜单项

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SubMenu 折叠/展开 | 自定义折叠动画和状态 | AntD Menu `openKeys` + `onOpenChange` | AntD 已处理动画、键盘导航、collapsed 弹出 |
| 搜索高亮 | 正则替换 dangerouslySetInnerHTML | React 节点拼接 + `<mark>` 标签 | 避免 XSS 风险 |
| 菜单 collapsed 弹出 | 自定义 Popover 弹出菜单 | AntD Sider + Menu `mode="inline"` | collapsed 时 SubMenu 自动变为 popup，已内置 |

## Common Pitfalls

### Pitfall 1: openKeys 与 selectedKeys 混淆
**What goes wrong:** 设置了 `openKeys` 但忘了同步 `selectedKeys`，导致菜单项选中状态和展开状态不一致
**Why it happens:** `openKeys` 控制哪些 SubMenu 展开，`selectedKeys` 控制哪个菜单项高亮，两者独立
**How to avoid:** `selectedKeys` 继续使用 `location.pathname`（已有逻辑），`openKeys` 用新 hook 管理
**Warning signs:** 点击菜单项后高亮位置不对，或展开了错误的分组

### Pitfall 2: Sider collapsed 时 openKeys 被忽略
**What goes wrong:** Sider 收缩后设置 openKeys 无效，展开后 openKeys 状态丢失
**Why it happens:** AntD Menu 在 `inline` 模式下才使用 `openKeys`；collapsed 时自动变为 popup 模式
**How to avoid:** 不需要特殊处理。collapsed 时 openKeys 被 AntD 忽略但 React state 仍保留，展开后自动恢复 [ASSUMED]
**Warning signs:** 收缩再展开后所有分组都折叠了

### Pitfall 3: 飞书菜单项的动态插入
**What goes wrong:** 飞书功能开关打开后，飞书同步/设置菜单项需要正确插入到「管理」分组
**Why it happens:** 当前 `dynamicNavItems` 通过 push 追加到扁平数组末尾，新的分组结构需要把它们插入到正确的 SubMenu children 中
**How to avoid:** 在 `buildMenuItems` 重构时，管理组的 children 构建逻辑中根据 `feishu_sync_enabled` 条件插入飞书菜单项
**Warning signs:** 飞书菜单项出现在分组外部或错误分组中

### Pitfall 4: 员工角色只有一个菜单项
**What goes wrong:** 员工角色 (`employee`) 只有「员工查询」一个菜单项，如果也套上分组会显得多余
**Why it happens:** 分组逻辑统一应用到所有角色
**How to avoid:** 员工角色不分组，直接显示单个菜单项（Claude's Discretion 已允许）
**Warning signs:** 员工看到一个只有一项的分组

### Pitfall 5: localStorage JSON 解析失败
**What goes wrong:** localStorage 中存储的 `menu-open-keys` 被手动篡改为非法 JSON，导致解析崩溃
**Why it happens:** try/catch 缺失或不完整
**How to avoid:** 参考 ThemeModeProvider 模式，读取 localStorage 时始终 try/catch，解析失败回退到默认值
**Warning signs:** 控制台报 JSON.parse 错误

## Code Examples

### 完整的菜单分组数据结构

```typescript
// Source: 基于 CONTEXT.md D-01 到 D-06 的决策 + AntD Menu items API
import type { MenuProps } from 'antd';

type MenuItem = Required<MenuProps>['items'][number];

interface MenuGroupConfig {
  key: string;
  label: string;
  icon: React.ReactNode;
  children: NavItem[];
  defaultOpen: boolean;
}

const MENU_GROUPS: MenuGroupConfig[] = [
  {
    key: 'group-common',
    label: '常用',
    icon: <AppstoreOutlined />,
    defaultOpen: true,  // D-06
    children: [
      { key: '/dashboard', icon: <DashboardOutlined />, label: '处理看板', roles: ['admin', 'hr'] },
      { key: '/imports', icon: <ImportOutlined />, label: '批次管理', roles: ['admin', 'hr'] },
      { key: '/results', icon: <CheckCircleOutlined />, label: '校验匹配', roles: ['admin', 'hr'] },
      { key: '/exports', icon: <ExportOutlined />, label: '导出结果', roles: ['admin', 'hr'] },
    ],
  },
  {
    key: 'group-analysis',
    label: '数据分析',
    icon: <BarChartOutlined />,
    defaultOpen: false,  // D-06
    children: [
      { key: '/compare', icon: <SwapOutlined />, label: '月度对比', roles: ['admin', 'hr'] },
      { key: '/period-compare', icon: <SwapOutlined />, label: '跨期对比', roles: ['admin', 'hr'] },
      { key: '/anomaly-detection', icon: <AlertOutlined />, label: '异常检测', roles: ['admin', 'hr'] },
      { key: '/mappings', icon: <ToolOutlined />, label: '映射修正', roles: ['admin', 'hr'] },
    ],
  },
  {
    key: 'group-admin',
    label: '管理',
    icon: <SettingOutlined />,
    defaultOpen: false,  // D-06
    children: [
      { key: '/employees', icon: <TeamOutlined />, label: '员工主档', roles: ['admin', 'hr'] },
      { key: '/data-management', icon: <DatabaseOutlined />, label: '数据管理', roles: ['admin', 'hr'] },
      { key: '/audit-logs', icon: <AuditOutlined />, label: '审计日志', roles: ['admin'] },
      { key: '/api-keys', icon: <KeyOutlined />, label: 'API 密钥', roles: ['admin'] },
      // 飞书菜单项在此条件插入
    ],
  },
];

// 置顶独立项 (D-02)
const TOP_ITEM: NavItem = { key: '/aggregate', icon: <UploadOutlined />, label: '快速融合', roles: ['admin', 'hr'] };
```

### useMenuOpenKeys Hook

```typescript
// frontend/src/hooks/useMenuOpenKeys.ts
import { useState, useCallback } from 'react';

const STORAGE_KEY = 'menu-open-keys';

export function useMenuOpenKeys(defaultKeys: string[]) {
  const [openKeys, setOpenKeys] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) return parsed;
      }
    } catch { /* fallback to default */ }
    return defaultKeys;
  });

  const handleOpenChange = useCallback((keys: string[]) => {
    setOpenKeys(keys);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(keys));
    } catch { /* Safari private mode */ }
  }, []);

  return { openKeys, onOpenChange: handleOpenChange };
}
```

### 设置页卡片搜索

```typescript
// frontend/src/pages/Settings.tsx
import { useState, useMemo } from 'react';
import { Input, Card, Row, Col, Typography, Button } from 'antd';
import { Link } from 'react-router-dom';

const { Search } = Input;

interface SettingsCard {
  key: string;
  title: string;
  description: string;
  keywords: string[];
  linkTo?: string;  // 「前往」跳转
}

const SETTINGS_CARDS: SettingsCard[] = [
  { key: 'audit', title: '审计日志', description: '查看系统操作记录', keywords: ['日志', '审计', '操作记录'], linkTo: '/audit-logs' },
  { key: 'api-keys', title: 'API 密钥', description: '管理 DeepSeek 等 API 密钥', keywords: ['密钥', 'API', 'DeepSeek'], linkTo: '/api-keys' },
  { key: 'feishu', title: '飞书集成', description: '飞书同步和文档映射配置', keywords: ['飞书', '同步', '集成'], linkTo: '/feishu-settings' },
  // 更多卡片...
];
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| AntD Menu JSX children (`<Menu.Item>`, `<SubMenu>`) | `items` prop 数据驱动 | AntD 4.20+ (2022) | 已在项目中使用 items 模式 [VERIFIED: MainLayout.tsx] |
| 手动实现暗黑模式 SubMenu 样式 | `theme="dark"` + AntD 5 token 系统 | AntD 5.0 (2023) | 已在项目中使用 [VERIFIED: MainLayout.tsx] |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | AntD Menu collapsed 时 openKeys state 仍保留，展开后自动恢复 | Pitfall 2 | 需要手动在 onCollapse 时保存/恢复 openKeys — 低风险，容易修复 |
| A2 | AntD Menu SubMenu 在 Sider collapsed 时自动变为 popup 模式 | Don't Hand-Roll | 如果不自动变为 popup 需要手动处理 — 低风险，AntD 文档描述此行为 |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | 无前端测试框架安装 |
| Config file | 不存在 |
| Quick run command | N/A |
| Full suite command | `npm run lint && npm run build` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UX-04 | 菜单按分组折叠/展开，状态持久化 | manual | `npm run build` (编译通过) | N/A |
| UX-05 | 设置页搜索过滤卡片 | manual | `npm run build` (编译通过) | N/A |

### Sampling Rate
- **Per task commit:** `npm run lint && npm run build`
- **Per wave merge:** `npm run lint && npm run build`
- **Phase gate:** lint + build 通过 + 手动验证菜单分组和设置页搜索

### Wave 0 Gaps
None -- 无前端测试框架，本阶段不引入（零新依赖策略）。依赖 lint + build + 手动验证。

## Security Domain

本阶段为纯前端 UI 重组，不涉及认证、授权变更、数据传输或加密。现有的角色权限过滤（`roles` 字段）在 `buildMenuItems` 中已有，重构后保持不变。

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A |
| V3 Session Management | no | N/A |
| V4 Access Control | yes (保持) | 现有 `roles` 过滤在菜单分组重构后必须保留 |
| V5 Input Validation | no | 搜索框为纯前端过滤，不发送请求 |
| V6 Cryptography | no | N/A |

### Known Threat Patterns
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| 角色过滤遗漏导致越权菜单可见 | Elevation of Privilege | 重构 buildMenuItems 时保持 roles 过滤逻辑，admin-only 项不暴露给 hr/employee |

## Sources

### Primary (HIGH confidence)
- `frontend/src/layouts/MainLayout.tsx` — 当前菜单定义和构建逻辑 [VERIFIED: 直接阅读源码]
- `frontend/src/theme/ThemeModeProvider.tsx` — localStorage 持久化模式参考 [VERIFIED: 直接阅读源码]
- `frontend/src/App.tsx` — 当前路由结构 [VERIFIED: 直接阅读源码]
- `frontend/package.json` — antd ^5.29.3, react ^18.3.1 [VERIFIED: 直接阅读]

### Secondary (MEDIUM confidence)
- Ant Design Menu SubMenu / openKeys API — 基于 AntD 5.x 官方文档记忆 [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - 全部使用已有依赖，无新引入
- Architecture: HIGH - 修改范围清晰（MainLayout + 新 Settings 页 + 新 hook + App.tsx 路由）
- Pitfalls: HIGH - 基于直接阅读当前代码发现的具体问题

**Research date:** 2026-04-07
**Valid until:** 2026-05-07 (稳定的 UI 重组，不受版本更新影响)
