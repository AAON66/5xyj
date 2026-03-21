# 社保表格聚合工具 - 架构设计文档

## 项目概述

系统目标是将来自广州、杭州、厦门、深圳、武汉、长沙等地区的社保 Excel 文件统一导入、识别、解析、标准化、校验、工号匹配，并最终同时导出两份固定模板结果。

核心业务链路：

多地区 Excel 上传 -> 有效 Sheet 识别 -> 表头识别与复合表头展开 -> 标准字段映射 -> 非明细行过滤 -> 标准化聚合 -> 数据校验 -> 工号匹配 -> 双模板导出 -> 看板统计

关键设计原则：

- 规则优先，DeepSeek 兜底
- 不依赖固定 sheet、固定行、固定列
- 所有标准化结果都必须可追溯到源文件和原始行
- 合计、小计、分组标题绝不能误判为人员明细
- 当前版本必须同时支持“薪酬模板”和“工具表最终版模板”两份导出

---

## 技术栈

| 层级 | 技术选型 |
|-----|---------|
| 前端 | React + TypeScript |
| 后端 | FastAPI (Python 3.11+) |
| 数据处理 | pandas + openpyxl |
| 数据库 | PostgreSQL |
| ORM / 迁移 | SQLAlchemy + Alembic |
| 文件上传 | python-multipart |
| LLM 兜底 | DeepSeek |
| 看板图表 | React 图表库 |
| 部署 | Docker Compose |

---

## 1. 系统架构图

```mermaid
graph TB
    subgraph Frontend["前端 (React)"]
        UploadUI[上传与批次管理]
        PreviewUI[解析预览]
        ValidationUI[校验结果]
        MatchingUI[工号匹配结果]
        ExportUI[双模板导出]
        DashboardUI[看板统计]
        MappingUI[字段映射修正]
    end

    subgraph Backend["后端 (FastAPI)"]
        API[REST API]
        BatchService[导入批次服务]
        WorkbookService[Workbook / Sheet 发现]
        HeaderService[表头识别与复合表头展开]
        MappingService[规则映射服务]
        LLMService[DeepSeek 兜底映射服务]
        FilterService[非明细行过滤]
        NormalizeService[标准化聚合服务]
        ValidationService[数据校验服务]
        MatchingService[工号匹配服务]
        ExportService[双模板导出服务]
        DashboardService[统计服务]
    end

    subgraph Data["数据层"]
        DB[(PostgreSQL)]
        Samples[data/samples]
        Templates[data/templates]
        Outputs[data/outputs]
    end

    subgraph External["外部能力"]
        DeepSeek[DeepSeek API]
        EmployeeSource[员工主数据源]
    end

    UploadUI --> API
    PreviewUI --> API
    ValidationUI --> API
    MatchingUI --> API
    ExportUI --> API
    DashboardUI --> API
    MappingUI --> API

    API --> BatchService
    API --> DashboardService
    BatchService --> WorkbookService
    WorkbookService --> HeaderService
    HeaderService --> MappingService
    MappingService --> LLMService
    MappingService --> FilterService
    FilterService --> NormalizeService
    NormalizeService --> ValidationService
    ValidationService --> MatchingService
    MatchingService --> ExportService

    BatchService --> DB
    HeaderService --> DB
    NormalizeService --> DB
    ValidationService --> DB
    MatchingService --> DB
    ExportService --> DB
    DashboardService --> DB

    BatchService --> Samples
    ExportService --> Templates
    ExportService --> Outputs
    LLMService --> DeepSeek
    MatchingService --> EmployeeSource
```

---

## 2. 核心业务流程图

> 关键特性：同一批次需要经过“解析、校验、匹配、导出”多个阶段，并且导出必须同时生成两份模板结果。

