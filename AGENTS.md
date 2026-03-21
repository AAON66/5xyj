# Social Security Spreadsheet Aggregation Tool - Project Instructions

## Project Context

这是一个基于 `React + FastAPI` 的社保表格聚合工具。

目标不是只做“上传 Excel”，而是构建一条完整的数据处理链路：

1. 聚合不同地区、不同公司、不同格式的社保表格
2. 自动识别表头与内容，统一映射到标准字段
3. 建立看板系统，展示导入、识别、校验、匹配、导出状态
4. 建立数据校验系统，标记缺失、异常、重复、结构错误
5. 基于员工主数据进行工号匹配
6. 同时导出两份固定模板结果

技术方向：

- Frontend: React
- Backend: FastAPI
- Data processing: Python ecosystem, preferred `pandas`, `openpyxl`, `python-multipart`
- LLM fallback: DeepSeek（API Key 由用户后续提供）

---

## Confirmed Output Templates

当前已确认必须同时输出以下两份模板，任意一份未成功导出，都不能视为任务完成：

1. `2026年02月社保公积金.x lsx_模板 （薪酬）.xlsx`
   - 路径：`C:\Users\AAON\Desktop\202602社保公积金台账\202602社保公积金汇总\2026年02月社保公积金.x lsx_模板 （薪酬）.xlsx`
2. `2026年02月社保公积金工具表.x lsx_模板 （最终版）.xlsx`
   - 路径：`C:\Users\AAON\Desktop\202602社保公积金台账\202602社保公积金汇总\2026年02月社保公积金工具表.x lsx_模板 （最终版）.xlsx`

规则：

- 当前版本必须支持双模板输出
- 导出服务必须清晰区分两种导出目标
- 后续新增模板时，必须在不破坏现有双模板能力的前提下扩展

---

## Confirmed Input Samples

当前已确认的地区样例文件如下，后续开发和测试必须尽量覆盖这些结构：

### Guangzhou

- `2026年2月社会保险费申报个人明细表--广分.xlsx`
- `2026年2月社会保险费申报个人明细表--视播.xlsx`

特征：

- 首行是报表标题
- 第 3 到 6 行是单位信息和所属期
- 第 7、8 行是两层表头
- 存在 `单位部分合计`、`个人部分合计`、`应缴金额合计`
- 典型字段包含：
  - `姓名`
  - `证件号码`
  - `个人社保号`
  - `费款所属期起`
  - `费款所属期止`
  - `基本养老保险(单位缴纳)`
  - `基本养老保险(个人缴纳)`
  - `失业保险(单位缴纳)`
  - `基本医疗保险（含生育）(单位缴纳)`
  - `工伤保险`

### Hangzhou

- `杭州聚变202602社保账单.xlsx`
- `杭州裂变202602社保账单.xlsx`

特征：

- 结构为 `单位社保费职工全险种申报明细`
- 第 3、4 行构成复合表头
- 一个险种下可能拆成 `单位部分`、`个人部分`
- 典型字段包含：
  - `基本养老应缴费额`
  - `机关养老应缴费额`
  - `失业应缴费额`
  - `工伤应缴费额`
  - `基本医疗应缴费额`
  - `公务员补助应缴费额`
  - `合计`

### Xiamen

- `厦门202602社保账单.xlsx`
- `厦门202602社保账单（补缴1月入职2人）.xlsx`

特征：

- 工作表名为 `职工社保对账单明细查询`
- 表头包含总金额、单位总额、个人总额
- 每个险种下还有二级字段，如：
  - `缴费工资`
  - `缴费基数`
  - `单位应缴`
  - `减免金额`
  - `个人应缴`
  - `本金合计`
  - `滞纳金`
  - `利息`
- 存在补缴场景，费款所属期可能不是当月
- 存在 `合计` 行，不能误当成人员明细

### Shenzhen

- `深圳创造欢乐202602社保明细.xlsx`
- `深圳零一金智202602社保明细.xlsx`
- `深圳零一裂变202602社保明细.xlsx`
- `深圳零一数科202602社保明细.xlsx`
- `深圳零一运营202602社保明细.xlsx`
- `深圳青春洋溢202602社保明细.xlsx`
- `深圳无限增长202602社保明细.xlsx`
- `刘艳玲202602社保缴费明细.xlsx`

