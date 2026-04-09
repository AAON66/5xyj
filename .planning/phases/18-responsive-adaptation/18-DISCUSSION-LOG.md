# Phase 18: 全页面响应式适配 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-09
**Phase:** 18-responsive-adaptation
**Areas discussed:** 移动端导航与 Header 压缩, 数据页筛选区在手机上的形态, 员工自助查询的手机优先布局, 长流程页面的主操作固定方式

---

## 移动端导航与 Header 压缩

| Option | Description | Selected |
|--------|-------------|----------|
| Drawer + 顶部汉堡按钮（推荐） | 保留桌面 `Sider`，手机端切成 `Drawer`，点击后自动收起 | ✓ |
| 覆盖式侧边栏 | 仍沿用侧栏感知，但手机端体验更笨重 | |
| 底部 Tab 导航 | 需要重排整套导航架构 | |

**User's choice:** Drawer + 顶部汉堡按钮

| Option | Description | Selected |
|--------|-------------|----------|
| 只保留页标题，面包屑隐藏（推荐） | 节省横向空间，优先保留手机端标题与主操作 | ✓ |
| 保留单行精简面包屑 | 层级更强，但容易压缩标题与右侧空间 | |
| 两行 Header | 信息完整，但明显抬高首屏 | |

**User's choice:** 只保留页标题，面包屑隐藏

| Option | Description | Selected |
|--------|-------------|----------|
| 跳转后自动关闭 Drawer（推荐） | 符合手机端预期，也满足 Phase 18 成功标准 | ✓ |
| 保持 Drawer 打开 | 需要用户手动再关闭 | |
| 同组页面保持打开、跨组才关闭 | 规则更复杂，收益不高 | |

**User's choice:** 跳转后自动关闭 Drawer

---

## 数据页筛选区在手机上的形态

| Option | Description | Selected |
|--------|-------------|----------|
| 收进“筛选”按钮打开的 Drawer（推荐） | 让主内容区保持可见，适合多筛选项页面 | ✓ |
| 默认纵向铺开在表格上方 | 首屏容易被筛选控件占满 | |
| 折叠面板页内展开 | 比 Drawer 轻，但展开后仍明显挤占内容区 | |

**User's choice:** 收进“筛选”按钮打开的 Drawer

| Option | Description | Selected |
|--------|-------------|----------|
| 底部“应用筛选 / 清空”按钮，确认后生效（推荐） | 避免移动端每改一个值就触发表格反复刷新 | ✓ |
| 每次修改立即生效 | 更直接，但联动筛选刷新会很频繁 | |
| 部分立即生效，部分点应用 | 规则复杂，用户不易预期 | |

**User's choice:** 底部“应用筛选 / 清空”按钮，确认后生效

| Option | Description | Selected |
|--------|-------------|----------|
| 桌面保持现状，平板/手机切到 Drawer（推荐） | 风险最低，保留后台系统桌面效率 | ✓ |
| 平板也改成 Drawer | 跨断点更统一，但可见信息减少 | |
| 所有尺寸都统一用 Drawer | 一致性最高，但会损失桌面效率 | |

**User's choice:** 桌面保持现状，平板/手机切到 Drawer

---

## 员工自助查询的手机优先布局

| Option | Description | Selected |
|--------|-------------|----------|
| 卡片流布局，先汇总后明细，历史记录按折叠卡片展开（推荐） | 最适合当前单页结构，也最贴合手机阅读 | ✓ |
| 尽量保留表格感 | 与桌面更一致，但手机可读性一般 | |
| 分成多个 Tab | 层次清楚，但会把单页信息切碎 | |

**User's choice:** 卡片流布局，先汇总后明细，历史记录按折叠卡片展开

| Option | Description | Selected |
|--------|-------------|----------|
| 只默认展开最新月份（推荐） | 最新月优先，首屏负担最小 | ✓ |
| 全部收起 | 更省空间，但多一次操作 | |
| 全部展开 | 信息直接，但页面会很长 | |

**User's choice:** 只默认展开最新月份

| Option | Description | Selected |
|--------|-------------|----------|
| 纵向连续堆叠，两张卡片上下排（推荐） | 不需要横向切换，最适合手机 | ✓ |
| 做成 Tabs：社保 / 公积金 | 节省首屏空间，但多一步切换 | |
| 合并成一张总卡片 | 信息更集中，但视觉更拥挤 | |

**User's choice:** 纵向连续堆叠，两张卡片上下排

---

## 长流程页面的主操作固定方式

| Option | Description | Selected |
|--------|-------------|----------|
| 底部 sticky action bar 固定主按钮（推荐） | 手机长页面里始终够得着主操作 | ✓ |
| 保留页内原位置 | 实现简单，但长页里返回按钮成本高 | |
| 页面顶部固定操作区 | 可达，但单手操作不如底部顺手 | |

**User's choice:** 底部 sticky action bar 固定主按钮

| Option | Description | Selected |
|--------|-------------|----------|
| 只放一个主动作，次要动作收进更多/页内（推荐） | 最稳，不会把手机底部条挤满 | ✓ |
| 主动作 + 一个次动作并排 | 效率更高，但容易拥挤 | |
| 两个以上动作都固定在底部 | 信息最全，但通常会很乱 | |

**User's choice:** 只放一个主动作，次要动作收进更多/页内

## Claude's Discretion

- 具体断点数值与 `Drawer` 宽度
- `sticky action bar` 的视觉样式和辅助说明
- 各页面次要动作的收纳方式

## Deferred Ideas

None
