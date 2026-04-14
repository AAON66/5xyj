# Phase 13: 基础准备与部署适配 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-04
**Phase:** 13-foundation-deploy-compat
**Areas discussed:** 审计日志 IP 问题, 技术债清理范围, 融合页面修复细节

---

## 审计日志 IP 问题

用户反馈审计日志显示 127.0.0.1，原因是通过 nginx 反向代理访问。

代码层 `get_client_ip()` 已有 X-Forwarded-For 解析，问题在部署配置侧。

| Option | Description | Selected |
|--------|-------------|----------|
| 代码+文档 | 代码增加 X-Real-IP 备选 + trusted proxy 配置项，同时输出 nginx 配置示例文档 | ✓ |
| 只修代码 | 只在代码层增强 IP 解析，nginx 配置用户自己处理 | |

**User's choice:** 代码+文档
**Notes:** 问题根因是 nginx 未配置 proxy_set_header X-Forwarded-For

---

## 技术债清理范围

研究发现 8 项 HIGH/MEDIUM 级别技术债。

| Option | Description | Selected |
|--------|-------------|----------|
| 全部清理 | 8 项全做，一次性解决 | ✓ |
| 仅关键项 | 只做依赖整理 + 废弃组件，其他留后续 | |
| 我来选 | 用户指定具体清理哪些 | |

**User's choice:** 全部清理

---

## 融合页面修复细节

### 文件计数显示

| Option | Description | Selected |
|--------|-------------|----------|
| 分区域显示 | "社保: 3 个文件 \| 公积金: 2 个文件"——分别在两个上传区域旁边显示 | |
| 汇总显示 | "已选择 5 个文件"——在开始按钮旁边统一显示 | |
| 两者都要 | 每个区域显示各自计数，底部再显示总数 | ✓ |

**User's choice:** 两者都要

### 员工主档默认值

| Option | Description | Selected |
|--------|-------------|----------|
| 智能切换 | 有主档时默认 existing，没有时自动回退到 none，无感切换 | ✓ |
| 始终 existing | 始终默认 existing，没有主档时用户自己看到 disabled 状态后手动切换 | |

**User's choice:** 智能切换

---

## Claude's Discretion

- Python 3.9 Pydantic v2 边界情况的具体修复方式
- 常量合并的具体文件路径和模块命名
- nginx 配置文档的放置位置
- 审计日志 IP 提示的具体 UI 样式

## Deferred Ideas

None — discussion stayed within phase scope
