# Feature Landscape

**Domain:** 社保公积金管理系统 v1.1 体验优化与功能完善
**Researched:** 2026-04-04
**Scope:** v1.1 新增功能特性研究（v1.0 基线功能已全部实现）

## Table Stakes

v1.1 版本中，用户会直接期望的能力。缺失 = 产品体验不完整。

| Feature | Why Expected | Complexity | Dependencies | Notes |
|---------|--------------|------------|--------------|-------|
| 全页面响应式自适应 | 用户在不同窗口尺寸和移动端使用 Web 应用已成为基本预期；v1.0 MainLayout 已有 useResponsiveCollapse 但数据表格在小屏仍体验差 | Medium | 现有 MainLayout + 各页面 Ant Design Table 逐一适配 | AntD Table 原生支持 `scroll.x`、`fixed` 列、`responsive` 列隐藏（HIGH confidence，官方文档） |
| 暗黑模式切换 | 内部管理工具经常低光环境长时间使用，暗黑模式在 2025+ 是基本预期 | Low-Med | 现有 theme/index.ts 定义了完整的 light token 集 | AntD 5 内置 `theme.darkAlgorithm` 运行时切换，无需额外 CSS 文件（HIGH confidence） |
| 账号管理系统前端 | 管理员需要创建/编辑用户、修改角色和重置密码；后端 `/api/v1/users` 全部 CRUD + password reset 已就绪但无前端页面 | Low-Med | 后端 users.py 已有 create/list/get/update/reset_password 五个端点 | 标准 Table + Modal 表单模式，后端零改动 |
| 左侧菜单多级折叠 | 当前 ALL_NAV_ITEMS 有 14+ 个菜单项全部平铺，低频功能（飞书设置、API 密钥、审计日志）淹没在列表中导致导航效率低 | Low | 现有 MainLayout 侧边栏 buildMenuItems | 使用 AntD Menu 的 SubMenu children 嵌套分组（HIGH confidence） |
| 数据管理筛选多选 | 当前 DataManagement 的 Select 筛选只支持单选，用户需要同时查看多个地区或公司 | Low | 现有 DataManagementPage + 后端 filter_options | 将 Select 改为 `mode="multiple"` + 后端支持逗号分隔或数组参数 |
| 数据管理已匹配/未匹配过滤 | HR 最高频的操作之一：快速区分哪些记录已完成工号匹配、哪些还缺失 | Low | 现有 DataManagement 筛选栏 | 新增一个 Select/Radio 筛选项 + 后端新增 matched 查询参数 |
| 员工主档默认使用服务器已有主档 | 当前 SimpleAggregate 中 employeeMasterMode 默认值是 'none'，但绝大多数场景应该用已有主档 | Trivial | SimpleAggregate 页面第 177 行 | 将默认值改为 'existing' 即可 |
| 批次删除联动月份数据清理 | 删除批次时不清理关联的 normalized records 会留下脏数据 | Low-Med | 后端 import batch + normalized_records 表 | 需后端级联删除（SQLAlchemy cascade 或手动删除） |

## Differentiators

不一定被期望，但能显著提升产品价值的功能。

