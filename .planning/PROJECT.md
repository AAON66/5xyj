# 社保公积金管理系统

## What This Is

公司内部社保公积金管理系统。从"Excel 融合工具"升级为完整的管理平台：支持多地区社保/公积金表格导入融合、数据标准化存储、员工自助查询、飞书多维表格双向同步，以及对外 API 接口。面向公司管理员、HR 和普通员工三类用户。

## Core Value

**社保公积金数据从多地区 Excel 汇入系统后，任何角色都能在正确的权限范围内快速查询和管理数据。**

## Requirements

### Validated

<!-- 已有代码中已经实现并可用的能力 -->

- ✓ 多地区社保 Excel 上传与解析（广州、杭州、厦门、深圳、武汉、长沙）— existing
- ✓ 多层表头自动识别与结构发现 — existing
- ✓ 规则优先 + DeepSeek LLM 兜底的字段映射 — existing
- ✓ 非明细行过滤（合计/小计/分组标题）— existing
- ✓ 标准字段归一化（canonical fields）— existing
- ✓ 员工工号匹配 — existing
- ✓ Salary 模板导出（薪酬模板）— existing, 完美运行
- ✓ Tool 模板导出（工具表最终版模板）— Phase 1 修复完成, 字段对齐正确
- ✓ NDJSON 流式进度反馈 — existing
- ✓ SQLite + SQLAlchemy 数据持久化 — existing
- ✓ 公积金表格解析（部分地区已覆盖）— existing

### Active

<!-- 本轮要建设的能力 -->

- [ ] 用户角色与权限系统（管理员 / HR / 员工三角色）
- [ ] 员工自助查询页面（工号+身份证号+姓名登录，查看个人社保公积金）
- [ ] 管理员/HR 数据管理界面（全员数据查看、筛选、导出）
- ✓ Tool 模板融合修复 — Validated in Phase 1: export-stabilization
- ✓ 导出器代码拆分（salary_exporter / tool_exporter / export_utils）— Validated in Phase 1
- [ ] 前端整体重设计（飞书风格 + 差异化高级设计感）
- [ ] 前端交互逻辑优化（使用流程顺畅化）
- [ ] 完善的 REST API 体系（供外部程序调用）
- [ ] 飞书多维表格双向同步（系统↔飞书，数据读写）
- [ ] 飞书 OAuth 登录（可选，为飞书集成准备）
- [ ] 融合后的数据作为系统录入源（从工具模式到管理系统模式转变）
- ✓ 公积金表格全地区覆盖与标准化 — Validated in Phase 11: intelligence-polish
- ✓ 跨期对比与异常检测 — Validated in Phase 11: intelligence-polish
- ✓ 字段映射管理 UI（内嵌编辑+独立页面）— Validated in Phase 11: intelligence-polish

### Out of Scope

- 移动端原生 App — 当前阶段只做 Web
- 薪资计算 — 本系统只管社保公积金数据，不涉及薪资核算
- 多租户/SaaS — 单公司内部使用
- Salary 模板融合逻辑改动 — 已完美运行，禁止修改

## Context

**现有系统状态：**
- 前后端可正常启动运行（React + FastAPI）
- 数据处理管线已打通：上传 → 解析 → 归一化 → 校验 → 匹配 → 导出
- Salary 模板导出完美，Tool 模板导出有字段映射错位问题
- 前端 UX 不顺畅，需要整体重设计
- 当前无用户认证/权限体系
- 6 个地区的社保样例已覆盖，公积金部分地区已覆盖

**技术环境：**
- Backend: FastAPI 0.115 + SQLAlchemy 2.0 + pandas + openpyxl
- Frontend: React 18 + TypeScript 5.8 + Vite 6.2
- Database: SQLite (WAL mode)
- 部署: Uvicorn

**用户角色定义：**
- **管理员**: 系统维护、高级设置、全部数据访问
- **HR**: 功能模块操作、全员数据查看与管理
- **员工**: 仅查询个人社保公积金信息（工号+身份证号+姓名验证）

**飞书集成需求：**
- 多维表格双向同步（系统数据推送到飞书 / 飞书数据拉取到系统）
- 可能需要飞书 OAuth 登录

**前端设计方向：**
- 整体风格参考飞书官网（简洁、卡片化）
- 差异化：更高级的设计感，背景与滚动配合的小设计，有审美的细节
- 不是简单复制飞书，而是在其基础上更精致

## Constraints

- **Tech Stack**: 保持 React + FastAPI + SQLite 技术栈不变
- **Salary 逻辑**: Salary 模板融合逻辑绝对不能改动
- **数据处理**: 现有的解析管线（规则优先 + LLM 兜底）保持不变
- **部署**: 单机部署，无需分布式
- **Timeline**: 无硬性截止日期，按质量优先

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 三角色权限模型（管理员/HR/员工）| 覆盖公司实际使用场景 | — Pending |
| 员工用工号+身份证号+姓名查询 | 不依赖额外账号体系，利用已有数据 | — Pending |
| 飞书多维表格双向同步 | 公司已使用飞书，数据需在两端保持一致 | — Pending |
| 前端飞书风格+差异化设计 | 用户熟悉飞书交互，但希望更精致的体验 | — Pending |
| REST API 对外开放 | 用户有自研工具需要调用系统数据 | — Pending |
| 保持 SQLite | 单公司使用，无需 PostgreSQL 的复杂度 | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-04 after Phase 11 completion*
