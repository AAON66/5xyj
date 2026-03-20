# 社保表格聚合工具

这是一个基于 React + FastAPI 的社保表格聚合项目，目标是把多地区、多格式的社保 Excel 统一导入、识别、标准化、校验、匹配，并最终同时导出两份固定模板结果。

## 当前状态

当前已完成第一阶段基础搭建：

- 根目录架构与任务文件就位
- 后端目录、依赖清单和最小应用入口已创建
- 前端 Vite + React + TypeScript 基础骨架已创建
- `data/samples`、`data/templates`、`data/outputs` 目录已预留

## 目录结构

```text
.
├── architecture.md
├── task.json
├── progress.txt
├── backend/
├── frontend/
├── data/
└── tests/
```

## 快速启动

### 后端

```powershell
cd backend
py -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 前端

```powershell
cd frontend
cmd /c npm.cmd install
cmd /c npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

## 环境变量

复制根目录的 `.env.example` 后按需填写数据库、DeepSeek 和文件目录配置。

## 下一步

按照 `task.json` 继续推进：

1. 数据库 Schema
2. 配置管理与依赖注入
3. Workbook / 表头 / 字段映射主链路
4. 校验、匹配、双模板导出