| Feature | Value Proposition | Complexity | Dependencies | Notes |
|---------|-------------------|------------|--------------|-------|
| 月度对比 diff 风格重做 | 当前 Compare.tsx 是单表+颜色标记，改为左右 Excel 表格 + 单元格级差异高亮后，HR 能直观看到"上月 vs 本月"每个人每个字段的变化量 | High | 现有 Compare.tsx / PeriodCompare.tsx 已有约 60% 基础 | **不要** 用 react-diff-viewer（代码 diff 库），应自建双 AntD Table + 单元格 diff |
| 融合特殊规则配置 | 允许 HR 选定员工 + 选定字段 + 输入覆盖值，保存可复用；解决"某人社保基数需手动覆盖"的真实痛点 | High | 融合管线 + 新建后端规则模型/API/引擎 | v1.1 最复杂的新功能，核心难点在规则引擎与融合管线集成 |
| 融合增加个人社保/公积金承担额 | 支持上传或飞书同步个人承担额独立数据，解决"个人实际承担额 != 标准扣缴额"的场景 | Med-High | 融合管线 + 新增 canonical fields + 模板列（仅 Tool 模板） | 不得修改 Salary 模板融合逻辑 |
| 快速融合上传文件计数 | 让 HR 在上传区域直接看到"已选 N 个社保文件 / M 个公积金文件" | Trivial | SimpleAggregate 页面 | 纯前端 `socialFiles.length` 展示 |
| 设置页搜索 + 快速导航 | 管理功能越来越多，搜索框让管理员快速跳转到目标设置项 | Med | 需新建设置项元数据列表或 Command Palette | 可做顶部搜索或 Cmd+K 面板 |
| 飞书功能前端完善 | 飞书凭证管理后端已有但无前端，补齐后管理员不需 curl 操作 | Low-Med | 后端 feishu credentials API | 标准表单页 |
| 审计日志完善（真实 IP） | 当前可能记录代理 IP 而非真实客户端 IP，影响安全审计可信度 | Low | 后端 request_helpers.get_client_ip | 解析 X-Forwarded-For / X-Real-IP 头 |
| 个人险种缴费基数数据修复 | 确保各地区缴费基数字段正确映射存储 | Med | 后端解析管线 + 逐地区验证 | 属于数据质量修复 |
| Python 3.9 适配 | 云服务器部署环境为 Python 3.9，需去除 3.10+ 语法 | Low-Med | 后端所有 Python 文件 | `match/case`、`X | Y` 类型联合、`list[int]` 等语法需降级 |
| v1.0 遗留技术债清理 | 5 个废弃组件文件待删除，武汉公积金样例缺失 | Low | Phase 7 遗留组件 | 清理提升代码健康度 |

## Anti-Features

明确不应该构建的功能。

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| 完全自定义主题编辑器 | 过度工程化，内部工具只需亮/暗两套 | 提供亮色/暗色开关，不做颜色 picker |
| 代码 diff 风格文本对比组件 | react-diff-viewer / diff2html 是文本/代码 diff 工具，社保数据是结构化表格，UX 完全不匹配 | 自建双 AntD Table + 单元格级条件样式 |
| 拖拽式菜单自定义 | 内部工具不需要用户自己排列菜单顺序 | 按使用频率固定分组，SubMenu 嵌套 |
| 细粒度权限矩阵 UI | 三角色模型（admin/hr/employee）已足够，字段级权限无人提需求 | 账号管理页只提供角色 Select 下拉 |
| Salary 模板融合逻辑修改 | 已明确禁止修改，运行完美 | 任何新增字段只加到 Tool 模板 |
| 实时协作编辑 | 单公司内部使用，无多人同时编辑场景 | 保持单用户操作模式 |
| 移动端原生 App | 明确 Out of Scope | 仅做 Web 响应式适配 |
| BPMN 审批流引擎 | 社保数据处理不需要多级审批流 | 简单状态推进 + 角色权限控制 |

## Feature Dependencies

```
[独立，无依赖]
  |- 员工主档默认值 (trivial, 一行代码)
  |- 文件计数显示 (trivial, 纯前端)
  |- 技术债清理 (独立)
  |- Python 3.9 适配 (独立，后端)
  |- 审计日志 IP 修复 (独立，后端)

[菜单 + 导航]
  |- 左侧菜单多级折叠 (独立)
  |- 设置页搜索 -> 依赖菜单重组完成后才能收集设置项元数据

[主题系统]
  |- 暗黑模式切换 -> 定义 dark tokens -> 处理非 AntD 元素颜色
                   -> MainLayout 硬编码颜色替换为 token 引用
                   -> Sider dark 主题调整

[响应式]
  |- 全页面响应式 -> 逐页面适配（7+ 个数据表格页面）
                  -> 移动端 Sider 改为 Drawer
                  -> Row/Col 断点配置

[数据管理增强]
  |- 筛选多选 -> 后端支持数组参数
  |- 已匹配/未匹配过滤 -> 后端新增 matched 查询参数
  |- 批次删除联动 -> 后端级联删除逻辑

[账号管理]
  |- 账号管理前端 (独立，后端已就绪)

[融合增强]
  |- 融合增加个人承担额 -> 新增 canonical fields
                        -> 映射规则扩展
                        -> Tool 模板新列（不动 Salary 模板）
  |- 融合特殊规则配置 -> 新建数据模型 OverrideRule
                      -> 新建 CRUD API
                      -> 融合管线插入规则应用步骤
                      -> 前端配置 UI
  (特殊规则配置可独立于个人承担额，但同属融合增强范畴)

[对比重做]
  |- 月度对比 diff 风格 -> 需重新设计 Compare 页面
                        -> 双 Table 渲染组件
                        -> 同步滚动机制
                        -> 单元格 diff 计算
                        -> "只看差异" 过滤

[飞书]
  |- 飞书前端完善 (独立)

[数据修复]
  |- 缴费基数修复 -> 逐地区验证映射规则
```

