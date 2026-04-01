# Phase 10: Feishu Integration - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

系统数据与飞书多维表格（Bitable）双向同步：HR/管理员可一键推送社保数据到飞书多维表格，也可从飞书拉取更新数据并预览冲突。同步操作全部为手动触发，无后台自动同步。同步状态页展示历史记录。可选的飞书 OAuth 登录通过 feature flag 控制（默认关闭）。

不涉及：后台定时同步（v2）、飞书机器人通知（v2）、公积金数据全地区标准化（Phase 11）。

</domain>

<decisions>
## Implementation Decisions

### 同步数据范围与粒度
- **D-01:** 支持两种粒度的推送：归一化后的人员明细（NormalizedRecord 级别，每人每月一行）和汇总级别数据（按公司+地区+月份汇总），分别对应不同的多维表格
- **D-02:** 用户可选择推送明细或汇总，每种粒度对应独立配置的多维表格

### 多维表格列结构与字段映射
- **D-03:** HR 先在飞书手动创建多维表格并定义列结构，系统按列名自动匹配或由管理员手动配置映射关系
- **D-04:** 字段映射 UI 采用拖拽连线式设计：左侧系统字段、右侧飞书列，拖拽建立映射关系
- **D-05:** 支持配置多个同步目标（多个多维表格），每个表格可独立配置字段映射

### 拉取映射与推送重复处理
- **D-06:** 拉取时复用推送时记录的映射关系（反向使用），前提是先推送过才能拉取
- **D-07:** 推送时如果飞书表格已有相同员工+月份的数据，提示用户选择：覆盖/跳过/取消，展示差异让 HR 决策

### 冲突处理与预览
- **D-08:** 拉取时冲突预览同时支持两种视图：只显示有差异的行（过滤一致数据），以及批量策略选择（概要+明细展开）
- **D-09:** 冲突解决策略支持三种：以系统为准、以飞书为准、逐条选择。三种策略在预览界面中可选

### 飞书 OAuth 登录
- **D-10:** 飞书 OAuth 登录成功后，系统发放自己的 JWT Token（与密码登录统一），后续请求使用系统 JWT
- **D-11:** 角色确定采用两者结合：已绑定的用户直接登录获得已绑定角色权限；未绑定的新用户首次登录默认为 employee 角色，管理员可后续调整
- **D-12:** 飞书 OAuth 通过 feature flag 控制，默认关闭

### 凭证与配置管理
- **D-13:** 飞书 App ID/Secret 两种配置方式：环境变量优先（FEISHU_APP_ID / FEISHU_APP_SECRET），如果未配则从数据库读取；管理员可在系统设置页面修改（加密存储）
- **D-14:** 多维表格同步目标由管理员在系统设置页配置（app_token / table_id），HR 只能触发同步操作
- **D-15:** 支持配置多个多维表格作为同步目标

### 同步状态页
- **D-16:** 同步历史列表展示基础信息：时间、方向（push/pull）、目标表格、记录数、成功/失败状态
- **D-17:** 失败的同步任务支持一键重试
- **D-18:** 同步进行中复用 NDJSON 流式进度反馈（与文件导入一致），前端实时显示进度条

### Feature Flag 控制
- **D-19:** 环境变量为主开关（FEISHU_SYNC_ENABLED / FEISHU_OAUTH_ENABLED，默认 false），开启后管理员可在 UI 微调子功能（如单独关闭 OAuth 保留同步）
- **D-20:** feature flag 关闭时，前端不显示飞书相关菜单项和路由

### Claude's Discretion
- 飞书 API SDK 选择（官方 SDK 或直接 httpx 调用）
- 同步任务的数据库模型设计（SyncJob / SyncConfig 等）
- 拖拽连线 UI 的具体前端库选择
- 飞书 OAuth 回调处理的具体实现细节
- 同步批次大小和错误重试策略

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 飞书开放平台
- 飞书多维表格 API 文档（需在线查阅）— Bitable CRUD 操作、字段类型、分页查询
- 飞书 OAuth 2.0 文档（需在线查阅）— 授权流程、token 刷新、用户信息获取

### 现有认证体系
- `backend/app/core/auth.py` — JWT 认证逻辑，飞书 OAuth 登录需在此基础上扩展
- `backend/app/dependencies.py` — 双认证依赖注入（JWT + API Key），飞书 OAuth 需与其共存
- `backend/app/models/user.py` — 用户模型，需扩展飞书用户绑定字段

### 现有数据模型
- `backend/app/models/normalized_record.py` — 归一化记录模型，推送数据的来源
- `backend/app/models/import_batch.py` — 导入批次模型，同步任务可参考其设计
- `backend/app/schemas/` — Pydantic schema 目录，需新增飞书相关 schema

### 现有流式进度
- `backend/app/api/v1/imports.py` — NDJSON 流式进度反馈实现，同步进度可复用此模式

### 配置体系
- `backend/app/core/config.py` — Settings 类，需新增飞书相关环境变量
- `.env.example` — 环境变量文档，需新增飞书配置项

### 前端架构
- `frontend/src/services/api.ts` — Axios HTTP 客户端，飞书相关 API 调用复用此实例
- `frontend/src/App.tsx` — 路由配置，需新增飞书同步和设置页面路由

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `httpx` HTTP 客户端：后端已用于 DeepSeek API 调用（`llm_mapping_service.py`），可复用同样的模式调用飞书 API
- NDJSON 流式进度：`imports.py` 中已实现 StreamingResponse + NDJSON 模式，同步进度可直接复用
- 统一响应格式：`responses.py` 中的 `success_response` / `error_response` 已建立
- Ant Design 组件体系：Phase 7-8 已建立完整的 UI 组件和主题系统
- 审计日志：`audit_log.py` 模型可复用记录同步操作日志

### Established Patterns
- 路由层权限控制：`dependencies=[Depends(require_role(...))]`
- 环境变量 + Settings 类配置模式
- SQLAlchemy 2.0 模型定义 + Alembic 迁移
- 前端 React Router + 角色感知路由

### Integration Points
- `backend/app/api/v1/router.py` — 注册飞书同步相关路由
- `backend/app/core/config.py` — 添加飞书配置项
- `backend/app/models/` — 新增 SyncConfig / SyncJob 等模型
- `frontend/src/App.tsx` — 新增飞书同步页面路由
- `frontend/src/components/Layout/` — 导航菜单新增飞书同步入口（受 feature flag 控制）

</code_context>

<specifics>
## Specific Ideas

- 拉取功能依赖先推送过的映射关系，这意味着同一个多维表格必须先执行过至少一次推送才能拉取
- 拖拽连线式字段映射 UI 需要视觉直观，左侧系统字段列表、右侧飞书列名列表，连线表示对应关系
- 冲突预览需要在列表和详情两个层级都可用：列表层看哪些行有冲突，点击行可展开看字段级差异
- 飞书凭证未配置时，飞书相关功能应优雅降级（显示配置引导而非报错）

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 10-feishu-integration*
*Context gathered: 2026-03-31*
