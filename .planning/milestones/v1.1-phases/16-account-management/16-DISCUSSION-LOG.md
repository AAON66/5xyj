# Phase 16: 账号管理 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-07
**Phase:** 16-账号管理
**Areas discussed:** 管理页面布局, 用户自改密码入口, 密码策略与安全, 角色与状态操作, 管理员自保护, 列表显示字段

---

## 管理页面布局

### 页面入口

| Option | Description | Selected |
|--------|-------------|----------|
| 管理组新菜单项 | 在 Phase 15 已有的「管理」分组中新增「账号管理」菜单项，路由 /users，admin-only | ✓ |
| Settings 页卡片内嵌 | 在现有设置页中新增「账号管理」卡片，点击展开用户列表 | |
| 两者皆有 | 侧边栏菜单直达 + Settings 中也放"前往"链接卡片 | |

**User's choice:** 管理组新菜单项
**Notes:** 无

### 编辑交互

| Option | Description | Selected |
|--------|-------------|----------|
| Modal 弹窗 | 点击编辑/新建弹出 Modal 表单，与现有员工主档页交互一致 | ✓ |
| 抽屉 Drawer | 右侧滑出抽屉，空间更大但模式不同 | |
| 行内编辑 | 直接在表格行内编辑，适合字段少的场景 | |

**User's choice:** Modal 弹窗
**Notes:** 无

---

## 用户自改密码入口

### 密码入口位置

| Option | Description | Selected |
|--------|-------------|----------|
| Header 用户下拉 | 右上角用户名下拉菜单增加「修改密码」项，点击弹出 Modal。所有角色都能看到 | ✓ |
| Settings 页卡片 | 在设置页新增「账号安全」卡片，点击进入密码修改表单 | |
| 两者皆有 | Header 下拉有快捷入口 + Settings 也有账号安全卡片 | |

**User's choice:** Header 用户下拉
**Notes:** 无

### 强制改密处理

| Option | Description | Selected |
|--------|-------------|----------|
| 强制 Modal | 登录后立即弹出不可关闭的修改密码 Modal，修改后才能操作系统 | ✓ |
| 横幅提示不强制 | 顶部显示醒目横幅提示修改密码，但不阻断用户操作 | |

**User's choice:** 强制 Modal
**Notes:** 当前 Login 页已有 mustChangePassword warning 提示

---

## 密码策略与安全

### 旧密码验证

| Option | Description | Selected |
|--------|-------------|----------|
| 必须验证 | 输入旧密码 + 新密码 + 确认新密码。防止他人利用未锁屏电脑修改密码 | ✓ |
| 不需要 | 已登录即可修改，只输新密码 + 确认。更简单但安全性降低 | |

**User's choice:** 必须验证
**Notes:** 无

### 密码强度

| Option | Description | Selected |
|--------|-------------|----------|
| 保持现状 | 最少 8 位即可，不增加复杂度要求。内部系统不需过度安全 | ✓ |
| 增强强度 | 要求包含大小写+数字，前端实时密码强度指示器 | |

**User's choice:** 保持现状
**Notes:** 当前后端 schema 已有 min_length=8

---

## 角色与状态操作

### 可选角色

| Option | Description | Selected |
|--------|-------------|----------|
| admin + hr | 保持现状，只能创建管理员和 HR。employee 通过三要素验证自动创建 | ✓ |
| admin + hr + employee | 允许手动创建员工账号，需考虑与现有三要素验证流程的关系 | |

**User's choice:** admin + hr
**Notes:** 无

### 禁用账号交互

| Option | Description | Selected |
|--------|-------------|----------|
| 开关切换 | 用户列表中每行显示启用/禁用 Switch 开关，点击即切换 | ✓ |
| 操作菜单中 | 禁用放在「更多操作」下拉中，防止误触但操作步骤多一步 | |

**User's choice:** 开关切换
**Notes:** 无

---

## 管理员自保护

| Option | Description | Selected |
|--------|-------------|----------|
| 禁止自我操作 | 不能禁用自己、不能改自己角色。前端灰色禁用 + 后端 403 双保险 | ✓ |
| 允许但确认 | 允许操作但弹出二次确认对话框 | |
| Claude 决定 | 交给 Claude 来决定具体实现 | |

**User's choice:** 禁止自我操作
**Notes:** 无

---

## 列表显示字段

| Option | Description | Selected |
|--------|-------------|----------|
| 标准字段 | 用户名、显示名、角色（Tag）、状态（Switch）、创建时间、操作（编辑/重置密码） | ✓ |
| 精简字段 | 用户名、角色、状态、操作。不显示显示名和创建时间 | |

**User's choice:** 标准字段
**Notes:** 无

---

## Claude's Discretion

- Modal 表单的具体布局和验证提示文案
- 用户列表的分页策略
- 重置密码确认对话框的具体文案
- 创建用户后是否自动生成初始密码或由管理员手动输入

## Deferred Ideas

None