## Detailed Feature Specifications

### 1. 响应式数据表格

**Expected behavior:**
- 所有 AntD Table 页面在 < 768px 宽度下能横向滚动
- 关键列（姓名、工号）使用 `fixed: 'left'` 固定在左侧
- 非关键列（补充医疗、滞纳金等低频字段）使用 `responsive: ['lg']` 在小屏隐藏
- 每个表格设置合理的 `scroll={{ x: N }}`（N 根据可见列总宽度计算）
- Sider 在移动端（< 768px）改为 Drawer 模式（点击汉堡菜单唤出）
- 卡片网格使用 `<Row gutter>` + `<Col xs={24} sm={12} md={8} lg={6}>` 断点
- Header 在移动端简化（隐藏面包屑，保留用户名和菜单按钮）

**Affected pages（按优先级）:**
1. DataManagement - 最多列（20+ 字段），最高频使用
2. PeriodCompare - 双倍列宽
3. Employees - 员工列表
4. Results - 校验匹配结果
5. Imports - 批次管理
6. AuditLogs - 日志列表
7. Exports - 导出记录

**Implementation key points:**
```typescript
// 列配置示例
{ title: '姓名', dataIndex: 'person_name', fixed: 'left', width: 100 },
{ title: '工号', dataIndex: 'employee_id', fixed: 'left', width: 100 },
{ title: '补充医疗', dataIndex: 'supplementary_medical_company', responsive: ['lg'] },
```

**Confidence:** HIGH - AntD 官方文档明确支持 `scroll.x`、`fixed`、`responsive` 属性。

### 2. 暗黑模式切换

**Expected behavior:**
- Header 右侧用户信息旁提供亮/暗切换按钮（Sun/Moon 图标）
- 用户偏好保存到 localStorage，刷新后保持
- 首次访问跟随系统 `prefers-color-scheme`
- 切换无闪烁（AntD 5 CSS-in-JS 运行时切换，不需 LESS 重编译）
- 非 AntD 元素（MainLayout 的背景色、自定义 CSS Module 等）也要跟随主题

**Implementation approach:**
```typescript
// theme/index.ts 扩展为 lightTheme + darkTheme
import { theme as antdTheme } from 'antd';

export const lightTheme: ThemeConfig = { /* 现有 theme 对象 */ };
export const darkTheme: ThemeConfig = {
  algorithm: antdTheme.darkAlgorithm,
  token: {
    colorPrimary: '#3370FF',  // 保持品牌色
    colorBgContainer: '#1F1F1F',
    colorBgLayout: '#141414',
    colorBgElevated: '#2A2A2A',
    colorText: '#E8E8E8',
    // ... 其余 dark tokens
  },
  components: {
    Layout: { siderBg: '#0D0D0D', bodyBg: '#141414' },
    // ... 组件级 dark 覆盖
  },
};
```

**Critical caveat (HIGH confidence):** AntD 5 的 `darkAlgorithm` 只覆盖 AntD 组件内部。页面 body 背景、MainLayout 中 `background: '#F5F6F7'` 等硬编码颜色必须改为 token 引用或 CSS 变量。当前 MainLayout.tsx 第 286-290 行的 Content style 有硬编码颜色需要处理。

**Storage:** `localStorage.setItem('theme-mode', 'dark' | 'light' | 'system')`

### 3. 月度对比 diff 风格重做

**Expected behavior:**
- 左右两个独立 AntD Table，各自渲染一个月的完整数据
- 同一员工行通过 employee_id 或 id_number 对齐
- 差异单元格高亮：金额增加 = 绿色背景，金额减少 = 红色背景，不变 = 无色
- 只在一侧出现的人员行整行标色（左侧独有 = 红底/删除，右侧独有 = 蓝底/新增）
- 支持"只看差异行"过滤开关
- 两个表格同步滚动（监听 `.ant-table-body` onScroll 事件互相同步 scrollTop/scrollLeft）
- 单元格 hover tooltip 显示变化量（+500.00）和变化百分比（+5.2%）
- 表格顶部统计卡片：变化人数、新增人数、减少人数、总额变化