特征：

- 工作表通常为 `申报明细`
- 第 1、2 行是两层表头
- 结构以 `应收金额 / 个人社保合计 / 单位社保合计` 开头
- 常见险种字段：
  - `基本养老保险（单位）`
  - `基本养老保险（个人）`
  - `基本医疗保险（单位）`
  - `地方补充医疗（单位）`
  - `基本医疗保险（个人）`
  - `生育保险`
  - `工伤保险（单位）`
  - `失业保险（单位）`
  - `失业保险（个人）`
  - `地方补充养老（单位）`
- 存在分组行或非明细行：
  - `在职人员`
  - `退休人员`
  - `家属统筹人员`
  - `小计`
- 某些文件存在只有部分险种金额的特殊行，不能按固定列数粗暴解析

### Wuhan

- `武汉202602社保台账.xlsx`

特征：

- 第一行是 `职工明细 / 单位缴纳 / 个人缴纳`
- 第二行开始为复合表头
- 单位和个人区块重复出现相同险种名
- 典型字段包含：
  - `养老保险应缴费额`
  - `失业保险应缴费额`
  - `企业职工基本医疗应缴费额`
  - `工伤保险应缴费额`
- 存在 `合计` 行

### Changsha

- `长沙202602社保账单.xlsx`

特征：

- 首个有效工作表不是常规 `Sheet1`，当前样例出现在 `Sheet4`
- 数据起始行不是第 1 行
- 表头结构接近透视结果，而不是标准明细表
- 当前可识别字段包含：
  - `姓名`
  - `工伤保险`
  - `失业保险(单位缴纳)`
  - `失业保险(个人缴纳)`
  - `职工大额医疗互助保险(个人缴纳)`
  - `职工基本养老保险(单位缴纳)`
  - `职工基本养老保险(个人缴纳)`
  - `职工基本医疗保险(单位缴纳)`
  - `职工基本医疗保险(个人缴纳)`
  - `总计`
- 不能假设“第一个 sheet + 第一行表头”就是有效数据

---

## Core Parsing Reality

本项目必须接受以下事实：

1. 不同地区表头名称不同，但表达的业务含义可能相同
2. 同一地区不同公司文件结构也可能略有差异
3. 有些文件是两层表头，有些是透视表样式，有些包含前置说明信息
4. 有些文件会混入 `合计`、`小计`、`在职人员` 这类非人员明细行
5. 有些文件按险种展开为多列，有些直接给总额
6. 不能依赖固定 sheet 名、固定起始行、固定列序

因此解析策略必须是：

- 先定位有效工作表
- 再定位表头区域
- 再识别数据开始行
- 再做标准字段映射
- 再过滤非明细行
- 再校验和工号匹配
- 最后同时导出两份模板

---

## Standard Canonical Fields

系统内部必须维护统一字段，不允许各地区直接把原始列名散落到业务层。

建议至少统一以下标准字段：

- `person_name`
- `id_type`
- `id_number`
- `employee_id`
- `social_security_number`
- `company_name`
- `region`
- `billing_period`
- `period_start`
- `period_end`
- `payment_base`
- `payment_salary`
- `total_amount`
- `company_total_amount`
- `personal_total_amount`
- `pension_company`
- `pension_personal`
- `medical_company`
- `medical_personal`
- `medical_maternity_company`
- `maternity_amount`
- `unemployment_company`
- `unemployment_personal`
- `injury_company`
- `supplementary_medical_company`
- `supplementary_pension_company`
- `large_medical_personal`
- `late_fee`
- `interest`
- `raw_sheet_name`
- `raw_header_signature`
- `source_file_name`
- `source_row_number`

要求：

- 原始值必须保留，不能只保留标准化后的值
- 标准字段映射必须可追溯到源文件列名
- 对无法确认的字段，不允许静默丢弃，必须标记为未识别

---

## Header Synonym Rules

以下是当前样例已经确认的同义表达，后续应优先做规则映射：

### Person Identity

- `姓名` -> `person_name`
- `证件号码` -> `id_number`
- `证件类型` -> `id_type`
- `个人社保号` -> `social_security_number`

### Period

- `费款所属期`
- `费款所属期起`
- `费款所属期止`
- `建账年月`

