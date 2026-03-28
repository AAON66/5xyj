# Phase 2: Authentication & RBAC - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 02-authentication-rbac
**Areas discussed:** 员工验证流程, 用户管理方式, Token 策略, 权限边界

---

## 员工验证流程

| Option | Description | Selected |
|--------|-------------|----------|
| 发 Token（推荐） | 验证成功后发临时 Token，可以浏览多页、查看历史 | ✓ |
| 单次查询 | 每次查询都需重新输入验证信息 | |

**User's choice:** 发 Token
**Notes:** 无

| Option | Description | Selected |
|--------|-------------|----------|
| 30 分钟（推荐） | 员工查询无需长时间保持 | ✓ |
| 2 小时 | 宽松一些 | |
| 8 小时 | 全天有效 | |

**User's choice:** 30 分钟

| Option | Description | Selected |
|--------|-------------|----------|
| 5次错误后锁定15分钟（推荐） | 防止枚举，不困扰正常员工 | ✓ |
| 3次错误后锁定30分钟 | 更严格 | |
| 不限制 | 内网环境 | |

**User's choice:** 5次错误后锁定15分钟

---

## 用户管理方式

| Option | Description | Selected |
|--------|-------------|----------|
| 数据库存储（推荐） | 界面管理用户，bcrypt 哈希密码 | ✓ |
| 配置文件 | 硬编码用户名密码 | |

**User's choice:** 数据库存储

| Option | Description | Selected |
|--------|-------------|----------|
| 不需要（推荐） | 员工通过主数据验证 | ✓ |
| 需要 | 每个员工独立账号 | |

**User's choice:** 不需要

| Option | Description | Selected |
|--------|-------------|----------|
| 首次启动自动创建（推荐） | 自动建默认管理员并提示改密 | ✓ |
| 命令行创建 | python manage.py create_admin | |

**User's choice:** 首次启动自动创建

---

## Token 策略

| Option | Description | Selected |
|--------|-------------|----------|
| 迁移到 PyJWT（推荐） | 行业标准，兼容飞书 OAuth | ✓ |
| 保持现状 | 现有 HMAC 可用 | |

**User's choice:** 迁移到 PyJWT

| Option | Description | Selected |
|--------|-------------|----------|
| 8 小时（推荐） | 一个工作日 | ✓ |
| 24 小时 | 一天 | |
| 7 天 | 一周 | |

**User's choice:** 8 小时

---

## 权限边界

| Option | Description | Selected |
|--------|-------------|----------|
| 管理员负责系统设置（推荐） | 管理员：系统设置+用户管理。HR：所有业务功能 | ✓ |
| HR 和管理员几乎一样 | 仅用户管理差异 | |

**User's choice:** 管理员负责系统设置

| Option | Description | Selected |
|--------|-------------|----------|
| 可以（推荐） | HR 是主要业务操作者 | ✓ |
| 只能查看 | 管理员负责上传导出 | |

**User's choice:** HR 可以上传和导出

---

## 额外讨论

用户关心：
1. 是否影响一键部署 — 不影响，继续用 SQLite，pip install 自动装依赖，首次启动自动建管理员
2. 是否影响融合功能 — 不影响，认证只加在路由层，不碰业务逻辑，auth_enabled 开关保留

## Claude's Discretion

- require_role 依赖注入实现方式
- 密码强度验证规则
- Token 刷新机制
- 数据库迁移策略

## Deferred Ideas

- 飞书 OAuth（Phase 10）
- API Key（Phase 9）
- 身份证号脱敏（Phase 3）
- 审计日志（Phase 3）
