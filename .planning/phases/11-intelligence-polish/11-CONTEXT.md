# Phase 11: Intelligence & Polish - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

跨期对比视图（两期并排比较，汇总+明细两个层级）、异常检测（基数/金额变化超阈值，按险种配置阈值，可确认/排除）、公积金全地区标准化（6 个地区全覆盖）、字段映射覆盖 UI（导入结果页内嵌+独立管理页，修正仅影响当前文件）。

不涉及：跨期趋势图表（v2）、自动异常修复（v2）、公积金新地区扩展（v2）。

</domain>

<decisions>
## Implementation Decisions

### 跨期对比视图
- **D-01:** 支持两个期间对比（选择两个月份/批次），左右并排展示
- **D-02:** 两个粒度层级：默认汇总级别（按公司/地区）+ 可展开的人员明细级别
- **D-03:** 差异展示使用表格+颜色高亮：增加用绿色，减少用红色，变化字段背景高亮
- **D-04:** 基于现有 `compare_service.py` 扩展，增加按 billing_period 对比（不仅限于 batch 对比）

### 异常检测
- **D-05:** 异常定义：同一员工相邻两期的缴费基数或各险种金额变化超过配置的百分比阈值
- **D-06:** 阈值按险种分别配置（养老、医疗、失业、工伤、生育、补充医疗、补充养老各自独立阈值）
- **D-07:** 检测结果支持 HR 标记处理状态：确认（确实异常）/ 排除（正常变动）
- **D-08:** 异常记录持久化到数据库，HR 的处理状态可追溯

### 公积金全地区标准化
- **D-09:** 6 个地区（广州、杭州、厦门、深圳、武汉、长沙）公积金样例文件全部已有
- **D-10:** 基于现有 `housing_fund_service.py` 扩展，确保全部 6 个地区的解析和标准化正确
- **D-11:** 公积金标准字段与社保标准字段统一进入 NormalizedRecord 体系

### 字段映射覆盖 UI
- **D-12:** 两个入口：导入结果页内嵌映射表（快速修正）+ 独立字段映射管理页（批量管理）
- **D-13:** HR 修正映射仅影响当前已导入的文件，后续导入仍使用自动映射
- **D-14:** 基于现有 `mapping_service.py` 和 `/api/v1/mappings` API 构建前端 UI
- **D-15:** 映射修正操作记录审计日志

### Claude's Discretion
- 跨期对比的具体 SQL 查询优化方式
- 异常检测阈值的默认值
- 公积金各地区解析器的具体实现细节
- 字段映射管理页的筛选条件设计
- 异常检测的批量运行还是实时检测

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 跨期对比
- `backend/app/services/compare_service.py` — 现有批次对比逻辑，跨期对比需在此基础上扩展
- `backend/app/api/v1/compare.py` — 现有对比 API 端点
- `backend/app/schemas/compare.py` — 对比相关 Pydantic schema

### 异常检测
- `backend/app/models/normalized_record.py` — 归一化记录模型，异常检测的数据源
- `backend/app/services/data_management_service.py` — 现有数据管理服务，异常检测可在此扩展
- `backend/app/core/config.py` — Settings 类，需新增阈值配置项

### 公积金
- `backend/app/services/housing_fund_service.py` — 现有公积金解析服务，需扩展全地区覆盖
- `data/samples/公积金/` — 公积金样例文件目录

### 字段映射
- `backend/app/services/mapping_service.py` — 现有字段映射 CRUD 服务
- `backend/app/api/v1/mappings.py` — 现有映射 API 端点
- `backend/app/services/header_normalizer.py` — 表头归一化逻辑
- `backend/app/mappings/manual_field_aliases.py` — 手工规则映射表

### 前端
- `frontend/src/theme/index.ts` — 主题配置（颜色、间距等）
- `frontend/src/services/api.ts` — Axios HTTP 客户端
- `frontend/src/App.tsx` — 路由配置

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `compare_service.py`: 已有完整的批次对比逻辑（build_compare_export_workbook, compare_batches），可扩展为按 billing_period 对比
- `housing_fund_service.py`: 已有公积金解析框架、HEADER_PATTERNS 定义、非明细行过滤逻辑
- `mapping_service.py`: 已有 HeaderMapping 的 list/update CRUD，前端只需构建 UI
- `data_management_service.py`: 已有数据质量仪表盘逻辑，异常检测可复用查询模式
- Ant Design Table 组件：跨期对比和异常列表可复用 Phase 6-8 建立的表格模式

### Established Patterns
- 路由层权限控制：`dependencies=[Depends(require_role(...))]`
- 统一响应格式：`success_response` / `error_response`
- 前端分页：useSearchParams 持久化筛选状态
- 审计日志：AuditLog 模型可复用

### Integration Points
- `backend/app/api/v1/router.py` — 注册新路由（异常检测等）
- `frontend/src/App.tsx` — 新增路由（对比页、映射管理页）
- `frontend/src/layouts/MainLayout.tsx` — 导航菜单新增入口

</code_context>

<specifics>
## Specific Ideas

- 跨期对比与现有的批次对比页面可以共享组件，区别在于选择维度（月份 vs 批次）
- 异常检测结果页应与数据管理仪表盘在同一导航区域，便于 HR 统一管理数据质量
- 字段映射修正入口应在导入流程中自然出现，不需要 HR 额外寻找

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 11-intelligence-polish*
*Context gathered: 2026-04-03*