```mermaid
flowchart TD
    Start([开始]) --> Upload[上传多个地区 Excel 文件]
    Upload --> Batch[创建导入批次]
    Batch --> Discover[发现有效 Sheet 与候选数据区域]
    Discover --> Header[识别表头与复合表头]
    Header --> MapRule[规则映射标准字段]
    MapRule --> NeedLLM{规则是否能确定?}
    NeedLLM -->|是| FilterRows[过滤合计/小计/分组标题]
    NeedLLM -->|否| DeepSeekMap[调用 DeepSeek 做语义归一化]
    DeepSeekMap --> FilterRows
    FilterRows --> Normalize[写入标准化记录]
    Normalize --> Validate[执行数据校验]
    Validate --> Match[执行工号匹配]
    Match --> Ready{是否满足导出条件?}
    Ready -->|否| Fix[人工修正映射/匹配/数据]
    Fix --> Validate
    Ready -->|是| ExportA[导出薪酬模板]
    ExportA --> ExportB[导出工具表最终版模板]
    ExportB --> Dashboard[刷新看板统计]
    Dashboard --> End([结束])
```

### 批次状态流转

```mermaid
stateDiagram-v2
    [*] --> uploaded
    uploaded --> parsing
    parsing --> normalized
    normalized --> validated
    validated --> matched
    matched --> export_ready
    export_ready --> exported
    parsing --> failed
    normalized --> blocked
    validated --> blocked
    matched --> blocked
    blocked --> normalized: 修正后重跑
    exported --> [*]
```

---

## 3. 数据模型图

```mermaid
erDiagram
    import_batches ||--o{ source_files : contains
    import_batches ||--o{ normalized_records : aggregates
    import_batches ||--o{ validation_issues : produces
    import_batches ||--o{ match_results : produces
    import_batches ||--o{ export_jobs : triggers

    source_files ||--o{ header_mappings : owns
    source_files ||--o{ normalized_records : contributes

    employee_master ||--o{ match_results : matches
    export_jobs ||--o{ export_artifacts : generates

    import_batches {
        uuid id PK
        string batch_name
        string status "uploaded/parsing/normalized/validated/matched/export_ready/exported/failed/blocked"
        datetime created_at
        datetime updated_at
    }

    source_files {
        uuid id PK
        uuid batch_id FK
        string file_name
        string file_path
        string region
        string company_name
        string raw_sheet_name
        string file_hash
        datetime uploaded_at
    }

    header_mappings {
        uuid id PK
        uuid source_file_id FK
        string raw_header
        string raw_header_signature
        string canonical_field
        string mapping_source "rule/llm/manual"
        float confidence
        boolean manually_overridden
        datetime created_at
    }

    normalized_records {
        uuid id PK
        uuid batch_id FK
        uuid source_file_id FK
        int source_row_number
        string person_name
        string id_type
        string id_number
        string employee_id
        string social_security_number
        string billing_period
        string period_start
        string period_end
        decimal total_amount
        decimal company_total_amount
        decimal personal_total_amount
        decimal pension_company
        decimal pension_personal
        decimal medical_company
        decimal medical_personal
        decimal unemployment_company
        decimal unemployment_personal
        decimal injury_company
        json raw_payload
        datetime created_at
    }

    validation_issues {
        uuid id PK
        uuid batch_id FK
        uuid normalized_record_id FK
        string issue_type
        string severity
        string field_name
        text message
        boolean resolved
        datetime created_at
    }

    employee_master {
        uuid id PK
        string employee_id
        string person_name
        string id_number
        string company_name
        string department
        boolean active
        datetime created_at
    }

    match_results {
        uuid id PK
        uuid batch_id FK
        uuid normalized_record_id FK
        uuid employee_master_id FK
        string match_status "matched/unmatched/duplicate/low_confidence/manual"
        string match_basis
        float confidence
        datetime created_at
    }

    export_jobs {
        uuid id PK
        uuid batch_id FK
        string status
        datetime created_at
        datetime completed_at
    }

    export_artifacts {
        uuid id PK
        uuid export_job_id FK
        string template_type "salary/final_tool"
        string file_path
        string status
        text error_message
        datetime created_at
    }
```

