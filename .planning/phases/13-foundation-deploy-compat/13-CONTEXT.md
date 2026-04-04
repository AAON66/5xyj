# Phase 13: 基础准备与部署适配 - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Python 3.9 兼容性修复、v1.0 遗留技术债全面清理、审计日志 IP 增强、快速融合页面小修复（文件计数、主档默认值）。不涉及新功能开发，仅做基础设施加固和小 UX 改进。

</domain>

<decisions>
## Implementation Decisions

### Python 3.9 适配
- **D-01:** 移除所有 `@dataclass(slots=True)` 装饰器（10+ 文件）
- **D-02:** 确保所有文件有 `from __future__ import annotations`（当前大部分已有）
- **D-03:** 依赖版本锁定：`fastapi>=0.115.0,<0.130.0`，`pandas>=2.2.3,<2.3.0`，确保兼容 3.9
- **D-04:** 不存在 `match/case` 和 `isinstance(x, A|B)` 运行时用法（已验证安全）

### 审计日志 IP 修复
- **D-05:** 增强 `get_client_ip()`：增加 `X-Real-IP` 作为备选头（有些反代用这个而不是 X-Forwarded-For）
- **D-06:** 添加 trusted proxy 配置项到 settings，防止客户端伪造 X-Forwarded-For
- **D-07:** 输出 nginx 反向代理配置示例文档（proxy_set_header X-Forwarded-For / X-Real-IP）
- **D-08:** 当审计日志检测到全部 IP 为 127.0.0.1 时，在前端审计日志页面显示提示

### 技术债清理（8 项全清）
- **D-09:** 添加 `xlrd>=2.0.0` 到 `requirements.txt`（.xls 上传依赖缺失）
- **D-10:** 清理 `requirements.server.txt`：移除未使用的 `python-jose` 和 `passlib`，考虑合并为单一 requirements 文件
- **D-11:** 移除未使用依赖：`psycopg2-binary`、`asyncpg`、`loguru`
- **D-12:** 合并 `REGION_LABELS` 到单一位置（`backend/app/mappings/regions.py`），其他文件统一 import
- **D-13:** 合并 `FILENAME_NOISE`、`DATE_PATTERN`、`_infer_company_name_from_filename` 到共享工具模块
- **D-14:** 合并 `ID_NUMBER_PATTERN`、`NON_MAINLAND_ID_NUMBER_PATTERN` 到共享 validators/constants 模块
- **D-15:** 删除 v1.0 遗留 5 个废弃组件文件：AppShell, GlobalFeedback, PageContainer, SectionState, SurfaceNotice
- **D-16:** 修复自助查询端点 `/employees/self-service/query` 缺少认证的安全隐患

### 融合页面修复
- **D-17:** 上传文件计数：社保和公积金上传区域各自显示 "N 个文件"，底部汇总显示总文件数
- **D-18:** 员工主档默认值：智能切换——服务器有主档数据时默认 `existing`，没有时自动回退到 `none`

### Claude's Discretion
- Python 3.9 Pydantic v2 边界情况的具体修复方式
- 常量合并的具体文件路径和模块命名
- nginx 配置文档的放置位置
- 审计日志 IP 提示的具体 UI 样式

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Python 3.9 适配
- `backend/app/parsers/header_extraction.py` — 含 `@dataclass(slots=True)`
- `backend/app/parsers/workbook_discovery.py` — 含 `@dataclass(slots=True)`
- `backend/app/exporters/export_utils.py` — 含 `@dataclass(slots=True)`
- `backend/app/mappings/manual_field_aliases.py` — 含 `@dataclass(slots=True)`
- `backend/app/validators/non_detail_row_filter.py` — �� `@dataclass(slots=True)`
- `backend/app/services/region_detection_service.py` — 含 `@dataclass(slots=True)`
- `backend/app/services/housing_fund_service.py` — 含 `@dataclass(slots=True)`
- `backend/app/services/matching_service.py` — 含 `@dataclass(slots=True)`
- `backend/app/services/compare_service.py` ��� 含 `@dataclass(slots=True)`
- `backend/app/services/header_normalizer.py` — 含 `@dataclass(slots=True)`

### 审计日志
- `backend/app/utils/request_helpers.py` — 当前 `get_client_ip()` 实现
- `backend/app/services/audit_service.py` — 审计日志写入服务
- `backend/app/core/config.py` — 配置项位置

### 技术债
- `backend/requirements.txt` — 主依赖文件
- `backend/requirements.server.txt` — 冲突的服务器依赖文件
- `backend/app/services/region_detection_service.py` — `REGION_LABELS` 规范位置
- `backend/app/services/import_service.py` — 含重复的 `REGION_LABELS`、`FILENAME_NOISE`、`DATE_PATTERN`
- `backend/app/exporters/template_exporter.py` — 含重复的 `REGION_LABELS`、`ID_NUMBER_PATTERN`
- `backend/app/services/matching_service.py` — 含重复的 `ID_NUMBER_PATTERN`
- `backend/app/services/aggregate_service.py` — 含重复的 `FILENAME_NOISE`
- `backend/app/api/v1/employees.py` — 自助查询端点（缺认证）
- `.planning/codebase/CONCERNS.md` — 完整技术债清单

### 融合页面
- `frontend/src/pages/SimpleAggregate.tsx` — 快速融合页面（主档默认值在 line 177，上传 UI）

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `get_client_ip()` in `backend/app/utils/request_helpers.py`: 已有 X-Forwarded-For 解析，需扩展
- `audit_service.write_audit_log()`: 所有调用点已统一使用，修改 IP 获取逻辑即全局生效
- `REGION_LABELS` canonical source: `backend/app/services/region_detection_service.py` line 20

### Established Patterns
- 所有 Python 文件以 `from __future__ import annotations` 开头
- 配置项集中在 `backend/app/core/config.py` 的 Settings 类
- 前端状态用 `useState` 管理，无外部状态库

### Integration Points
- `requirements.txt` / `requirements.server.txt`: 部署依赖入口
- `frontend/src/components/index.ts`: barrel export，删除组件需更新
- `backend/app/api/v1/router.py`: 路由注册点，自助端点认证需在此处或端点层处理

</code_context>

<specifics>
## Specific Ideas

- 审计日志全是 127.0.0.1 的场景是通过 nginx 反向代理访问时，nginx 未配置 proxy_set_header
- 需要同时提供 nginx 配置示例文档，让部署者知道该怎么配
- 文件计数要分区域（社保 N 个 | 公积金 N 个）+ 底部总计

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 13-foundation-deploy-compat*
*Context gathered: 2026-04-04*
