# Phase 21: 飞书字段映射完善 - Research

**Researched:** 2026-04-16
**Domain:** 飞书 Bitable 字段映射 UI 增强（类型展示 + 同义词匹配 + 完整性校验）
**Confidence:** HIGH

## Summary

Phase 21 是纯 UI 增强 + 后端新增一个匹配建议 API，所有核心基础设施已就绪。后端 `FeishuClient.list_fields()` 已实现分页拉取飞书字段（含 type），前端 `FeishuFieldMappingPage.tsx` 已有 ReactFlow 连线 UI，`manual_field_aliases.py` 同义词规则库已有 90+ 条规则。

核心改动集中在四个方面：(1) 后端 `FeishuFieldInfo` schema 扩展 `ui_type` 字段并在 API 中提取；(2) 前端 `FeishuColumnNode` 组件增加类型 Tag + Tooltip；(3) 后端新增匹配建议 API，复用现有 `AliasRule.matches()` 对飞书字段名做同义词匹配；(4) 前端保存时增加关键字段未映射警告 Modal 和映射预览 Modal。

**Primary recommendation:** 后端扩展 `ui_type` 到 `FeishuFieldInfo` schema 并新增 `/suggest-mapping` 端点，前端增强 `FeishuColumnNode` 显示类型 Tag，保存流程增加两步 Modal（预览 + 警告）。零新依赖。

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- 字段类型展示：Badge + Tooltip 组合，FeishuColumnNode 内 Ant Design Tag，悬停 Tooltip 显示完整类型
- 颜色编码：文本=蓝，数字=绿，日期=橙，单选/多选=紫，其他=灰
- Tag 显示 ui_type 简写（如"文本"、"数字"），Tooltip 显示完整类型名 + type 枚举值
- 同义词匹配：后端新增 API 端点，调用现有 manual_field_aliases 规则库返回匹配建议（含置信度）
- 前端拿到建议后自动连线，高置信度（>=0.9）实线，低置信度（<0.9）虚线
- 用户可手动删除自动连线或新增连线覆盖自动建议
- 未映射字段警告：保存时 Modal 阻断，检查 person_name（必须）、employee_id（必须）、id_number（建议）
- 映射预览：保存前弹出预览 Modal，表格形式展示系统字段名 | 中文名 | 飞书字段名 | 飞书字段类型

### Claude's Discretion
- 后端匹配建议 API 的具体路由路径和响应格式
- 虚线/实线的具体样式参数（dashArray 等）
- 预览 Modal 和警告 Modal 的合并或分离（可以是同一个 Modal 两步流程）
- 飞书字段类型枚举值到 ui_type 的映射表

### Deferred Ideas (OUT OF SCOPE)
- 映射配置模板导入导出（v2+）
- field_mapping 结构升级为含 field_id + field_type（Phase 22 或后续处理）
- LLM 辅助的语义字段匹配（需要 DeepSeek API Key）
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FMAP-01 | 用户可在飞书字段映射页看到从飞书多维表格 API 拉取的真实字段列表 | 后端 API 已实现（`get_feishu_fields` 端点），前端 `fetchFeishuFields` 已调用。当前已可工作，需确认 ui_type 是否需要展示 |
| FMAP-02 | 用户可在映射 UI 中看到每个飞书字段的类型标签（文本/数字/单选等） | 需扩展 `FeishuFieldInfo` schema 增加 `ui_type`，前端 `FeishuColumnNode` 增加 Tag 组件，颜色编码按 CONTEXT.md 决策 |
| FMAP-03 | 用户保存映射时，系统检查核心字段是否已映射，未映射则弹出警告 | 前端保存流程增加 Modal 阻断逻辑，关键字段列表：person_name, employee_id, id_number |
| FMAP-04 | 系统基于中英文同义词库自动推荐字段映射候选项 | 后端新增匹配建议 API，复用 `MANUAL_ALIAS_RULES` + `normalize_signature`，前端替换当前简单的 label 包含匹配 |
</phase_requirements>

## Standard Stack

### Core（零新依赖）

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @xyflow/react | ^12.10.2 | ReactFlow 连线 UI | 已安装，用于字段映射可视化连线 |
| antd | ^5.29.3 | Tag, Tooltip, Modal 组件 | 已安装，项目 UI 框架 |
| React | ^18.3.1 | 前端框架 | 已安装 |
| FastAPI | existing | 后端框架 | 已安装 |

[VERIFIED: frontend/package.json]

**Installation:** 无需安装任何新依赖。

