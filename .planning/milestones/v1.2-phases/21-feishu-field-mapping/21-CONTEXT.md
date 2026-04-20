# Phase 21: 飞书字段映射完善 - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning
**Source:** /gsd-discuss-phase interactive session

<domain>
## Phase Boundary

增强飞书字段映射 UI，使用户能看到飞书多维表格的真实字段及其类型，获得智能映射推荐和完整性校验。纯 UI 增强 + 后端新增匹配建议 API，不涉及 auth 变更或新依赖。

**现有基础设施（已完成）：**
- `FeishuClient.list_fields()` — 后端 API 已实现分页拉取飞书字段（含 type/ui_type）
- `FeishuFieldMappingPage.tsx` — ReactFlow 连线 UI 已存在（SystemFieldNode + FeishuColumnNode）
- `manual_field_aliases.py` — 同义词规则库（normalize_signature + AliasRule + MANUAL_ALIAS_RULES）
- `fetchFeishuFields()` — 前端服务已调用后端 API
- `saveSyncConfigMapping()` — 前端保存映射已实现

</domain>

<decisions>
## Implementation Decisions

### 字段类型展示方式
- Badge + Tooltip 组合：FeishuColumnNode 节点内显示简写 Tag（Ant Design Tag 组件），悬停 Tooltip 显示完整类型信息
- 颜色编码按类型分类：文本=蓝，数字=绿，日期=橙，单选/多选=紫，其他=灰
- Tag 显示 ui_type 简写（如"文本"、"数字"），Tooltip 显示完整类型名 + type 枚举值

### 同义词自动匹配策略
- 后端匹配接口：新增 API 端点，接收飞书字段列表，调用现有 manual_field_aliases 规则库返回匹配建议（含置信度）
- 前端拿到建议后自动连线，高置信度（>=0.9）用实线，低置信度（<0.9）用虚线
- 用户可手动删除自动连线或新增连线覆盖自动建议
- 匹配逻辑复用 normalize_signature + AliasRule.matches()，扩展支持中英文飞书字段名

### 未映射字段警告
- 保存时 Modal 阻断：点击保存按钮时检查关键字段（person_name, employee_id）是否已映射
- 未映射时弹出 Ant Design Modal，列出缺失的关键字段，提供"返回补全"和"仍然保存"两个按钮
- 关键字段列表：person_name（必须）、employee_id（必须）、id_number（建议）

### 映射结果预览
- 保存前弹出预览 Modal，汇总所有映射关系（系统字段 → 飞书字段）
- 表格形式展示：系统字段名 | 系统字段中文名 | 飞书字段名 | 飞书字段类型
- 未映射的关键字段高亮警告行
- 用户确认后再提交保存

### Claude's Discretion
- 后端匹配建议 API 的具体路由路径和响应格式
- 虚线/实线的具体样式参数（dashArray 等）
- 预览 Modal 和警告 Modal 的合并或分离（可以是同一个 Modal 两步流程）
- 飞书字段类型枚举值到 ui_type 的映射表

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 飞书集成
- `backend/app/services/feishu_client.py` — FeishuClient.list_fields() 实现，字段拉取 API
- `backend/app/api/v1/feishu_settings.py` — 飞书设置 API 路由
- `frontend/src/services/feishu.ts` — 前端飞书服务（fetchFeishuFields, saveSyncConfigMapping 等）
- `frontend/src/pages/FeishuFieldMapping.tsx` — 当前 ReactFlow 连线 UI 实现

### 字段映射规则
- `backend/app/mappings/manual_field_aliases.py` — 同义词规则库（AliasRule, MANUAL_ALIAS_RULES, normalize_signature）
- `backend/app/services/header_normalizer.py` — 表头标准化服务

### 研究参考
- `.planning/research/SUMMARY.md` — v1.2 研究摘要（飞书字段类型读写不对称等关键发现）

</canonical_refs>

<specifics>
## Specific Ideas

- 飞书 API 返回的字段包含 `type`（数字枚举 1=文本, 2=数字, 3=单选...）和 `field_name`
- 研究发现：飞书字段类型读写不对称 — 文本字段写入是 plain string，读取是富文本数组
- 现有 FeishuColumnNode 节点宽度 200px，需要扩展以容纳 Tag
- 现有 SYSTEM_FIELDS 列表在前端硬编码（23 个字段），与后端 CANONICAL_FIELDS 对应

</specifics>

<deferred>
## Deferred Ideas

- 映射配置模板导入导出（v2+）
- field_mapping 结构升级为含 field_id + field_type（Phase 22 或后续处理）
- LLM 辅助的语义字段匹配（需要 DeepSeek API Key）

</deferred>

---

*Phase: 21-feishu-field-mapping*
*Context gathered: 2026-04-16 via /gsd-discuss-phase*
