# Phase 10: Feishu Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-31
**Phase:** 10-feishu-integration
**Areas discussed:** 同步数据范围与映射, 冲突处理与预览, 飞书 OAuth 登录集成, 飞书凭证与配置管理, 同步状态页设计, Feature Flag 控制机制, 同步字段映射 UI

---

## 同步数据范围与映射

### 数据粒度

| Option | Description | Selected |
|--------|-------------|----------|
| 归一化后的人员明细 | 每个员工每个月一行，包含所有险种金额、基数等字段（NormalizedRecord 级别） | |
| 汇总级别数据 | 按公司+地区+月份汇总，不展示个人明细 | |
| 两者都支持 | 用户可选择推送明细或汇总，分别对应不同的多维表格 | ✓ |

**User's choice:** 两者都支持

### 列结构定义

| Option | Description | Selected |
|--------|-------------|----------|
| 系统自动创建表格和列 | 推送时系统自动在飞书创建多维表格并定义列结构 | |
| HR 先手动创建表格，系统匹配列 | HR 在飞书先建好表格和列，系统按列名自动映射或由 HR 配置映射关系 | ✓ |
| 系统创建 + HR 可调整 | 系统首次同步时自动创建表格和列，之后 HR 可以在系统内调整字段映射 | |

**User's choice:** HR 先手动创建表格，系统匹配列

### 拉取映射

| Option | Description | Selected |
|--------|-------------|----------|
| 复用推送时的映射关系 | 推送时记录了"系统字段→飞书列"的映射，拉取时反向使用，前提是先推送过才能拉取 | ✓ |
| HR 单独配置拉取映射 | 拉取映射可以独立于推送映射，HR 可以从任意飞书多维表格拉取并配置字段对应关系 | |

**User's choice:** 复用推送时的映射关系

### 推送重复处理

| Option | Description | Selected |
|--------|-------------|----------|
| 覆盖更新 | 直接用系统数据覆盖飞书中的旧数据，以系统为准 | |
| 跳过已存在的行 | 只推送飞书中不存在的新数据，不修改已有行 | |
| 提示用户选择 | 推送前检测重复并展示差异，由 HR 选择覆盖/跳过/取消 | ✓ |

**User's choice:** 提示用户选择

---

## 冲突处理与预览

### 冲突预览展示

| Option | Description | Selected |
|--------|-------------|----------|
| 表格对比视图 | 左右分栏或上下分栏，显示每行每个字段的"系统值 vs 飞书值"，差异字段高亮 | |
| 只显示有差异的行 | 过滤掉一致的数据，只展示有变化的记录，每条显示变化前后值 | |
| 批量策略 + 明细查看 | 默认只显示冲突数量和概要，用户可选"全部以系统为准/全部以飞书为准/逐条处理" | |

**User's choice:** 2和3的功能都需要（只显示差异行 + 批量策略+明细查看）

### 冲突解决策略

| Option | Description | Selected |
|--------|-------------|----------|
| 以系统为准 / 以飞书为准 / 逐条选择 | 三种策略：批量保留系统数据、批量采用飞书数据、或逐行手动选择 | ✓ |
| 仅"以飞书为准"或"取消" | 拉取就是以飞书数据为准更新系统，不想要就不拉取 | |

**User's choice:** 三种策略全部支持

---

## 飞书 OAuth 登录集成

### 角色映射

| Option | Description | Selected |
|--------|-------------|----------|
| 管理员预先绑定 | 管理员在系统内先把飞书用户 ID 与系统用户绑定 | |
| 首次登录时分配 | 飞书用户首次 OAuth 登录时自动创建用户并分配默认角色 | |
| 两者结合 | 已绑定的用户直接登录；未绑定的新用户首次登录后默认为 employee，管理员可调整 | ✓ |

**User's choice:** 两者结合

### Token 策略

| Option | Description | Selected |
|--------|-------------|----------|
| 系统自己的 JWT | 飞书 OAuth 验证身份后，系统发放自己的 JWT Token，后续请求用系统 JWT | ✓ |
| 直接用飞书 Token | 保留飞书的 access_token，后端每次验证时调飞书 API 确认身份 | |

**User's choice:** 系统自己的 JWT

---

## 飞书凭证与配置管理

### 凭证存储

| Option | Description | Selected |
|--------|-------------|----------|
| 环境变量 + .env | 跟 DeepSeek API Key 一样，通过环境变量配置 | |
| 系统设置界面 | 管理员可以在系统设置页面填写飞书凭证，存在数据库中（加密存储） | |
| 两种都支持 | 环境变量优先，如果没配则从数据库读取，管理员可在界面修改 | ✓ |

**User's choice:** 两种都支持

### 同步目标配置

| Option | Description | Selected |
|--------|-------------|----------|
| HR 在同步页面配置 | HR 填写飞书多维表格的 URL 或 app_token/table_id | |
| 管理员在设置页配置 | 只有管理员能配置同步目标，HR 只能触发同步操作 | ✓ |

**User's choice:** 管理员在设置页配置

### 多表格支持

| Option | Description | Selected |
|--------|-------------|----------|
| 一个表格 | 系统只同步到一个飞书多维表格 | |
| 多个表格 | 可配置多个同步目标，每个表格可独立配置字段映射 | ✓ |

**User's choice:** 多个表格

---

## 同步状态页设计

### 历史展示

| Option | Description | Selected |
|--------|-------------|----------|
| 基础信息 | 时间、方向（push/pull）、目标表格、记录数、成功/失败状态 | ✓ |
| 详细信息 | 基础信息 + 操作人、耗时、失败原因、冲突处理结果，可展开查看明细 | |
| 详细 + 可重试 | 上述详细信息 + 失败的同步可一键重试 | |

**User's choice:** 基础信息

**Notes:** 失败重试功能在后续追加讨论中确认需要（见 D-17）

### 进度反馈

| Option | Description | Selected |
|--------|-------------|----------|
| 复用 NDJSON 流式进度 | 跟文件导入一样，用 NDJSON 流式返回每条记录的同步状态，前端实时显示进度条 | ✓ |
| 简单 loading + 结果 | 点击同步后显示 loading，完成后一次性返回结果 | |

**User's choice:** 复用 NDJSON 流式进度

---

## Feature Flag 控制机制

| Option | Description | Selected |
|--------|-------------|----------|
| 环境变量控制 | FEISHU_SYNC_ENABLED 和 FEISHU_OAUTH_ENABLED 环境变量，默认 false | |
| 数据库 + 管理员 UI 控制 | 管理员可在系统设置页开关飞书功能，无需重启服务 | |
| 环境变量为主 + UI 辅助 | 环境变量控制总开关，开启后管理员可在 UI 微调子功能 | ✓ |

**User's choice:** 环境变量为主 + UI 辅助

---

## 同步字段映射 UI

| Option | Description | Selected |
|--------|-------------|----------|
| 拖拽连线式 | 左侧系统字段、右侧飞书列，拖拽连线建立映射关系，视觉直观 | ✓ |
| 下拉选择式 | 表格形式，每行左侧是系统字段，右侧下拉选择对应的飞书列 | |
| Claude 决定 | 由 Claude 根据开发复杂度和用户体验选择最合适的形式 | |

**User's choice:** 拖拽连线式

---

## Claude's Discretion

- 飞书 API SDK 选择（官方 SDK 或直接 httpx 调用）
- 同步任务的数据库模型设计
- 拖拽连线 UI 的具体前端库选择
- 飞书 OAuth 回调处理的具体实现细节
- 同步批次大小和错误重试策略

## Deferred Ideas

None — discussion stayed within phase scope