### 关键状态字段说明

| 字段 | 可选值 | 说明 |
|-----|-------|------|
| import_batches.status | uploaded | 文件已上传 |
| | parsing | 正在识别 sheet、表头和数据区 |
| | normalized | 已生成标准化结果 |
| | validated | 已完成校验 |
| | matched | 已完成工号匹配 |
| | export_ready | 满足导出条件 |
| | exported | 双模板导出成功 |
| | blocked | 因缺模板、缺主数据、低置信度字段等阻塞 |
| | failed | 流程失败 |
| match_results.match_status | matched | 精确或可接受匹配 |
| | unmatched | 无匹配结果 |
| | duplicate | 匹配到多个员工 |
| | low_confidence | 匹配置信度不足 |
| | manual | 人工修正后确认 |
| export_artifacts.template_type | salary | 薪酬模板 |
| | final_tool | 工具表最终版模板 |

---

## 4. 页面结构图

```mermaid
graph TB
    subgraph Main["主要页面"]
        Dashboard[看板首页 /]
        Imports[导入批次列表 /imports]
        ImportDetail[导入批次详情 /imports/:id]
        Validation[校验结果 /imports/:id/validation]
        Matching[匹配结果 /imports/:id/matching]
        Exports[导出结果 /imports/:id/exports]
        Mappings[字段映射 /mappings]
        Employees[员工主数据 /employees]
    end

    subgraph ImportDetailSections["批次详情功能"]
        RawFiles[原始文件列表]
        HeaderPreview[表头识别预览]
        NormalizePreview[标准化结果预览]
        IssueSummary[问题汇总]
        MatchSummary[匹配汇总]
        ExportSummary[导出汇总]
    end

    Dashboard --> Imports
    Imports --> ImportDetail
    ImportDetail --> Validation
    ImportDetail --> Matching
    ImportDetail --> Exports
    Dashboard --> Mappings
    Dashboard --> Employees

    ImportDetail --> RawFiles
    ImportDetail --> HeaderPreview
    ImportDetail --> NormalizePreview
    ImportDetail --> IssueSummary
    ImportDetail --> MatchSummary
    ImportDetail --> ExportSummary
```

---

## 5. API 设计

### 导入与解析 API

| 方法 | 路径 | 描述 |
|-----|------|-----|
| POST | /api/v1/imports | 创建导入批次并上传文件 |
| GET | /api/v1/imports | 获取导入批次列表 |
| GET | /api/v1/imports/{id} | 获取导入批次详情 |
| POST | /api/v1/imports/{id}/parse | 触发解析和标准化 |
| GET | /api/v1/imports/{id}/preview | 查看解析预览 |

### 校验与匹配 API

| 方法 | 路径 | 描述 |
|-----|------|-----|
| POST | /api/v1/imports/{id}/validate | 执行数据校验 |
| GET | /api/v1/imports/{id}/validation-issues | 获取校验问题列表 |
| POST | /api/v1/imports/{id}/match | 执行工号匹配 |
| GET | /api/v1/imports/{id}/match-results | 获取匹配结果 |
| PATCH | /api/v1/match-results/{id} | 人工修正匹配结果 |

### 导出 API

| 方法 | 路径 | 描述 |
|-----|------|-----|
| POST | /api/v1/imports/{id}/export | 同时触发两份模板导出 |
| GET | /api/v1/imports/{id}/exports | 获取导出任务状态 |
| GET | /api/v1/exports/{id}/files | 获取导出产物列表 |
| GET | /api/v1/export-files/{id}/download | 下载导出文件 |

### 配置与看板 API

