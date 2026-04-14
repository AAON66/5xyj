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
- ✓ 全页面响应式自适应（手机端+平板+不同窗口尺寸）— v1.1 Phase 18
- ✓ 融合增加个人社保承担额 / 个人公积金承担额（支持 Excel burden source / Feishu config 输入）— v1.1 Phase 19
- ✓ 快速融合特殊规则配置（规则保存复用 + Tool-only burden export）— v1.1 Phase 19
- ✓ 月度对比 diff 风格重做（左右 workbook 视图 + 同步滚动 + 差异高亮）— v1.1 Phase 20
- ✓ 飞书前端配置闭环（运行时开关/凭证/同步页状态感知）— v1.1 Phase 20
- ✓ Python 3.9 云服务器适配（slots=True 移除、类型注解兼容、依赖锁定）— v1.1 Phase 13
- ✓ v1.0 技术债清理（废弃组件删除、缺失测试补充）— v1.1 Phase 13
- ✓ 审计日志真实 IP 解析（X-Forwarded-For / X-Real-IP）— v1.1 Phase 13
- ✓ 内联样式 Token 化 + 暗黑模式切换（localStorage 持久化 + FOUC 预防）— v1.1 Phase 14
- ✓ 左侧菜单多级分组折叠 — v1.1 Phase 15
- ✓ 设置页搜索 + 高亮 + 自动滚动导航 — v1.1 Phase 15
- ✓ 管理员用户 CRUD + 角色权限管理 + 密码重置 — v1.1 Phase 16
- ✓ 用户自主改密 + 强制改密拦截 — v1.1 Phase 16
- ✓ 数据管理多选筛选 + 匹配状态过滤 — v1.1 Phase 17
- ✓ 批次删除联动清理（NormalizedRecords + MatchResults + ValidationIssues）— v1.1 Phase 17
- ✓ 缴费基数数据修复（payment_base/payment_salary 映射规则修复）— v1.1 Phase 17

### Active

#### Current Milestone: v1.2 飞书深度集成与登录体验升级

**Goal:** 打通飞书字段映射闭环、实现飞书 OAuth 自动登录、重做登录页面视觉体验

**Target features:**
- 飞书字段映射完善（拉取飞书多维表格实际字段，支持与系统标准字段一一对应）
- 飞书 OAuth 自动登录（扫码/自动登录 + 按姓名/工号自动匹配绑定系统用户）
- 登录页面改版（左右分栏 + Three.js 3D 粒子波浪动态背景）

### Out of Scope

- 移动端原生 App — 当前只做 Web
- 薪资计算 — 本系统只管社保公积金数据，不涉及薪资核算
- 多租户/SaaS — 单公司内部使用
- Salary 模板基础险种汇总逻辑扩散改动 — Phase 19 后个人承担额只保留在 Tool 模板
- 后台定时同步飞书 — 需迁移到 PostgreSQL，v2 考虑

## Context

**v1.1 已发布状态（2026-04-14）：**
- v1.0 + v1.1 共 20 个阶段、59 个计划、113 个任务全部完成
- v1.1 新增 177 个文件修改，+20,069 / -5,653 行代码
- v1.1 开发周期：2026-03-20 → 2026-04-14（25 天）
- 前端 16,008 行 TS/TSX，后端 28,488 行 Python

**技术环境：**
- Backend: FastAPI 0.115 + SQLAlchemy 2.0 + pandas + openpyxl (Python 3.9+)
- Frontend: React 18 + TypeScript 5.8 + Vite 6.2 + Ant Design 5
- Database: SQLite (WAL mode)
- UI: 飞书风格主题 + 暗黑模式 + 响应式布局 + 页面动画
- 部署: Uvicorn + nginx (X-Forwarded-For)

**已知技术债务：**
- 武汉公积金样例文件缺失（测试标记为 skipif）
- Nyquist VALIDATION.md 模板未补齐（Phase 13-17）
- 飞书 burden source / 飞书 tenant 凭证需 staging smoke test

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
| Python 3.9 优先适配 | 阻断云服务器部署 | ✓ v1.1 Phase 13 |
| 零新依赖策略 | AntD 5 内置暗黑模式/响应式/多级菜单 | ✓ v1.1 |
| 样式 Token 化先于暗黑模式 | 329 处硬编码样式需先迁移 | ✓ v1.1 Phase 14 |
| 个人承担额仅影响 Tool 模板 | Salary 模板基础险种逻辑不扩散 | ✓ v1.1 Phase 19 |
| 飞书设置 runtime DB 持久化 | system_settings 表 + effective settings 合并 | ✓ v1.1 Phase 20 |
| Sider 两模式保持深色 #1F2329 | 暗黑模式下与内容区有视觉区分 | ✓ v1.1 Phase 14 |

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
*Last updated: 2026-04-14 after v1.2 milestone started*
