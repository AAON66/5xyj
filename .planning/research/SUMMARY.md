# Project Research Summary

**Project:** Social Security Aggregation Tool v1.1
**Domain:** v1.1 体验优化与功能完善 -- 响应式设计、暗黑模式、对比重做、账号管理、Python 3.9 适配、融合增强
**Researched:** 2026-04-04
**Confidence:** HIGH

## Executive Summary

v1.1 是一个以"用好现有技术栈"为核心理念的体验优化里程碑。四份研究报告一致得出的结论是：前端零新依赖（Ant Design 5 内置暗黑模式、响应式断点、多级菜单），后端零新依赖（SQLAlchemy 级联删除、FastAPI 已有用户 CRUD），Python 3.9 适配仅需移除 10 处 `slots=True` + 固定两个包的版本上界。技术选型风险极低，主要工作量在于将 v1.0 遗留的 329 处硬编码内联样式迁移到 Ant Design token 体系，以及实现融合特殊规则这一唯一真正的"新功能"。

推荐的实施路径是：先做 Python 3.9 适配（部署前置条件）和内联样式 token 化（暗黑模式和响应式的共同前置条件），再分批交付 UI 增强功能，将融合特殊规则和对比 diff 重做放在最后阶段。这一顺序确保了每个阶段的工作都建立在前一阶段的基础之上，避免返工。

主要风险集中在三个方面：(1) SQLite 级联删除依赖 `PRAGMA foreign_keys=ON`，必须通过集成测试验证；(2) 暗黑模式如果不先做样式迁移就直接加开关，会导致界面"半白半黑"的灾难效果；(3) 融合特殊规则是 v1.1 唯一涉及新数据模型 + 新 API + 新业务逻辑的功能，复杂度最高。这三项风险都有明确的防范策略，详见各研究文件。

## Key Findings

### Recommended Stack

v1.1 无需引入任何新的 npm 或 pip 依赖。现有 Ant Design 5 + FastAPI 0.115 已内置所有所需能力。

**Core technologies:**
- **AntD `theme.darkAlgorithm`**：暗黑模式 -- 运行时切换，自动从种子色派生暗色 token，零 CSS 重编译
- **AntD `Grid.useBreakpoint()`**：响应式 -- 内置 xs/sm/md/lg/xl 断点布尔值，替代 react-responsive
- **AntD `Table` + `onCell`**：对比面板 -- 单元格级条件样式，替代 react-diff-viewer（代码 diff 库不适合表格数据）
- **SQLite JSON column**：融合规则 -- 简单 JSON 存储规则定义，SQLAlchemy ORM 管理
- **FastAPI <0.130.0 + pandas <2.3.0**：Python 3.9 适配 -- 版本上界固定

**明确拒绝的库：** react-diff-viewer、Tailwind CSS、@ant-design/pro-components、ag-grid、zustand/jotai/redux、fuse.js、framer-motion。每一个都有更轻量的内置替代方案（详见 STACK.md）。

### Expected Features

**Must have (Table Stakes):**
- 全页面响应式自适应 -- 各窗口尺寸基本预期
- 暗黑模式切换 -- 低光环境长时间使用刚需
- 账号管理前端 -- 后端已 100% 就绪，无前端页面
- 左侧菜单多级折叠 -- 14 个平铺菜单项导航效率低
- 数据管理筛选多选 + 已匹配/未匹配过滤 -- HR 高频操作
- 员工主档默认使用已有主档 -- trivial 一行修复
- 批次删除联动月份数据清理 -- 避免脏数据

**Should have (Differentiators):**
- 月度对比 diff 风格重做 -- 左右 Excel 表格 + 单元格级差异高亮
- 融合特殊规则配置 -- 选人 + 选字段 + 覆盖值，可保存复用（v1.1 最复杂新功能）
- 融合增加个人社保/公积金承担额 -- 仅影响 Tool 模板，不动 Salary 模板
- Python 3.9 适配 -- 部署环境硬性要求
- 审计日志真实 IP -- 安全审计可信度

