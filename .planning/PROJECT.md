# 社保公积金管理系统

## What This Is

公司内部社保公积金全流程管理平台。支持多地区（广州、杭州、厦门、深圳、武汉、长沙）社保/公积金 Excel 导入融合、数据标准化存储、三角色权限管理（管理员/HR/员工）、员工自助查询、跨期对比与异常检测、飞书多维表格双向同步，以及对外 REST API 接口。

## Core Value

**社保公积金数据从多地区 Excel 汇入系统后，任何角色都能在正确的权限范围内快速查询和管理数据。**

## Requirements

### Validated

- ✓ 多地区社保 Excel 上传与解析（广州、杭州、厦门、深圳、武汉、长沙）— existing
- ✓ 多层表头自动识别与结构发现 — existing
- ✓ 规则优先 + DeepSeek LLM 兜底的字段映射 — existing
- ✓ 非明细行过滤（合计/小计/分组标题）— existing
- ✓ 标准字段归一化（canonical fields）— existing
- ✓ 员工工号匹配 — existing
- ✓ Salary 模板导出（薪酬模板）— existing
- ✓ NDJSON 流式进度反馈 — existing
- ✓ SQLite + SQLAlchemy 数据持久化 — existing
- ✓ Tool 模板导出修复与字段对齐 — v1.0 Phase 1
- ✓ 导出器代码拆分（salary_exporter / tool_exporter / export_utils）— v1.0 Phase 1
- ✓ 双模板同时导出 — v1.0 Phase 1
- ✓ 回归测试覆盖 Salary 模板 — v1.0 Phase 1
- ✓ 用户角色与权限系统（管理员/HR/员工三角色 RBAC）— v1.0 Phase 2
- ✓ PyJWT 认证 + bcrypt 密码 — v1.0 Phase 2
- ✓ 员工三要素验证（工号+身份证号+姓名）— v1.0 Phase 2
- ✓ PII 保护、登录频率限制、审计日志、身份证号脱敏 — v1.0 Phase 3
- ✓ 员工主数据管理（批量导入、区域/公司筛选）— v1.0 Phase 4
- ✓ 员工自助查询页面（个人社保公积金明细）— v1.0 Phase 5
- ✓ HR 数据管理界面（级联筛选、URL 状态持久化）— v1.0 Phase 6
- ✓ Ant Design 5 飞书风格主题 + 页面动画 — v1.0 Phase 7
- ✓ 全页面重建（响应式布局、中文本地化、流程优化）— v1.0 Phase 8
- ✓ REST API 体系 + API Key 双重认证 — v1.0 Phase 9
- ✓ 飞书多维表格双向同步 + OAuth 登录 — v1.0 Phase 10
- ✓ 跨期对比与异常检测 — v1.0 Phase 11
- ✓ 公积金表格全地区标准化覆盖 — v1.0 Phase 11
- ✓ 字段映射管理 UI（独立页面+内嵌编辑器）— v1.0 Phase 11
- ✓ 集成路径修复（飞书 OAuth/字段路径、API 密钥导航）— v1.0 Phase 12

### Active

## Current Milestone: v1.1 体验优化与功能完善

**Goal:** 清理技术债、全面提升前端体验（响应式+暗黑模式+菜单重组）、补齐账号管理和融合能力短板、适配云服务器部署环境。

**Target features:**
- 融合增加个人社保承担额 + 个人公积金承担额（支持 Excel 上传或飞书同步）
- 快速融合上传文件计数、特殊规则配置（选人+选字段+覆盖值，可保存复用）
- 员工主档默认使用服务器已有主档
- 个人险种缴费基数数据修复
- 数据管理批次删除联动月份数据清理
- 全页面响应式自适应（手机端+不同窗口尺寸）
- 黑夜模式切换
- 左侧菜单多级折叠（低频功能收进高级设置）
- 设置页搜索 + 快速导航
- 数据管理筛选多选 + 已匹配/未匹配过滤
- 账号管理系统（创建账号/修改权限/改密码）
- 月度对比 diff 风格重做（左右 Excel 表格 + 差异高亮）
- 飞书功能前端完善
- 审计日志完善（真实 IP 地址等）
- 适配 Python 3.9（云服务器部署）
- v1.0 遗留技术债清理

### Out of Scope

- 移动端原生 App — 当前只做 Web
- 薪资计算 — 本系统只管社保公积金数据，不涉及薪资核算
- 多租户/SaaS — 单公司内部使用
- Salary 模板融合逻辑改动 — 已完美运行，禁止修改
- 后台定时同步飞书 — 需迁移到 PostgreSQL，v2 考虑

## Context

**v1.0 已发布状态：**
- 完整管理平台已上线：上传 → 解析 → 归一化 → 校验 → 匹配 → 导出 → 查询 → 同步
- 12 个阶段、31 个计划、56 个任务全部完成
- 378 个文件修改，53,276 行新增代码
- 开发周期：2026-03-26 → 2026-04-04（10 天）

**技术环境：**
- Backend: FastAPI 0.115 + SQLAlchemy 2.0 + pandas + openpyxl
- Frontend: React 18 + TypeScript 5.8 + Vite 6.2 + Ant Design 5
- Database: SQLite (WAL mode)
- UI: 飞书风格主题 + 响应式布局 + 页面动画
- 部署: Uvicorn

**已知技术债务：**
- Phase 7 遗留 5 个废弃组件文件（AppShell, GlobalFeedback, PageContainer, SectionState, SurfaceNotice）
- 飞书凭证管理端点无前端消费者（仅 API 可用）
- 武汉公积金样例文件缺失（测试标记为 skipif）

## Constraints

- **Tech Stack**: 保持 React + FastAPI + SQLite 技术栈不变
- **Salary 逻辑**: Salary 模板融合逻辑绝对不能改动
- **数据处理**: 现有的解析管线（规则优先 + LLM 兜底）保持不变
- **部署**: 单机部署，无需分布式

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 三角色权限模型（管理员/HR/员工）| 覆盖公司实际使用场景 | ✓ v1.0 Phase 2 |
| 员工用工号+身份证号+姓名查询 | 不依赖额外账号体系，利用已有数据 | ✓ v1.0 Phase 2 |
| PyJWT 替换 python-jose | python-jose 已废弃 | ✓ v1.0 Phase 2 |
| pwdlib BcryptHasher | 避免 argon2 依赖 | ✓ v1.0 Phase 2 |
| Ant Design 5 + 飞书风格 | 用户熟悉飞书交互，专业感 | ✓ v1.0 Phase 7 |
| REST API + API Key 双重认证 | 支持外部程序调用 | ✓ v1.0 Phase 9 |
| 飞书多维表格双向同步 | 公司已使用飞书，数据需在两端保持一致 | ✓ v1.0 Phase 10 |
| 保持 SQLite | 单公司使用，无需 PostgreSQL 的复杂度 | ✓ v1.0 |
| 可配置异常检测阈值 | 不同险种阈值不同，支持请求级覆盖 | ✓ v1.0 Phase 11 |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition:**
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions

**After each milestone:**
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-04 after v1.1 milestone started*
