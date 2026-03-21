# 社保表格聚合工具

这是一个基于 React + FastAPI 的社保表格聚合项目，目标是把多地区、多格式的社保 Excel 统一导入、识别、标准化、校验、匹配并同时导出两份固定模板结果。

## 当前状态

当前仓库已经完成以下主链路：
- 多文件上传与导入批次管理
- Workbook / Sheet 发现与复合表头识别
- 规则优先、LLM 兜底的标准字段映射
- 非明细行过滤、标准化聚合、数据校验、工号匹配
- 双模板导出
- Dashboard、导入预览、结果页、导出页、映射修正页
- 地区样例解析回归、双模板导出回归、DeepSeek 降级测试

当前仍未完成的核心任务：
- 任务 6“员工主数据与工号主档导入”仍处于未完成状态
- 前端 `/employees` 仍是占位页，员工主档导入 API 还没有正式落地

这意味着：
- 匹配服务本身已经可用
- 但生产使用前仍需要补齐员工主档导入能力，或由外部方式先写入员工主数据表

## 技术栈

- Frontend: React 18 + TypeScript + Vite
- Backend: FastAPI + SQLAlchemy + Alembic
- Data processing: openpyxl, pandas
- HTTP client: httpx
- LLM fallback: DeepSeek
- Database: 通过 `DATABASE_URL` 配置，当前测试主要使用 SQLite，默认示例为 PostgreSQL

## 目录结构

```text
.
├── architecture.md
├── task.json
├── progress.txt
├── README.md
├── DEPLOYMENT.md
├── backend/
├── frontend/
├── data/
└── tests/
```

## 环境准备

1. Python 3.11+
2. Node.js 18+
3. 可用数据库
4. 两份输出模板文件
5. 可选：DeepSeek API Key

把根目录 `.env.example` 复制为 `.env` 后按需填写。

关键环境变量：
- `DATABASE_URL`
- `UPLOAD_DIR`
- `SAMPLES_DIR`
- `TEMPLATES_DIR`
- `OUTPUTS_DIR`
- `SALARY_TEMPLATE_PATH`
- `FINAL_TOOL_TEMPLATE_PATH`
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_API_BASE_URL`
- `DEEPSEEK_MODEL`
- `VITE_API_BASE_URL`

## 本地启动

### 后端

```powershell
py -m pip install -r backend\requirements.txt
py backend\run.py
```

默认监听：`http://127.0.0.1:8000`

### 前端

```powershell
cd frontend
cmd /c npm.cmd install
cmd /c npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

默认访问：`http://127.0.0.1:5173`

## 当前主要页面

- `/` 看板首页
- `/imports` 导入与解析预览
- `/imports/:batchId` 批次详情
- `/results` 校验与匹配结果
- `/exports` 双模板导出
- `/mappings` 字段映射修正
- `/employees` 员工主档占位页

## 当前主要 API

- `GET /api/v1/system/health`
- `GET /api/v1/dashboard/overview`
- `POST /api/v1/imports`
- `GET /api/v1/imports`
- `GET /api/v1/imports/{batch_id}`
- `POST /api/v1/imports/{batch_id}/parse`
- `GET /api/v1/imports/{batch_id}/preview`
- `POST /api/v1/imports/{batch_id}/validate`
- `GET /api/v1/imports/{batch_id}/validation`
- `POST /api/v1/imports/{batch_id}/match`
- `GET /api/v1/imports/{batch_id}/match`
- `POST /api/v1/imports/{batch_id}/export`
- `GET /api/v1/imports/{batch_id}/export`
- `GET /api/v1/mappings`
- `PATCH /api/v1/mappings/{mapping_id}`

## 推荐联调顺序

1. 确认 `/api/v1/system/health` 正常
2. 上传真实地区样例创建批次
3. 执行 `parse`，检查表头映射、过滤行和标准化预览
4. 执行 `validate`
5. 在员工主数据存在的前提下执行 `match`
6. 触发双模板 `export`
7. 回到 Dashboard 检查看板统计

## 测试命令

### 后端

```powershell
py -m compileall backend
.\.venv\Scripts\python.exe -m pytest backend\tests -p no:cacheprovider
```

### 前端

```powershell
cd frontend
cmd /c npm.cmd run lint
cmd /c npm.cmd run build
```

## 已知限制

- 员工主档导入流程尚未正式实现，任务 6 仍未完成
- DeepSeek 测试当前以 mock 为主，没有在自动化里跑真实网络调用
- 双模板导出回归依赖本地真实模板文件，缺模板时测试会跳过
- 地区样例回归依赖 `data/samples` 下的真实文件，缺样例时测试会跳过

## 进一步说明

更完整的部署、联调、验证和风险说明见 [DEPLOYMENT.md](./DEPLOYMENT.md)。