**Defer (v1.2+):**
- 设置页搜索 / Command Palette -- 菜单分组后可能不再需要
- 完全自定义主题编辑器 -- 内部工具只需亮/暗两套
- 移动端原生 App -- 明确 Out of Scope，仅做 Web 响应式

### Architecture Approach

v1.1 的架构变更集中在前端层：新增 ThemeProvider（暗黑模式状态）、useBreakpoint hook（响应式断点）、DiffTable 组件（对比面板）、UserManagement 页面（账号 CRUD）。后端仅需新增 SpecialRule 模型和对应 CRUD API、数据管理删除端点、审计日志 IP 改进。核心数据管线（Upload -> Parse -> Normalize -> Validate -> Match -> Export）保持不变，融合特殊规则作为"标准化之后、导出之前"的可选插入步骤。

**Major components:**
1. **ThemeProvider** (new) -- 暗黑/亮色模式状态 + localStorage 持久化 + `prefers-color-scheme` 初始检测
2. **useBreakpoint hook** (new) -- 统一响应式断点逻辑（isMobile/isTablet/isDesktop），避免各页面重复实现
3. **DiffTable + DiffCell** (new) -- 双表同步滚动 + 单元格 diff 高亮 + 行级状态指示
4. **UserManagement page** (new) -- 标准 CRUD 表格（后端 5 个端点已完整实现）
5. **SpecialRule model + API** (new) -- 融合规则持久化、CRUD、管线集成点
6. **MainLayout** (modified) -- 多级菜单、移动端 Drawer、暗黑模式切换按钮、响应式 Header

### Critical Pitfalls

1. **SQLite CASCADE DELETE 默认不生效** -- `PRAGMA foreign_keys=ON` 必须在每个连接上激活。防范：集成测试验证 + 启动时断言 PRAGMA 值。
2. **329 处硬编码内联样式阻断暗黑模式** -- 必须先完成样式 token 化迁移，再实现暗黑模式开关。预计 2x 时间预算。
3. **Python 3.9 `@dataclass(slots=True)` 不兼容** -- 10 处使用分布在 5 个文件中。直接移除 `slots=True`，无功能影响。
4. **融合增强可能破坏 Salary 模板** -- 新字段只加到 Tool 模板。冻结 Salary exporter 字段列表 + 字节级回归测试。
5. **对比面板大数据量性能** -- 500+ 员工 x 20+ 列。服务端计算 diff + 虚拟化渲染。

## Implications for Roadmap

### Phase 1: 基础准备与快速见效
**Rationale:** Python 3.9 是部署硬性前置条件，不做就无法上线；trivial 修复可立即改善日常体验；技术债清理减少后续干扰。如果推迟 3.9 适配，后续所有新代码都可能使用 3.10+ 语法导致二次审计。
**Delivers:** 可在 Python 3.9 上部署的后端 + 若干立即可感知的体验改善
**Addresses:** Python 3.9 适配（移除 slots=True + 版本固定）、员工主档默认值（一行代码）、文件计数显示（纯前端）、v1.0 技术债清理（5 个废弃文件）、审计日志 IP 修复
**Avoids:** Pitfall 2/3（union type + built-in generics 语法问题）、Pitfall 11（Pydantic + __future__ 边界情况）

### Phase 2: 样式 Token 化 + 暗黑模式
**Rationale:** 样式 token 化是暗黑模式和响应式的共同前置条件。三份研究报告（STACK、ARCHITECTURE、PITFALLS）一致指出 329 处硬编码样式是暗黑模式的最大障碍。必须先迁移再加开关。
**Delivers:** 暗黑/亮色模式切换 + 去除所有硬编码颜色
**Addresses:** 内联样式 token 化（22 个页面文件）、ThemeProvider 创建、暗黑模式切换按钮、localStorage 持久化
**Avoids:** Pitfall 4（内联样式阻断）、Pitfall 8（主题复制漂移 -- 使用 darkAlgorithm 派生而非复制）、Pitfall 13（CSS 模块不足）、Pitfall 17（偏好未持久化）