## Architecture Patterns

### 现有文件结构（只修改，不新建）

```
backend/app/
├── api/v1/feishu_settings.py    # 新增 suggest-mapping 端点
├── schemas/feishu.py            # 扩展 FeishuFieldInfo 加 ui_type
├── mappings/manual_field_aliases.py  # 已有，直接复用
└── services/header_normalizer.py    # 已有，参考匹配逻辑

frontend/src/
├── pages/FeishuFieldMapping.tsx  # 主要修改文件
└── services/feishu.ts           # 新增 suggestMapping API 调用
```

### Pattern 1: 飞书字段类型枚举映射表

**What:** 将飞书 API 返回的 `type`（数字）+ `ui_type`（字符串）转换为用户可读的中文标签和颜色

**Example:**
```typescript
// 飞书字段类型到中文标签的映射
const FEISHU_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  // 文本类 — 蓝色
  'Text': { label: '文本', color: 'blue' },
  'Email': { label: '邮箱', color: 'blue' },
  'Barcode': { label: '条码', color: 'blue' },
  'Phone': { label: '电话', color: 'blue' },
  'Url': { label: '链接', color: 'blue' },
  // 数字类 — 绿色
  'Number': { label: '数字', color: 'green' },
  'Progress': { label: '进度', color: 'green' },
  'Currency': { label: '货币', color: 'green' },
  'Rating': { label: '评分', color: 'green' },
  // 日期类 — 橙色
  'DateTime': { label: '日期', color: 'orange' },
  'CreatedTime': { label: '创建时间', color: 'orange' },
  'ModifiedTime': { label: '更新时间', color: 'orange' },
  // 选择类 — 紫色
  'SingleSelect': { label: '单选', color: 'purple' },
  'MultiSelect': { label: '多选', color: 'purple' },
  // 其他 — 灰色
  'Checkbox': { label: '复选框', color: 'default' },
  'User': { label: '人员', color: 'default' },
  'Attachment': { label: '附件', color: 'default' },
  'Formula': { label: '公式', color: 'default' },
  'Lookup': { label: '查找引用', color: 'default' },
  'SingleLink': { label: '单向关联', color: 'default' },
  'DuplexLink': { label: '双向关联', color: 'default' },
  'Location': { label: '地理位置', color: 'default' },
  'GroupChat': { label: '群组', color: 'default' },
  'CreatedUser': { label: '创建人', color: 'default' },
  'ModifiedUser': { label: '修改人', color: 'default' },
  'AutoNumber': { label: '自动编号', color: 'default' },
};
```
[VERIFIED: https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-field/guide]

### Pattern 2: 后端匹配建议 API 响应格式

**What:** 新增 API 端点接收飞书字段名列表，返回每个字段的匹配建议

**推荐路由:** `POST /feishu/settings/configs/{config_id}/suggest-mapping`

```python
# 请求体
{"feishu_fields": [{"field_name": "姓名", "field_id": "fldXXX"}, ...]}

# 响应
{
  "data": {
    "suggestions": [
      {
        "feishu_field_id": "fldXXX",
        "feishu_field_name": "姓名",
        "canonical_field": "person_name",
        "confidence": 0.99,
        "matched_rule": "姓名"
      },
      {
        "feishu_field_id": "fldYYY",
        "feishu_field_name": "养老保险(单位)",
        "canonical_field": "pension_company",
        "confidence": 0.93,
        "matched_rule": "社保公司 + 养老"
      },
      ...
    ],
    "unmatched": ["fldZZZ"]
  }
}
```

### Pattern 3: 自动连线 Edge 样式区分

**What:** 高置信度（>=0.9）用实线，低置信度（<0.9）用虚线

```typescript
const buildEdgeFromSuggestion = (
  sysKey: string, fsFieldId: string, confidence: number
): Edge => ({
  id: `edge-${sysKey}-${fsFieldId}`,
  source: `sys-${sysKey}`,
  target: `fs-${fsFieldId}`,
  type: 'smoothstep',
  style: {
    stroke: colors.BRAND,
    strokeWidth: 2,
    strokeDasharray: confidence >= 0.9 ? undefined : '5 5',
  },
  data: { confidence, isAutoSuggestion: true },
});
```

### Pattern 4: 两步 Modal 保存流程

**What:** 保存按钮点击后先检查 -> 预览 -> 确认