| 方法 | 路径 | 描述 |
|-----|------|-----|
| GET | /api/v1/dashboard/overview | 获取看板概览数据 |
| GET | /api/v1/dashboard/regions | 获取按地区汇总数据 |
| GET | /api/v1/mappings | 获取字段映射记录 |
| PATCH | /api/v1/mappings/{id} | 人工修正字段映射 |
| POST | /api/v1/employees/import | 导入员工主数据 |
| GET | /api/v1/employees | 获取员工主数据列表 |

---

## 6. 外部 API 集成

### 6.1 DeepSeek（表头语义归一化兜底）

```python
# endpoint: https://api.deepseek.com/v1/chat/completions
# auth: Bearer Token
# model: deepseek-chat 或 deepseek-reasoner
```

#### 典型调用场景

1. 原始表头无法通过规则映射到标准字段
2. 同一个表头可能表示“单位金额”或“总金额”，需要结合上下文判断
3. 透视表或复合表头结构不标准，需要语义辅助拆解

#### 调用约束

- 规则优先，只有低置信度字段才走 DeepSeek
- DeepSeek 只返回字段归类建议、候选字段和置信度
- DeepSeek 不能直接参与金额汇总、工号匹配和导出写值

#### 字段归一化请求示例

```python
import httpx

async def map_headers_with_deepseek(raw_headers: list[str], context: dict, api_key: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "你是社保表格字段归一化助手。"
                            "你只能把原始表头映射为给定标准字段集合中的候选项，"
                            "并返回置信度与理由。"
                        )
                    },
                    {
                        "role": "user",
                        "content": f"原始表头: {raw_headers}\\n上下文: {context}"
                    }
                ],
                "temperature": 0.1
            }
        )
        return response.json()
```

---

## 7. 标准字段体系

系统内部建议统一维护以下标准字段：

| 标准字段 | 含义 |
|-----|-----|
| person_name | 姓名 |
| id_type | 证件类型 |
| id_number | 证件号码 |
| employee_id | 工号 |
| social_security_number | 个人社保号 |
| company_name | 公司名称 |
| region | 地区 |
| billing_period | 所属期 |
| period_start | 所属期起 |
| period_end | 所属期止 |
| payment_salary | 缴费工资 |
| payment_base | 缴费基数 |
| total_amount | 总金额 |
| company_total_amount | 单位总金额 |
| personal_total_amount | 个人总金额 |
| pension_company | 养老单位金额 |
| pension_personal | 养老个人金额 |
| medical_company | 医疗单位金额 |
| medical_personal | 医疗个人金额 |
| unemployment_company | 失业单位金额 |
| unemployment_personal | 失业个人金额 |
| injury_company | 工伤单位金额 |
| supplementary_medical_company | 补充医疗单位金额 |
| supplementary_pension_company | 补充养老单位金额 |
| large_medical_personal | 大额医疗个人金额 |
| late_fee | 滞纳金 |
| interest | 利息 |

---

## 8. Header 同义词策略

以下同义关系应优先由规则处理：

### 身份类字段

- `姓名` -> `person_name`
- `证件号码` -> `id_number`
- `证件类型` -> `id_type`
- `个人社保号` -> `social_security_number`

### 时间类字段

- `费款所属期`
- `费款所属期起`
- `费款所属期止`
- `建账年月`

### 汇总金额类字段

- `应缴金额合计`
- `总金额`
- `应收金额`
- `合计`
- `总计`

### 单位 / 个人总额字段

- `单位部分合计`
- `单位缴费总金额`
- `单位社保合计`

- `个人部分合计`
- `个人缴费总金额`
- `个人社保合计`

### 典型险种字段

- 养老：`基本养老保险(单位缴纳)`、`基本养老保险（单位）`、`职工基本养老保险(单位缴纳)`、`基本养老应缴费额`
- 医疗：`基本医疗保险（含生育）(单位缴纳)`、`职工基本医疗保险费`、`基本医疗应缴费额`
- 失业：`失业保险(单位缴纳)`、`失业保险费`、`失业应缴费额`
- 工伤：`工伤保险`、`工伤保险费`、`工伤应缴费额`