### Phase 3: 菜单重组 + 账号管理 + 数据管理增强
**Rationale:** 三组互相独立的功能可并行开发。菜单重组独立性强、账号管理后端已 100% 完成、数据管理增强改动小但高频使用。
**Delivers:** 清晰的导航层级 + 管理员账号 CRUD + 更灵活的数据筛选与删除
**Addresses:** 左侧菜单多级折叠、账号管理前端页面、筛选多选、已匹配/未匹配过滤、批次删除联动清理
**Avoids:** Pitfall 1（SQLite FK 强制执行 -- 集成测试验证）、Pitfall 6（自降级保护）、Pitfall 7（删除范围歧义 -- 区分 batch 删除与 period 删除）、Pitfall 10（URL 书签失效 -- 只改视觉分组不改路由路径）

### Phase 4: 全页面响应式适配
**Rationale:** 涉及 7+ 页面逐一适配，工作量可预测但需要逐页测试。依赖 Phase 2 的样式 token 化成果（避免新加的响应式内联样式又变成硬编码颜色）。
**Delivers:** 所有页面在移动端/平板端可用
**Addresses:** 全页面响应式（7 个数据表格页面）、移动端 Sider 改为 Drawer、员工自助页面移动端优先适配
**Avoids:** Pitfall 5（数据表格在窄屏断裂 -- 横向滚动 + 固定左列，不隐藏保险字段列）、Pitfall 14（移动端侧边栏导航后不关闭）、Pitfall 15（员工自助页面遗漏 -- 最高价值移动端场景优先）

### Phase 5: 融合能力增强
**Rationale:** v1.1 最复杂的新功能，涉及新数据模型 + CRUD API + 管线集成 + 前端配置 UI。放在后半段因为需要对现有融合管线的深入理解，且不阻断任何其他功能。建议分三步递进：规则存储 -> 管线集成 -> 前端 UI。
**Delivers:** 融合特殊规则配置 + 个人承担额支持 + 缴费基数修复
**Addresses:** 融合特殊规则配置（SpecialRule 模型 + CRUD + 管线插入）、融合增加个人承担额（新 canonical fields + Tool 模板新列）、缴费基数数据修复
**Avoids:** Pitfall 18（Salary 模板回归 -- 冻结 Salary exporter + 回归测试）

### Phase 6: 对比重做 + 收尾
**Rationale:** 复杂度最高的 UI 重建，但不影响核心融合流程。放在最后可以把前面 phase 的响应式/暗黑模式经验带入。后端已有完整的 diff 计算逻辑，纯前端重建。
**Delivers:** 左右 Excel 风格 diff 对比面板 + 飞书前端完善
**Addresses:** 月度对比 diff 风格重做（双 Table + 同步滚动 + 单元格 diff）、飞书前端完善、设置页搜索（评估菜单分组后是否仍需要）
**Avoids:** Pitfall 9（大数据量渲染性能 -- 服务端 diff + 虚拟化）

### Phase Ordering Rationale

- **Python 3.9 必须最先做**：阻断云服务器部署。且如果推迟，后续所有新代码都可能使用 3.10+ 语法，需要二次审计。
- **样式 token 化必须在暗黑模式和响应式之前**：三份研究报告一致指出 329 处硬编码样式是暗黑模式的最大障碍。这是一次性的准备工作，同时惠及后续两个 phase。
- **账号管理 + 菜单 + 数据管理可并行**：三组功能互不依赖，适合并行开发或快速串行交付。
- **响应式独立成 phase**：涉及 7+ 个页面逐一适配，工作量主要是重复性的逐页审计和调整。
- **融合增强在后半段**：复杂度最高（新模型 + 新 API + 管线集成），需要对融合管线深入理解。
- **对比重做放最后**：虽然用户价值高，但是纯前端重建，不阻断核心流程，且可利用前面 phase 积累的响应式/暗黑模式经验。

### Research Flags

**Needs deeper research during planning:**
- **Phase 5（融合增强）：** 融合特殊规则的规则引擎设计、规则与融合管线的集成点、个人承担额的 canonical field 扩展 -- 需要 `/gsd:research-phase` 深入分析现有融合管线代码
- **Phase 6（对比重做）：** 双表同步滚动的实现细节、大数据量虚拟化渲染策略 -- 需要评估是否引入 `react-window` 或使用 AntD Table `virtual` prop