以上字段应统一归并到 `billing_period / period_start / period_end`

### Totals

- `应缴金额合计`
- `总金额`
- `应收金额`
- `合计`
- `总计`

这些字段不一定完全等价，但都属于“金额汇总类字段”，需要进一步结合上下文判断映射。

### Company / Personal Totals

- `单位部分合计`
- `单位缴费总金额`
- `单位社保合计`

映射到 `company_total_amount`

- `个人部分合计`
- `个人缴费总金额`
- `个人社保合计`

映射到 `personal_total_amount`

### Pension

- `基本养老保险(单位缴纳)`
- `基本养老保险（单位）`
- `职工基本养老保险(单位缴纳)`
- `基本养老应缴费额` + `单位部分`

映射到 `pension_company`

- `基本养老保险(个人缴纳)`
- `基本养老保险（个人）`
- `职工基本养老保险(个人缴纳)`
- `基本养老应缴费额` + `个人部分`

映射到 `pension_personal`

### Unemployment

- `失业保险(单位缴纳)`
- `失业保险（单位）`
- `失业保险费` + `单位应缴`
- `失业应缴费额` + `单位部分`

映射到 `unemployment_company`

- `失业保险(个人缴纳)`
- `失业保险（个人）`
- `失业保险费` + `个人应缴`
- `失业应缴费额` + `个人部分`

映射到 `unemployment_personal`

### Medical

- `基本医疗保险（含生育）(单位缴纳)`
- `基本医疗保险（单位）`
- `职工基本医疗保险费` + `单位应缴`
- `职工基本医疗保险(单位缴纳)`
- `基本医疗应缴费额` + `单位部分`

映射到 `medical_company` 或 `medical_maternity_company`

- `基本医疗保险（含生育）(个人缴纳)`
- `基本医疗保险（个人）`
- `职工基本医疗保险费` + `个人应缴`
- `职工基本医疗保险(个人缴纳)`
- `基本医疗应缴费额` + `个人部分`

映射到 `medical_personal`

### Injury

- `工伤保险`
- `工伤保险（单位）`
- `工伤保险费` + `单位应缴`
- `工伤应缴费额`

映射到 `injury_company`

### Supplementary Items

- `地方补充医疗（单位）` -> `supplementary_medical_company`
- `地方补充养老（单位）` -> `supplementary_pension_company`
- `职工大额医疗互助保险(个人缴纳)` -> `large_medical_personal`

注意：

- 规则映射优先于 LLM
- 只有规则无法确定或置信度不足时，才允许调用 DeepSeek 做语义归一化

---

## DeepSeek Integration Strategy

允许接入 DeepSeek，但必须遵循 `rules first, LLM fallback` 原则。

DeepSeek 适用场景：

1. 识别非标准抬头的语义归属
2. 对低置信度字段做候选映射排序
3. 对异常结构文件给出解析建议
4. 辅助判断某列是“单位金额”“个人金额”还是“总金额”

DeepSeek 不应直接替代：

- 数值计算
- 金额汇总
- 工号精确匹配
- 导出模板填充

接入要求：

- API Key 未提供前，只能先实现接口封装和降级逻辑
- 没有 API Key 时，系统必须仍可运行基础规则链路
- 每次 LLM 参与映射时，必须保留：
  - 原始表头文本
  - 候选标准字段
  - 最终选择结果
  - 置信度
  - 是否由人工规则覆盖

推荐后端模块：

- `backend/app/services/header_normalizer.py`
- `backend/app/services/llm_mapping_service.py`
- `backend/app/mappings/manual_field_aliases.py`

---

## MANDATORY: Agent Workflow

Every new agent session MUST follow this workflow:

### Step 1: Understand the Current Project State

- 阅读 `AGENTS.md`、`architecture.md`、`task.json`
- 确认当前任务属于以下主线之一：
  - 文件导入
  - 表头识别
  - 字段标准化
  - 非明细行过滤
  - 工号匹配
  - 数据校验
  - 双模板导出
  - 看板展示

### Step 2: Select Next Task

Read `task.json` and select ONE task to work on.

Priority:

1. `passes: false`
2. 优先主链路：导入 -> 识别 -> 标准化 -> 过滤 -> 匹配 -> 校验 -> 双模板导出
3. 看板排在核心数据链路之后