```
用户点击"保存映射"
  ↓
检查关键字段映射状态
  ↓ （有未映射的关键字段）
弹出警告 Modal
  → "返回补全" → 关闭 Modal
  → "仍然保存" → 进入预览 Modal
  ↓ （全部关键字段已映射）
弹出预览 Modal
  → 确认 → 提交保存
  → 取消 → 关闭
```

### Anti-Patterns to Avoid
- **不要在前端硬编码 type 到 ui_type 的映射**：飞书 API 已返回 `ui_type` 字段，后端应直接透传，前端只做 `ui_type` 到中文标签/颜色的映射
- **不要丢弃低置信度建议**：低置信度也应展示（虚线），让用户决定
- **不要用 type 数字做分类**：type=1 对应文本/邮箱/条码三种，必须用 ui_type 区分

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 字段同义词匹配 | 前端自行实现匹配逻辑 | 后端 `MANUAL_ALIAS_RULES` + `normalize_signature` | 规则库 90+ 条，含 region 过滤和 excludes 逻辑，前端简单 includes 匹配远不够 |
| 类型标签渲染 | 自定义 div + CSS | Ant Design `<Tag>` + `<Tooltip>` | 已有组件，样式统一 |
| 连线 UI | 自定义 SVG 拖拽 | ReactFlow (`@xyflow/react`) | 已有集成 |
| Modal 交互 | 自定义弹窗 | Ant Design `<Modal>` | 已有组件 |

**Key insight:** 当前前端 `handleAutoMatch` 只做了简单的 label 精确匹配和包含匹配，无法识别中文同义词（如"养老保险(单位)" vs "pension_company"）。必须将匹配逻辑移到后端复用已有的 90+ 条 AliasRule。

## Common Pitfalls

### Pitfall 1: FeishuFieldInfo 缺少 ui_type
**What goes wrong:** 当前后端 `FeishuFieldInfo` schema 只有 `field_type: int`（对应 type），没有 `ui_type` 字段。飞书 API 实际返回 `ui_type`，但被 `get_feishu_fields` 端点丢弃了。
**Why it happens:** v1.1 实现时只关注了字段名和 ID，类型展示不在当时的需求范围。
**How to avoid:** 修改 `FeishuFieldInfo` schema 增加 `ui_type: Optional[str] = None`，在 `get_feishu_fields` 端点中提取 `f.get("ui_type", "")`。
**Warning signs:** 前端只能看到 type=1 但分不清是文本还是邮箱还是条码。
[VERIFIED: 代码分析 — backend/app/schemas/feishu.py 第 135-139 行]

### Pitfall 2: AliasRule 对飞书字段名的适配
**What goes wrong:** 现有 `MANUAL_ALIAS_RULES` 是为社保 Excel 表头设计的，飞书多维表格的字段名可能更简洁（如"姓名"而非"职工姓名"），也可能包含英文（如"Name"、"pension_company"）。
**Why it happens:** 飞书多维表格是用户自定义字段名，可能用中文也可能用英文，与 Excel 表头习惯不同。
**How to avoid:** 匹配建议 API 中，对飞书字段名先做 `normalize_signature` 然后遍历 MANUAL_ALIAS_RULES 的 patterns。对于英文字段名，增加一组简单的英文别名映射（canonical field key 本身就是英文，如 `person_name` 直接匹配 `person_name`、`personname` 等）。
**Warning signs:** 英文命名的飞书字段全部显示为"未匹配"。

### Pitfall 3: ReactFlow Edge 样式 defaultEdgeOptions 覆盖
**What goes wrong:** 当前 `defaultEdgeOptions` 在组件 useMemo 中定义，所有 edge 共享相同样式。自动匹配需要区分实线/虚线，但新 edge 可能被 defaultEdgeOptions 覆盖 `strokeDasharray`。
**Why it happens:** ReactFlow 的 `defaultEdgeOptions` 会作为 fallback 合并到每条 edge 上。
**How to avoid:** 自动匹配生成的 edge 必须显式设置 `style` 属性（含或不含 `strokeDasharray`），不依赖 defaultEdgeOptions。
**Warning signs:** 所有自动匹配连线都显示相同样式，无法区分置信度。

### Pitfall 4: FeishuColumnNode 宽度不够
**What goes wrong:** 当前 FeishuColumnNode 宽度 200px，加了 Tag 后字段名较长时会溢出。
**Why it happens:** Tag 组件额外占用约 40-60px 宽度。
**How to avoid:** 将 FeishuColumnNode 宽度扩展到 260-280px，或使用 flex 布局让字段名 truncate + ellipsis。同时需要调整飞书节点的 x 坐标（从 450 增大到 500-520）以保持连线美观。