---

## 9. Python 项目结构

```text
social-security-aggregator/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── parsers/
│   │   ├── mappings/
│   │   ├── validators/
│   │   ├── matchers/
│   │   └── exporters/
│   ├── tests/
│   ├── alembic/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── utils/
│   ├── package.json
│   └── vite.config.ts
├── data/
│   ├── samples/
│   ├── templates/
│   └── outputs/
└── docker-compose.yml
```

### Python 依赖建议

```txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
python-multipart==0.0.12
sqlalchemy==2.0.36
alembic==1.14.0
psycopg2-binary==2.9.10
asyncpg==0.30.0
pydantic==2.10.3
pydantic-settings==2.6.1
httpx==0.28.1
pandas==2.2.3
openpyxl==3.1.5
python-dotenv==1.0.1
loguru==0.7.3
```

---

## 10. 环境变量

```env
# 数据库
DATABASE_URL=postgresql://user:password@localhost:5432/social_security_aggregator
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# 应用
APP_NAME=社保表格聚合工具
APP_VERSION=1.0.0
API_V1_PREFIX=/api/v1
BACKEND_CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# 目录
UPLOAD_DIR=./data/uploads
SAMPLES_DIR=./data/samples
TEMPLATES_DIR=./data/templates
OUTPUTS_DIR=./data/outputs

# DeepSeek
DEEPSEEK_API_KEY=
DEEPSEEK_API_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
ENABLE_LLM_FALLBACK=true

# 日志
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

## 11. 核心功能特性

### 11.1 多地区 Excel 解析

- 支持广州、杭州、厦门、深圳、武汉、长沙等地区格式
- 支持复合表头、透视表样式、非固定 sheet、非固定表头起始行
- 支持保留源文件和原始行号

### 11.2 标准字段归一化

- 通过规则库优先映射字段
- 通过地区规则处理差异
- 对低置信度字段使用 DeepSeek 做兜底建议

### 11.3 非明细行过滤

- 过滤 `合计`
- 过滤 `小计`
- 过滤 `在职人员`
- 过滤 `退休人员`
- 过滤 `家属统筹人员`

### 11.4 数据校验

- 必填字段校验
- 身份证号格式校验
- 金额合法性校验
- 同人同期开票重复校验
- 汇总逻辑校验

### 11.5 工号匹配

- 身份证号优先匹配
- 姓名 + 公司辅助匹配
- 支持人工纠正
- 记录匹配依据和置信度

### 11.6 双模板导出

- 同时导出“薪酬模板”和“工具表最终版模板”
- 保留模板结构和关键样式
- 任一模板导出失败都视为任务未完成

### 11.7 看板统计

- 批次总览
- 地区分布
- 未识别字段统计
- 校验问题统计
- 工号匹配统计
- 双模板导出统计

---

## 12. 数据统计指标

### 批次维度

- 导入批次数
- 文件总数
- 标准化记录总数
- 地区覆盖数

### 解析维度

- 有效 sheet 识别成功率
- 表头识别成功率
- 未识别字段数
- 低置信度字段数

### 校验维度

- 缺失字段数
- 异常金额数
- 重复记录数
- 结构错误数

### 匹配维度

- 工号匹配成功率
- 未匹配数量
- 重复匹配数量
- 人工修正数量

### 导出维度

- 薪酬模板导出成功率
- 工具表最终版模板导出成功率
- 双模板同时成功率

---

## 13. 未来扩展方向

1. **地区规则可视化配置**
   - 后台直接维护字段别名和解析规则
   - 发布新规则无需改代码

2. **人工校正闭环**
   - 将人工修正映射沉淀为长期规则
   - 将人工修正匹配沉淀为长期员工映射

3. **批量月度处理**
   - 支持按月份批量运行
   - 支持历史批次对比

4. **公积金扩展**
   - 在现有社保聚合能力上扩展公积金字段和模板

5. **更强的智能识别**
   - DeepSeek 辅助解析复杂透视表
   - 字段解释、异常原因自动总结

---

## 14. 任务对齐矩阵

以下矩阵用于把 `task.json` 的任务编号和本架构文档中的模块直接对齐，后续开发默认按这个映射推进。

### A. 基础设施层

| 任务ID | 任务标题 | 对应架构模块 / 章节 |
|-----|-----|-----|
| 1 | 项目基础配置 | 技术栈、项目结构、环境变量 |
| 2 | 数据库 Schema 设计 | 数据模型图 |
| 3 | 配置管理与基础依赖注入 | 后端核心配置、环境变量 |
| 4 | FastAPI 应用初始化 | 系统架构图、API 设计 |
| 5 | React 前端初始化 | 页面结构图 |
| 6 | 员工主数据与工号主档导入 | 数据模型图、工号匹配服务 |

### B. 核心解析与数据处理链路

| 任务ID | 任务标题 | 对应架构模块 / 章节 |
|-----|-----|-----|
| 7 | 文件上传与导入批次管理 | 核心业务流程图、import_batches/source_files |
| 8 | Workbook / Sheet 发现服务 | 系统架构图中的 WorkbookService |
| 9 | 表头识别与复合表头展开服务 | 系统架构图中的 HeaderService |
| 10 | 规则映射服务与别名规则库 | Header 同义词策略、MappingService |
| 11 | DeepSeek 兜底映射服务 | 外部 API 集成、LLMService |
| 12 | 非明细行过滤服务 | 核心功能特性 11.3、FilterService |
| 13 | 标准化聚合服务 | 标准字段体系、NormalizeService |
| 14 | 数据校验服务 | 核心功能特性 11.4、ValidationService |
| 15 | 工号匹配服务 | 核心功能特性 11.5、MatchingService |
| 16 | 双模板导出服务 | 核心功能特性 11.6、ExportService |

### C. 后端 API 层

| 任务ID | 任务标题 | 对应架构模块 / 章节 |
|-----|-----|-----|
| 17 | 导入与解析 API | API 设计中的导入与解析 API |
| 18 | 校验与匹配 API | API 设计中的校验与匹配 API |
| 19 | 导出 API | API 设计中的导出 API |
| 20 | 看板统计 API | API 设计中的配置与看板 API |

### D. 前端页面层

| 任务ID | 任务标题 | 对应架构模块 / 章节 |
|-----|-----|-----|
| 21 | 上传与解析预览页面 | 页面结构图中的 Imports / ImportDetail |
| 22 | 校验与匹配结果页面 | 页面结构图中的 Validation / Matching |
| 23 | 双模板导出页面 | 页面结构图中的 Exports |
| 24 | 看板首页 UI | 页面结构图中的 Dashboard |
| 25 | 导入批次详情页面 | 页面结构图中的 ImportDetail |
| 26 | 字段映射配置与人工修正页面 | 页面结构图中的 Mappings |
| 27 | 错误处理与加载状态 | 所有前端页面的横切能力 |
| 28 | 响应式适配 | 所有前端页面的横切能力 |

### E. 测试与交付层

| 任务ID | 任务标题 | 对应架构模块 / 章节 |
|-----|-----|-----|
| 29 | 地区样例解析自动化测试 | 广州/杭州/厦门/深圳/武汉/长沙输入样例 |
| 30 | 双模板导出自动化测试 | 双模板导出服务、导出 API |
| 31 | DeepSeek 集成测试与降级验证 | 外部 API 集成、规则优先策略 |
| 32 | 最终联调与部署文档 | 全链路验收、部署与环境变量 |

### 推荐开发顺序

1. 先完成 1-5，建立基础设施
2. 再完成 6-16，打通核心数据链路
3. 然后完成 17-20，暴露可调用 API
4. 再完成 21-28，补齐前端操作和看板
5. 最后完成 29-32，做自动化验证和最终交付