### Step 3: Implement the Task

- 先实现规则解析，再考虑 LLM 兜底
- 不要把地区差异硬编码到前端
- 不要依赖固定 sheet 名、固定起始行、固定列号
- 任何地区特殊逻辑，都应收敛到解析器、映射器或配置层

### Step 4: Test Thoroughly

**Testing Requirements - MANDATORY:**

1. 涉及导入、识别、映射的修改
   - 必须至少使用 2 个不同地区样例验证
   - 优先覆盖“复合表头”和“非标准表头”场景

2. 涉及特殊行过滤的修改
   - 必须验证以下内容不会进入最终人员明细：
     - `合计`
     - `小计`
     - `在职人员`
     - `退休人员`
     - `家属统筹人员`

3. 涉及工号匹配的修改
   - 必须验证：
     - 可匹配
     - 无法匹配
     - 重复匹配

4. 涉及导出的修改
   - 必须同时验证两份输出模板
   - 不能只验证其中一份

5. 涉及 DeepSeek 的修改
   - 必须验证无 API Key 时的降级逻辑
   - 必须验证规则优先、LLM 兜底的触发条件

测试清单：

- [ ] 广州样例可解析
- [ ] 杭州样例可解析
- [ ] 厦门样例可解析
- [ ] 深圳样例可解析
- [ ] 武汉样例可解析
- [ ] 长沙样例可识别有效表头
- [ ] 非明细行已过滤
- [ ] 标准字段映射正确
- [ ] 工号匹配结果正确
- [ ] 已成功导出“薪酬模板”
- [ ] 已成功导出“工具表最终版模板”
- [ ] lint 通过
- [ ] build 成功

### Step 5: Update Progress

Write your work to `progress.txt`:

```text
## [Date] - Task: [task description]

### What was done:
- [specific changes made]

### Testing:
- [how it was tested]

### Risks / Open Questions:
- [missing employee master / unresolved field alias / DeepSeek key not provided yet]

### Notes:
- [any relevant notes for future agents]
```

### Step 6: Commit Changes

Only when all validations pass:

```bash
git add .
git commit -m "[task description] - completed"
```

Rules:

- 不要删除任务
- 不要假装完成
- 只有在完整验证通过后，才能把 `passes` 改成 `true`

---

## Blocking Issues

以下情况必须视为阻塞：

1. 任意一个输出模板不可访问
2. 缺少员工主数据，无法做工号匹配
3. 某地区样例缺失，导致无法验证对应解析规则
4. DeepSeek API Key 尚未提供，但任务又强依赖 LLM 结果
5. 无法确认某字段是单位金额、个人金额还是总金额

Blocked 时：

- 不要提交伪完成代码
- 不要绕过双模板要求
- 不要把低置信度字段静默映射到错误目标
- 必须在 `progress.txt` 中明确记录缺失材料和风险

---

## Project Structure

推荐结构：

```text
/
├── AGENTS.md
├── task.json
├── progress.txt
├── architecture.md
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── parsers/
│   │   ├── mappings/
│   │   ├── validators/
│   │   ├── matchers/
│   │   ├── exporters/
│   │   └── models/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── utils/
├── data/
│   ├── samples/
│   ├── templates/
│   └── outputs/
└── tests/
```

职责分工：

- React 负责上传、看板、识别结果展示、异常提示、导出入口
- FastAPI 负责文件接收、解析、字段归一化、工号匹配、校验、导出编排、DeepSeek 调用封装

---

## Commands

```bash
# backend
uvicorn backend.app.main:app --reload
pytest

# frontend
npm run lint
npm run build
npm run dev
```

---

## Key Rules

1. **Data pipeline first** - 先保证主链路可用，再做看板增强
2. **Rules before LLM** - 规则优先，DeepSeek 只做兜底
3. **No fixed-position parsing** - 不要假设固定 sheet、固定行、固定列
4. **Keep provenance** - 每条标准化结果都必须可追溯到原始文件和原始行
5. **Ignore non-detail rows** - `合计/小计/分组标题` 绝不能当成人员明细
6. **Match by employee ID carefully** - 工号匹配必须可解释、可回溯
7. **Export both templates** - 当前必须同时满足两份模板输出