### Pitfall 5: 前端 SYSTEM_FIELDS 与后端 CANONICAL_FIELDS 不完全对齐
**What goes wrong:** 前端硬编码了 23 个 SYSTEM_FIELDS，后端 CANONICAL_FIELDS 有 34 个。匹配建议 API 返回的 canonical_field 可能不在前端列表中。
**Why it happens:** 前端只展示了最常用的字段子集。
**How to avoid:** 匹配建议 API 只返回前端 SYSTEM_FIELDS 列表中存在的 canonical_field 匹配结果。前端可以在请求中传入 system_fields 列表，或后端硬编码同样的子集。

## Code Examples

### 飞书 API 返回的字段数据结构示例

```json
// GET /bitable/v1/apps/{app_token}/tables/{table_id}/fields 响应中每个 item
{
  "field_id": "fldXXXXXXX",
  "field_name": "姓名",
  "type": 1,
  "ui_type": "Text",
  "property": {},
  "description": null
}
```
[VERIFIED: https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-field/guide]

### 扩展后的 FeishuFieldInfo Schema

```python
class FeishuFieldInfo(BaseModel):
    field_id: str
    field_name: str
    field_type: int
    ui_type: Optional[str] = None  # 新增：如 "Text", "Number", "SingleSelect"
    description: Optional[str] = None
```

### 匹配建议逻辑（后端核心）

```python
from backend.app.mappings.manual_field_aliases import (
    MANUAL_ALIAS_RULES, normalize_signature
)

def suggest_field_mapping(
    feishu_fields: list[dict],
    system_fields: list[str] | None = None,
) -> list[dict]:
    """对每个飞书字段名，用 AliasRule 规则库匹配最佳 canonical_field。"""
    suggestions = []
    for ff in feishu_fields:
        field_name = ff["field_name"]
        best_match = None
        best_confidence = 0.0
        best_rule = ""

        for rule in MANUAL_ALIAS_RULES:
            if system_fields and rule.canonical_field not in system_fields:
                continue
            if rule.matches(field_name, region=None):
                if rule.confidence > best_confidence:
                    best_match = rule.canonical_field
                    best_confidence = rule.confidence
                    best_rule = " + ".join(rule.patterns)

        # 英文精确匹配 fallback
        if best_match is None and system_fields:
            normalized = normalize_signature(field_name)
            for sf in system_fields:
                if normalized == normalize_signature(sf):
                    best_match = sf
                    best_confidence = 1.0
                    best_rule = "exact_key_match"
                    break

        if best_match:
            suggestions.append({
                "feishu_field_id": ff["field_id"],
                "feishu_field_name": field_name,
                "canonical_field": best_match,
                "confidence": best_confidence,
                "matched_rule": best_rule,
            })
    return suggestions
```

### 飞书字段类型完整枚举表（供前端映射）

| type | ui_type | 中文标签 | 颜色 |
|------|---------|---------|------|
| 1 | Text | 文本 | blue |
| 1 | Email | 邮箱 | blue |
| 1 | Barcode | 条码 | blue |
| 2 | Number | 数字 | green |
| 2 | Progress | 进度 | green |
| 2 | Currency | 货币 | green |
| 2 | Rating | 评分 | green |
| 3 | SingleSelect | 单选 | purple |
| 4 | MultiSelect | 多选 | purple |
| 5 | DateTime | 日期 | orange |
| 7 | Checkbox | 复选框 | default |
| 11 | User | 人员 | default |
| 13 | Phone | 电话 | blue |
| 15 | Url | 链接 | blue |
| 17 | Attachment | 附件 | default |
| 18 | SingleLink | 单向关联 | default |
| 19 | Lookup | 查找引用 | default |
| 20 | Formula | 公式 | default |
| 21 | DuplexLink | 双向关联 | default |
| 22 | Location | 地理位置 | default |
| 23 | GroupChat | 群组 | default |
| 1001 | CreatedTime | 创建时间 | orange |
| 1002 | ModifiedTime | 更新时间 | orange |
| 1003 | CreatedUser | 创建人 | default |
| 1004 | ModifiedUser | 修改人 | default |
| 1005 | AutoNumber | 自动编号 | default |