**Why NOT use react-diff-viewer / diff2html:**
- 这些库设计用于代码/文本 diff，输出的是行级对比视图
- 社保数据是结构化表格（姓名、工号、N 个金额字段），需要单元格级别对比
- react-diff-viewer 的 split view 虽然左右分栏，但渲染的是文本行不是表格列
- 自建双 Table 可以完全控制列配置、固定列、列隐藏等 AntD 特性

**Implementation approach:**
- 用 Map<string, LeftRow> + Map<string, RightRow> 按员工 ID 对齐
- 合并为 unified list: `{ left: LeftRow | null, right: RightRow | null, status: 'match' | 'left_only' | 'right_only' }`
- 逐字段比较生成 diff 标记
- 渲染时通过 AntD Table 的 `onCell` 返回条件背景色
- 同步滚动：两个 Table 的 `.ant-table-body` 互相监听 scroll 事件

**Complexity note:** 现有 Compare.tsx 已有字段映射 FIELD_LABELS、diffCellStyle、rowBackground 等约 60% 的基础逻辑，重做主要是将单表渲染改为双表渲染。

### 4. 账号管理系统

**Expected behavior:**
- 仅 admin 可访问的独立页面 `/accounts` 或 `/users`
- 用户列表 Table：用户名、显示名、角色（Tag 颜色区分）、创建时间、操作列
- "新建用户"按钮 -> Modal 表单（用户名、密码、确认密码、角色 Select、显示名）
- "编辑"按钮 -> Modal 表单（角色 Select、显示名，用户名不可改）
- "重置密码"按钮 -> Modal（新密码 + 确认密码）
- 安全约束：不能删除/降级自己；不能降级唯一 admin
- 所有操作自动记录审计日志（后端已实现）

**Backend status (HIGH confidence):**
- `POST /api/v1/users/` - 创建用户
- `GET /api/v1/users/` - 列表查询
- `GET /api/v1/users/:id` - 获取详情
- `PUT /api/v1/users/:id` - 更新信息（role, display_name）
- `PUT /api/v1/users/:id/password` - 重置密码
- Schema: UserCreate(username, password, role, display_name), UserUpdate(role?, display_name?), UserPasswordReset(new_password)

**Frontend implementation:** 标准 AntD Table + Modal.confirm/Form 模式，预计 200-300 行代码。

### 5. 融合特殊规则配置

**Expected behavior:**
- 入口在快速融合页面的"高级设置"折叠面板中
- 规则定义三要素：
  1. 目标员工（姓名/工号搜索 AutoComplete）
  2. 目标字段（canonical field 下拉 Select）
  3. 覆盖值（数字 InputNumber）
- 规则可保存命名（如"张三 2月基数调整"），下次融合勾选复用
- 规则执行时机：标准化之后、导出之前（在融合管线中间插入）
- 执行后在结果中标记"已被规则覆盖"（traceability）
- 不得影响 Salary 模板融合逻辑

**Backend design:**
- 新模型：`OverrideRule(id, name, rules: JSON, created_by, created_at, updated_at)`
- rules JSON 结构：`[{ employee_id?: string, person_name?: string, id_number?: string, field: string, value: number }]`
- 新 API：`CRUD /api/v1/override-rules`
- 融合管线新步骤：`apply_override_rules(normalized_records, rule_ids) -> modified_records`

**Complexity analysis:** v1.1 最复杂的新功能。分三步递进实现：
1. 规则存储 + CRUD API（Low-Med）
2. 融合管线集成（Med）
3. 前端配置 UI（Med）

### 6. 菜单多级折叠

**Recommended grouping:**
```
快速融合          (顶级，最高频)
处理看板          (顶级)
数据管理          (顶级)

对比分析 >        (SubMenu)
  |- 月度对比
  |- 跨期对比
  |- 异常检测

基础数据 >        (SubMenu)
  |- 批次管理
  |- 映射修正
  |- 校验匹配
  |- 导出结果
  |- 员工主档

系统管理 >        (SubMenu, admin only)
  |- 账号管理      (新增)
  |- 审计日志
  |- API 密钥

飞书集成 >        (SubMenu, 条件显示)
  |- 飞书同步
  |- 飞书设置
```

**Implementation:** 将 ALL_NAV_ITEMS 改为嵌套结构，使用 AntD Menu 的 `children` 属性。折叠状态下 SubMenu 显示为 popover 子菜单。

### 7. 暗黑模式 - 需要处理的非 AntD 元素清单

