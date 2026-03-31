# Phase 9: API System - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-31
**Phase:** 09-api-system
**Areas discussed:** API Key 认证设计, API 版本与路由结构, 响应格式规范化, API 文档定制

---

## API Key 认证设计

### Q1: API Key 绑定层级

| Option | Description | Selected |
|--------|-------------|----------|
| 绑定到用户（推荐） | API Key 关联到具体 admin/HR 用户，继承角色权限，审计可追溯 | ✓ |
| 绑定到角色 | API Key 只绑定角色，不关联用户，管理简单但审计弱 | |
| 独立实体 | API Key 是独立"服务账号"，有自己的权限配置 | |

**User's choice:** 绑定到用户（推荐）

### Q2: API Key 过期机制

| Option | Description | Selected |
|--------|-------------|----------|
| 永不过期（推荐） | 创建后长期有效，管理员可手动禁用/删除 | ✓ |
| 可设置过期时间 | 创建时可选填过期日期，到期自动失效 | |

**User's choice:** 永不过期（推荐）

### Q3: API Key 数量限制

| Option | Description | Selected |
|--------|-------------|----------|
| 最多 5 个（推荐） | 每用户最多 5 个 Key | ✓ |
| 只要 1 个 | 每用户只能有一个活跃 Key | |
| 不限制 | 不限数量 | |

**User's choice:** 最多 5 个（推荐）

### Q4: API Key 传递方式

| Option | Description | Selected |
|--------|-------------|----------|
| Header: X-API-Key（推荐） | 通过请求头 X-API-Key 传递 | ✓ |
| Header: Authorization | 用 Authorization: Bearer <key>，和 JWT 共用同一个头 | |
| Query 参数 | 通过 ?api_key=xxx 传递 | |

**User's choice:** Header: X-API-Key（推荐）

---

## API 版本与路由结构

### Q1: 路由结构

| Option | Description | Selected |
|--------|-------------|----------|
| 共用 /api/v1/（推荐） | 外部和前端调用同一套端点，仅认证方式不同 | ✓ |
| 独立 /api/external/ | 外部 API 单独一套路由 | |
| 共用 + 白名单 | 共用端点但用配置控制哪些允许 API Key | |

**User's choice:** 共用 /api/v1/（推荐）

### Q2: 开放范围

| Option | Description | Selected |
|--------|-------------|----------|
| 社保查询 | 查询社保明细、汇总、筛选 | ✓ |
| 员工管理 | 员工主数据 CRUD | ✓ |
| 导入导出 | 触发文件导入、下载导出结果 | ✓ |
| 什么都开放 | 所有现有端点全部开放 | ✓ |

**User's choice:** 全部开放，涉密功能仅管理员 API Key 可访问，只有管理员能设置 API 开放权限
**Notes:** 用户强调"部分涉密功能仅管理员开放，API只有管理员能够设置开放"

---

## 响应格式规范化

### Q1: 响应格式调整

| Option | Description | Selected |
|--------|-------------|----------|
| 保持现有 + 加分页（推荐） | 保留现有结构，列表接口加 pagination 字段 | ✓ |
| 完全不动 | 现有格式已够用 | |
| 重新设计 | 采用更标准的 REST 信封格式 | |

**User's choice:** 保持现有 + 加分页（推荐）

### Q2: 错误码体系

| Option | Description | Selected |
|--------|-------------|----------|
| 统一错误码前缀（推荐） | 按模块分类：AUTH_001, IMPORT_002 等 | ✓ |
| HTTP 状态码够用 | 不需要自定义错误码 | |
| 现有就行 | 当前已有部分 error code，不系统化整理 | |

**User's choice:** 统一错误码前缀（推荐）

---

## API 文档定制

### Q1: 文档定制内容

| Option | Description | Selected |
|--------|-------------|----------|
| 中文描述（推荐） | 端点、参数、模型加中文描述 | ✓ |
| 分组标签（推荐） | 端点按功能分组 | ✓ |
| 示例数据 | 关键端点提供示例值 | ✓ |
| 隐藏内部端点 | 内部端点不在文档展示 | ✓ |

**User's choice:** 全选，额外要求生成 MD 文档和提供文档 API 端点
**Notes:** 用户要求"API文档做个md文档和只在内部展示，并且做一个api可以直接调用api文档的api"

### Q2: 文档访问控制

| Option | Description | Selected |
|--------|-------------|----------|
| 仅管理员可见（推荐） | 只有 admin 角色登录后才能看到 /docs | ✓ |
| 登录后可见 | admin 和 HR 都能访问 | |
| 完全公开 | 任何人都可访问 | |

**User's choice:** 仅管理员可见（推荐）

---

## Claude's Discretion

- API Key 生成算法和长度
- API Key 数据库存储方式（哈希 vs 明文）
- 分页参数默认值和最大值
- 错误码编号规则细节
- Markdown 文档格式和章节结构

## Deferred Ideas

None — discussion stayed within phase scope