[VERIFIED: https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-field/guide]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 前端 label 包含匹配 | 后端规则库同义词匹配 | Phase 21 | 从 ~5 个精确匹配提升到 90+ 条规则覆盖 |
| 只显示字段名 | 字段名 + 类型 Tag + Tooltip | Phase 21 | 用户能区分同名但不同类型的字段 |
| 直接保存无检查 | 保存前预览 + 关键字段警告 | Phase 21 | 防止遗漏核心映射导致同步失败 |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | 飞书 list_fields API 返回数据中包含 `ui_type` 字段 | Pitfall 1 / Code Examples | 如果不返回 ui_type，前端只能用 type 数字做粗分类（type=1 无法区分文本/邮箱/条码） |
| A2 | 飞书多维表格字段名可能使用英文 | Pitfall 2 | 如果全是中文则英文 fallback 匹配不需要，但无害 |

**A1 说明:** 飞书官方文档明确列出 list_fields 响应包含 ui_type [CITED: https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-field/guide]。但实际 API 行为需在有凭证的环境中验证。

## Open Questions

1. **飞书 API 是否一定返回 ui_type 字段？**
   - What we know: 官方文档说返回 ui_type [CITED: https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-field/guide]
   - What's unclear: 旧版 API 或特定权限下是否可能不返回
   - Recommendation: 后端用 `f.get("ui_type", None)` 安全提取，前端对 ui_type 为 None 时 fallback 到 type 数字做粗分类

2. **匹配建议是否需要传入 region 参数？**
   - What we know: `AliasRule` 支持 `regions` 过滤，部分规则限定地区（如 wuhan, xiamen）
   - What's unclear: 飞书多维表格字段是全局的，不按地区分
   - Recommendation: 匹配建议 API 不传 region（传 None），让所有无地区限定的规则参与匹配

## Project Constraints (from CLAUDE.md)

- **Rules before LLM**: 规则映射优先于 LLM，本 Phase 只用规则，不涉及 DeepSeek
- **Keep provenance**: 每条标准化结果都必须可追溯到原始文件和原始行 -- 匹配建议需返回 matched_rule
- **No fixed-position parsing**: 不假设固定结构 -- 不适用于本 Phase（UI 增强）
- **Frontend/Backend separation**: React 负责展示，FastAPI 负责逻辑 -- 匹配逻辑在后端，前端只展示结果

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | 无独立 config，直接 `pytest` 运行 |
| Quick run command | `pytest tests/test_feishu_sync.py -x` |
| Full suite command | `pytest` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FMAP-01 | 飞书字段列表拉取（含 ui_type） | unit | `pytest tests/test_feishu_field_mapping.py::test_feishu_fields_include_ui_type -x` | No -- Wave 0 |
| FMAP-02 | 字段类型 Tag 展示 | manual-only | 前端视觉验证 | N/A |
| FMAP-03 | 未映射关键字段警告 | manual-only | 前端交互验证 | N/A |
| FMAP-04 | 同义词匹配建议 API | unit | `pytest tests/test_feishu_field_mapping.py::test_suggest_mapping -x` | No -- Wave 0 |

### Wave 0 Gaps

- [ ] `tests/test_feishu_field_mapping.py` -- 覆盖 FMAP-01 (ui_type 透传) 和 FMAP-04 (匹配建议逻辑)
- [ ] 测试用例：飞书字段名 "姓名" -> person_name (confidence >= 0.9)
- [ ] 测试用例：飞书字段名 "person_name" -> person_name (英文精确匹配)
- [ ] 测试用例：飞书字段名 "无关字段ABC" -> 不匹配

### Sampling Rate

- **Per task commit:** `pytest tests/test_feishu_field_mapping.py -x`
- **Per wave merge:** `pytest`
- **Phase gate:** Full suite green before `/gsd-verify-work`

## Sources

### Primary (HIGH confidence)
- [飞书 Bitable 字段类型枚举](https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-field/guide) -- type/ui_type 完整对照表
- [飞书 list_fields API](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/bitable-v1/app-table-field/list) -- 响应字段结构
- 项目源码一手分析: `feishu_client.py`, `feishu_settings.py`, `FeishuFieldMappingPage.tsx`, `manual_field_aliases.py`, `feishu.ts`

### Secondary (MEDIUM confidence)
- [飞书多维表格数据结构概述](https://open.feishu.cn/document/docs/bitable-v1/app-table-record/bitable-record-data-structure-overview) -- 字段读写格式差异

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - 零新依赖，所有组件已安装已验证
- Architecture: HIGH - 现有代码结构清晰，改动范围精确到文件和行号
- Pitfalls: HIGH - 基于源码一手分析发现 5 个具体问题，均有明确解决方案

**Research date:** 2026-04-16
**Valid until:** 2026-05-16 (30 days -- 稳定领域)
