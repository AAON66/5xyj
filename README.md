# 社保表格聚合工具

基于 **React + FastAPI** 的多地区社保/公积金表格自动化处理系统。

支持广州、杭州、厦门、深圳、武汉、长沙等地区的原始申报明细表，自动完成：
表头识别 → 字段标准化 → 数据校验 → 工号匹配 → 双模板导出。

---

## 功能概览

| 模块 | 说明 |
|------|------|
| 文件导入 | 批量上传多地区 Excel 文件，自动识别工作表和表头行 |
| 字段标准化 | 170+ 规则映射同义字段，DeepSeek 兜底不确定项 |
| 数据校验 | 检测缺失、重复、异常值，标记非明细行 |
| 工号匹配 | 与员工主数据对比，支持精确/低置信度/未匹配分类 |
| 双模板导出 | 同时输出「薪酬模板」和「工具表最终版」两份 Excel |
| 看板 | 展示各批次导入、识别、校验、导出状态 |
| 字段映射管理 | 对低置信度字段进行人工修正 |
| 员工主数据 | 支持 CSV/XLSX 批量导入，支持员工自助查询 |

---

## 技术栈

- **前端**：React 18 + TypeScript + Vite
- **后端**：FastAPI + SQLAlchemy 2 + Alembic
- **数据处理**：pandas、openpyxl
- **数据库**：SQLite（开发）/ PostgreSQL（生产推荐）
- **LLM 兜底**：DeepSeek（可选，无 Key 时规则链路正常运行）
- **认证**：自定义 HMAC-SHA256 Token，admin / hr 双角色

---

## 目录结构

```
execl_mix/
├── backend/               # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/        # API 路由
│   │   ├── core/          # 配置、数据库、认证
│   │   ├── models/        # SQLAlchemy 模型（11张表）
│   │   ├── parsers/       # Excel 解析器
│   │   ├── services/      # 业务逻辑（16个服务）
│   │   ├── mappings/      # 字段别名规则
│   │   ├── exporters/     # 双模板导出
│   │   ├── validators/    # 数据校验
│   │   └── matchers/      # 工号匹配
│   ├── alembic/           # 数据库迁移
│   ├── tests/             # 自动化测试
│   ├── run.py             # 启动入口
│   └── requirements.txt
├── frontend/              # React 前端
│   ├── src/
│   │   ├── pages/         # 18个页面组件
│   │   ├── components/    # 公共组件
│   │   └── services/      # API 客户端
│   └── package.json
├── data/
│   ├── uploads/           # 用户上传文件
│   ├── samples/           # 地区样例文件
│   ├── templates/         # 导出模板文件
│   └── outputs/           # 生成的导出文件
├── .env.example           # 环境变量模板
├── architecture.md        # 系统架构文档
└── DEPLOYMENT.md          # 部署指南
```

---

## 快速开始（本地开发）

### 1. 克隆仓库并配置环境变量

```bash
git clone <repo-url>
cd execl_mix
cp .env.example .env
```

编辑 `.env`，至少填写以下内容：

```env
DATABASE_URL=sqlite:///./data/app.db
SALARY_TEMPLATE_PATH=/path/to/薪酬模板.xlsx
FINAL_TOOL_TEMPLATE_PATH=/path/to/工具表最终版模板.xlsx
```

### 2. 启动后端

```bash
# 安装依赖（建议使用虚拟环境）
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.\.venv\Scripts\activate         # Windows

pip install -r backend/requirements.txt

# 执行数据库迁移
python -m alembic -c backend/alembic.ini upgrade head

# 启动服务
python backend/run.py
```

后端地址：`http://127.0.0.1:8000`
接口文档：`http://127.0.0.1:8000/docs`

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端地址：`http://127.0.0.1:5173`

### 4. 登录

| 角色 | 账号 | 默认密码 | 权限 |
|------|------|----------|------|
| admin | admin | admin123 | 全部功能 |
| hr | hr | hr123 | 导入、查看、员工自助 |

> 密码通过 `.env` 中的 `ADMIN_PASSWORD` / `HR_PASSWORD` 修改。

---

## 主要 API

```
GET  /api/v1/system/health           健康检查
POST /api/v1/auth/login              登录
GET  /api/v1/auth/me                 当前用户信息

POST /api/v1/imports                 创建导入批次（上传文件）
GET  /api/v1/imports                 批次列表
GET  /api/v1/imports/{batch_id}      批次详情
POST /api/v1/imports/{batch_id}/parse     触发解析
GET  /api/v1/imports/{batch_id}/preview   预览标准化结果
POST /api/v1/imports/{batch_id}/validate  触发数据校验
POST /api/v1/imports/{batch_id}/match     触发工号匹配
POST /api/v1/imports/{batch_id}/export    触发双模板导出
GET  /api/v1/exports                 导出任务列表

GET  /api/v1/mappings                字段映射列表
PATCH /api/v1/mappings/{mapping_id}  修正字段映射

GET  /api/v1/employees               员工列表
POST /api/v1/employees/import        批量导入员工主数据

GET  /api/v1/dashboard/overview      看板统计
```

---

## 操作流程

1. 登录系统，检查看板健康状态
2. 进入「导入」页，上传一个或多个地区的 Excel 文件
3. 打开批次详情，触发解析，查看识别结果
4. 如有字段识别错误，在「字段映射」页手动修正
5. 触发「数据校验」，处理标记的异常
6. 确认员工主数据已导入后，触发「工号匹配」
7. 触发「导出」，在 `OUTPUTS_DIR` 目录取回两份模板文件
8. 查看看板确认状态

---

## 测试

```bash
# 后端单元/集成测试
.venv/bin/python -m pytest backend/tests -p no:cacheprovider

# 地区样例回归测试
.venv/bin/python -m pytest backend/tests/test_region_sample_regression.py

# 双模板导出回归测试
.venv/bin/python -m pytest backend/tests/test_template_exporter_regression.py

# 前端 lint + build
cd frontend
npm run lint
npm run build
```

---

## 服务器部署

详见 [DEPLOYMENT.md](./DEPLOYMENT.md)。