| 位置 | 当前硬编码 | 需改为 |
|------|-----------|--------|
| MainLayout Content style | `background: '#F5F6F7'` | `token.colorBgLayout` |
| MainLayout Header style | `background: '#fff'`, `borderBottom: '1px solid #DEE0E3'` | `token.colorBgContainer`, `token.colorBorder` |
| AuthRouteState | `background: '#F5F6F7'` | `token.colorBgLayout` |
| Login page | 可能有硬编码背景色 | token 引用 |
| MainLayout.module.css | logo 样式 | CSS 变量或 className 条件切换 |
| animations.module.css | 动画中可能有颜色值 | 检查并替换 |
| PeriodCompare diffCellStyle | `color: '#00B42A'` / `'#F54A45'` | 可保持（绿红在暗黑模式下仍可读），但 rowBackground 的浅色背景需调整 |

## MVP Recommendation

### Phase 1: 快速见效 + UI 基础整理（1-2 天）
改动小、用户感知强的功能集中交付：

1. **员工主档默认使用已有主档** - Trivial
2. **文件计数显示** - Trivial
3. **左侧菜单多级折叠** - Low
4. **数据管理筛选多选 + 匹配过滤** - Low
5. **技术债清理**（废弃组件删除）- Low
6. **Python 3.9 适配** - Low-Med（可并行）

### Phase 2: 账号管理 + 主题（2-3 天）
7. **账号管理前端页面** - Low-Med
8. **暗黑模式切换** - Low-Med
9. **审计日志 IP 修复** - Low

### Phase 3: 响应式全面适配（2-3 天）
10. **全页面响应式** - Medium（7+ 页面逐一适配）
11. **飞书前端完善** - Low-Med

### Phase 4: 融合能力增强（3-4 天）
12. **融合增加个人承担额** - Med-High
13. **融合特殊规则配置** - High
14. **缴费基数数据修复** - Med
15. **批次删除联动清理** - Low-Med

### Phase 5: 对比重做 + 收尾（2-3 天）
16. **月度对比 diff 风格重做** - High
17. **设置页搜索** - Med（评估菜单分组后是否仍需要）

**Defer to v1.2:**
- 设置页搜索（如果菜单分组足够清晰，可能不再需要）
- Command Palette（优先级最低的 UX 增强）

## Phase Ordering Rationale

1. **Trivial + Low 优先**: 员工主档默认值、文件计数、菜单分组可以一天内全部完成，立刻改善日常使用体验
2. **账号管理在主题之前**: 后端已就绪，纯前端工作，交付后管理员立刻可用；暗黑模式需要更多全局样式审计
3. **响应式独立成 phase**: 涉及 7+ 个页面的逐一适配，工作量可预测但需要逐页测试
4. **融合增强在后半段**: 复杂度最高（特别是特殊规则配置），需要新建后端模型/API/引擎，且依赖对现有融合管线的深入理解
5. **对比重做最后**: 虽然用户价值高，但复杂度也最高，且不影响核心融合流程；放到最后可以把前面 phase 的响应式/暗黑模式经验带入

## Sources

- [Ant Design 5 Customize Theme](https://ant.design/docs/react/customize-theme/) - darkAlgorithm 运行时切换，HIGH confidence
- [Ant Design Table](https://ant.design/components/table/) - scroll.x / fixed / responsive 属性，HIGH confidence
- [Ant Design Menu](https://ant.design/components/menu/) - SubMenu / inlineCollapsed 多级折叠，HIGH confidence
- [Ant Design Select](https://ant.design/components/select/) - mode="multiple" 多选模式，HIGH confidence
- [How To Toggle Dark Theme With Ant Design 5.0](https://betterprogramming.pub/how-to-toggle-dark-theme-with-ant-design-5-0-eb68552f62b8) - 实现参考，MEDIUM confidence
- [Ant Design Pro Permission Management](https://beta-pro.ant.design/docs/authority-management/) - 权限管理模式参考
- [react-diff-viewer (GitHub)](https://github.com/praneshr/react-diff-viewer) - 评估后决定不采用（代码 diff 工具，不适合表格数据）
- [diff2html](https://diff2html.xyz/) - 评估后决定不采用（文本 diff 工具）
- [AntD Table responsive](https://medium.com/@rohitkumar1351999rk/improving-horizontal-scroll-indication-in-ant-design-tables-43abe8ecaa02) - 横向滚动 UX 改进
