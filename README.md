# Social Security And Housing Fund Management System

这是一个基于 React + FastAPI 的社保、公积金数据处理平台。系统面向管理员、HR 和员工三类角色，支持从多地区 Excel 台账中提取明细、做标准化归一、过滤异常/非明细行、执行校验与员工匹配，并同时导出两份固定模板结果。

当前仓库已经不只是“上传 Excel 的小工具”，而是一套包含导入、校验、匹配、导出、查询、权限和审计能力的业务系统。

## Current Product Scope

系统目前覆盖以下能力：

- 多地区社保和公积金 Excel 导入
- 有效 sheet 发现与复合表头识别
- 规则优先的标准字段映射，DeepSeek 作为兜底
- `合计`、`小计`、分组标题等非明细行过滤
- 数据校验、重复检测、金额一致性检查
- 员工主数据导入与工号匹配
- 双模板导出
- 批次预览、字段映射查看、结果查询与数据管理
- 管理员/HR 后台工作台
- 员工自助查询入口
- JWT 登录、角色鉴权、API Key、审计日志

## Roles And Entry Points

系统内有三类角色：

- `admin`
  负责系统管理、用户管理、API Key、审计日志，并拥有全部 HR 业务能力。
- `hr`
  负责导入、校验、匹配、导出、查询、员工主数据等业务操作。
- `employee`
  通过工号、身份证号、姓名完成身份校验后进入员工自助查询。

默认路由入口：

- 管理员工作台：`/workspace/admin`
- HR 工作台：`/workspace/hr`
- 员工查询：`/employee/query`

## Main Workflow

核心业务链路如下：

1. 上传多个地区的社保/公积金工作簿
2. 识别有效工作表与表头区域
3. 将原始字段映射到标准字段
4. 过滤合计、小计、分组行等非人员明细
5. 执行校验并识别重复/异常
6. 基于员工主数据进行工号匹配
7. 同时导出两份固定模板
8. 在看板、明细查询和员工门户中查看结果

支持的主要样例地区包括广州、杭州、厦门、深圳、武汉、长沙，样例文件位于 [`data/samples`](./data/samples)。

## Tech Stack

- Frontend: React 18 + TypeScript + Vite + Ant Design
- Backend: FastAPI + SQLAlchemy + Alembic
- Data processing: pandas + openpyxl
- Database: SQLite for local startup, PostgreSQL supported via env
- Authentication: JWT + role-based access control
- LLM fallback: DeepSeek

## Repository Layout

```text
.
├── backend/               FastAPI app, models, services, parsers, exporters
├── frontend/              React app
├── data/
│   ├── samples/           Regional sample files
│   ├── templates/         Export templates and regression fixtures
│   ├── outputs/           Generated export files
│   └── external/          External source data
├── tests/                 Cross-cutting integration/security tests
├── backend/tests/         Backend service and API regression tests
├── AGENTS.md              Project-specific agent rules
├── architecture.md        Architecture and workflow design
├── OPERATIONS.md          Supported local/deployment operations
└── DEPLOYMENT.md          Deployment instructions
```

## Supported Local Startup

本仓库当前的推荐本地启动方式是根目录包装脚本：

- `start_project_local.cmd`
- `start_project_local.ps1`

它们会分别拉起：

- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:5173`

### What The Wrapper Starts

后端脚本等价于：

```powershell
$env:DATABASE_URL = "sqlite:///./data/app.db"
.\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head
.\.venv\Scripts\python.exe -m backend.run
```

前端脚本等价于：

```powershell
Set-Location frontend
cmd /c npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

如果你只是要正常本地使用项目，优先走这套包装脚本。

## Manual Development Commands

如果你需要单独调试前后端，可以使用下面的命令。
以下示例假设你已经进入仓库根目录，并使用当前 Python 环境或已激活虚拟环境。

### Backend

安装依赖：

```bash
python -m venv .venv
python -m pip install -r backend/requirements.txt
```

执行迁移并启动：

```bash
python -m alembic -c backend/alembic.ini upgrade head
python -m backend.run
```

### Frontend

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

## Environment Variables

项目使用根目录 [`.env.example`](./.env.example) 作为配置样例。常用变量如下：

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
- `ENABLE_LLM_FALLBACK`
- `VITE_API_BASE_URL`

认证相关的重要变量在后端配置中也已支持：

- `AUTH_ENABLED`
- `AUTH_SECRET_KEY`
- `ADMIN_LOGIN_USERNAME`
- `ADMIN_LOGIN_PASSWORD`
- `HR_LOGIN_USERNAME`
- `HR_LOGIN_PASSWORD`
- `RUNTIME_ENVIRONMENT`

## Local Auth Notes

应用启动时会自动确保数据表存在，并在数据库中没有管理员账号时自动创建一个默认管理员：

- username: `admin`
- password: `admin`

这个默认管理员会被标记为必须修改密码，只建议用于本地开发。

员工入口不依赖后台用户名密码，而是依赖已导入的员工主数据进行身份校验。因此如果你要测试员工自助查询，需要先导入员工主数据。

## API Surface

后端主要 API 分组包括：

- `/api/v1/auth`
- `/api/v1/imports`
- `/api/v1/aggregate`
- `/api/v1/mappings`
- `/api/v1/compare`
- `/api/v1/dashboard`
- `/api/v1/employees`
- `/api/v1/data-management`
- `/api/v1/users`
- `/api/v1/api-keys`
- `/api/v1/audit-logs`

受保护的文档入口：

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Markdown API docs: `http://127.0.0.1:8000/api/v1/docs/markdown`

这些文档路由要求管理员身份。

## Dual Template Export

当前版本要求导出时必须同时生成两份模板，任意一份失败都视为整体失败：

- 薪酬模板
- 工具表最终版模板

模板路径可以通过 `SALARY_TEMPLATE_PATH` 和 `FINAL_TOOL_TEMPLATE_PATH` 显式指定；如果不指定，系统会从 `data/templates` 及相关默认路径中查找。

## Testing

后端测试：

```bash
python -m pytest backend/tests -p no:cacheprovider
python -m pytest tests -p no:cacheprovider
```

前端检查：

```bash
cd frontend
npm run lint
npm run build
```

常见重点测试覆盖包括：

- 地区样例解析回归
- 非明细行过滤
- 标准化与校验
- 工号匹配
- 双模板导出
- 认证、权限、API Key、审计

## Key Documents

- 项目约束与代理工作规则：[AGENTS.md](./AGENTS.md)
- 架构设计：[architecture.md](./architecture.md)
- 运行约定：[OPERATIONS.md](./OPERATIONS.md)
- 部署文档：[DEPLOYMENT.md](./DEPLOYMENT.md)

## Notes For Maintainers

- 规则优先，LLM 只做兜底，不要反过来设计主链路。
- 不要把地区差异硬编码到前端页面。
- 不要依赖固定 sheet 名、固定起始行或固定列号。
- 标准化结果必须保留源文件、源行号和原始字段溯源信息。
- 双模板导出是硬要求，不能只生成其中一份。