**Standard patterns (skip research-phase):**
- **Phase 1（基础准备）：** 模式完全确定 -- 移除 `slots=True` + 固定版本上界 + trivial 修复
- **Phase 2（暗黑模式）：** AntD 5 `darkAlgorithm` 是官方一级特性，文档充分，实现路径明确
- **Phase 3（账号管理/菜单/数据管理）：** 标准 CRUD + AntD Menu children + Select mode="multiple"，无需额外研究
- **Phase 4（响应式）：** AntD `useBreakpoint` + Table `scroll.x` + Drawer 是标准实践，重复性适配工作

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | 零新依赖，所有方案基于现有库的内置功能，官方文档验证 |
| Features | HIGH | 基于 v1.0 完整代码库分析 + 后端 API 就绪状态已确认 + 用户场景推导 |
| Architecture | HIGH | 基于 128 个后端文件 + 24 个前端页面的逐文件审计，集成点明确 |
| Pitfalls | HIGH | 基于代码级检查（329 处内联样式、10 处 slots=True、PRAGMA 配置），非推测性结论 |

**Overall confidence:** HIGH

### Gaps to Address

- **融合特殊规则 UI/UX 设计**：数据模型和 API 结构已明确，但前端配置界面的交互细节（员工搜索方式、字段选择、规则预览）需在 phase 规划时确定
- **对比面板虚拟化策略**：推荐 AntD Table `virtual` prop 或 `react-window`，但需要实际性能测试确定 500+ 行场景是否真正需要虚拟化
- **Python 3.9 CI 环境**：研究建议在 CI 中测试 3.9 兼容性，当前项目未见 CI 配置，需确认测试策略
- **暗黑模式与现有暗色侧边栏交互**：Sider 已使用 `theme="dark"`，暗黑模式下侧边栏与内容区背景是否会无法区分，需视觉测试
- **飞书前端完善具体范围**：后端凭证 API 已有但无前端，具体需要哪些页面/表单需在 phase 规划时明确

## Sources

### Primary (HIGH confidence)
- 代码库逐文件审计：128 后端 Python 文件 + 24 前端页面组件 + MainLayout + theme/index.ts
- [Ant Design 5 Customize Theme](https://ant.design/docs/react/customize-theme/) -- darkAlgorithm 运行时切换
- [Ant Design Grid useBreakpoint](https://ant.design/components/grid/) -- 响应式断点 hook
- [Ant Design Table](https://ant.design/components/table/) -- scroll.x / fixed / responsive 属性
- [Ant Design Menu](https://ant.design/components/menu/) -- SubMenu / children 多级折叠
- [Ant Design Select](https://ant.design/components/select/) -- mode="multiple" 多选模式
- Python 3.9 release notes / [PEP 585](https://peps.python.org/pep-0585/) / [PEP 604](https://peps.python.org/pep-0604/) -- 类型语法兼容性
- [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/) -- Python 3.9 support dropped at 0.130.0
- [pandas 2.3.0 drops Python 3.9](https://github.com/pandas-dev/pandas/issues/61563)
- SQLite documentation -- PRAGMA foreign_keys 默认关闭行为

### Secondary (MEDIUM confidence)
- [How To Toggle Dark Theme With Ant Design 5.0](https://betterprogramming.pub/how-to-toggle-dark-theme-with-ant-design-5-0-eb68552f62b8) -- 暗黑模式实现参考
- [Conditional Responsive Design with useBreakpoint](https://dev.to/sarwarasik/conditional-responsive-design-with-ant-designs-usebreakpoint-hook-2lim) -- 断点 hook 使用模式
- [AntD Table responsive](https://medium.com/@rohitkumar1351999rk/improving-horizontal-scroll-indication-in-ant-design-tables-43abe8ecaa02) -- 横向滚动 UX 改进
- [Ant Design Pro Permission Management](https://beta-pro.ant.design/docs/authority-management/) -- 权限管理模式参考

---
*Research completed: 2026-04-04*
*Ready for roadmap: yes*
