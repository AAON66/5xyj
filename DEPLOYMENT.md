# 部署指南

本文档涵盖本地开发、Linux 服务器部署（systemd）、Docker 容器化部署三种方式。

---

## 目录

1. [环境要求](#1-环境要求)
2. [环境变量说明](#2-环境变量说明)
3. [本地开发（Windows）](#3-本地开发windows)
4. [Linux 服务器部署](#4-linux-服务器部署)
5. [Docker 部署](#5-docker-部署)
6. [Nginx 反向代理](#6-nginx-反向代理)
7. [数据库：SQLite vs PostgreSQL](#7-数据库sqlite-vs-postgresql)
8. [认证配置](#8-认证配置)
9. [模板文件配置](#9-模板文件配置)
10. [验证与回归测试](#10-验证与回归测试)
11. [已知限制](#11-已知限制)

---

## 1. 环境要求

| 组件 | 最低版本 | 说明 |
|------|----------|------|
| Python | 3.11+ | 后端运行时 |
| Node.js | 18+ | 前端构建 |
| pip | 23+ | Python 包管理 |
| npm | 9+ | 前端包管理 |
| SQLite | 3.35+ | 默认数据库（开发） |
| PostgreSQL | 14+ | 推荐生产数据库 |

---

## 2. 环境变量说明

复制 `.env.example` 为 `.env`，按需修改：

```env
# 应用基础
APP_NAME=社保表格聚合工具
APP_VERSION=0.1.0
API_V1_PREFIX=/api/v1

# CORS（前端地址，多个用 JSON 数组）
BACKEND_CORS_ORIGINS=["http://localhost:5173","https://your-domain.com"]

# 数据库（开发用 SQLite，生产用 PostgreSQL）
DATABASE_URL=sqlite:///./data/app.db
# DATABASE_URL=postgresql://user:password@localhost:5432/social_security_db

# 文件目录（相对于项目根目录，或绝对路径）
UPLOAD_DIR=./data/uploads
SAMPLES_DIR=./data/samples
TEMPLATES_DIR=./data/templates
OUTPUTS_DIR=./data/outputs

# 必须配置：两份导出模板的绝对路径
SALARY_TEMPLATE_PATH=/path/to/2026年02月社保公积金_模板（薪酬）.xlsx
FINAL_TOOL_TEMPLATE_PATH=/path/to/2026年02月社保公积金工具表_模板（最终版）.xlsx

# DeepSeek（可选，留空则只使用规则链路）
DEEPSEEK_API_KEY=
DEEPSEEK_API_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
ENABLE_LLM_FALLBACK=true

# 认证（生产环境务必修改默认密码）
AUTH_ENABLED=true
ADMIN_PASSWORD=admin123
HR_PASSWORD=hr123
AUTH_SECRET_KEY=请替换为随机长字符串
AUTH_TOKEN_TTL_MINUTES=480

# 日志
LOG_LEVEL=INFO
LOG_FORMAT=json

# 前端访问后端的地址（构建时注入）
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

> **生产环境必改项**：
> - `ADMIN_PASSWORD`、`HR_PASSWORD`：使用强密码
> - `AUTH_SECRET_KEY`：使用至少 32 位随机字符串（`openssl rand -hex 32`）
> - `BACKEND_CORS_ORIGINS`：只允许实际前端域名
> - `VITE_API_BASE_URL`：指向生产后端地址

---

## 3. 本地开发（Windows）

### 后端

```powershell
# 创建虚拟环境
py -m venv .venv
.\.venv\Scripts\activate

# 安装依赖
pip install -r backend\requirements.txt

# 数据库迁移
python -m alembic -c backend\alembic.ini upgrade head

# 启动
python backend\run.py
# → http://127.0.0.1:8000
```

### 前端

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
# → http://127.0.0.1:5173
```

### 一键启动脚本

项目根目录提供了 PowerShell 脚本：

```powershell
# 启动后端
.\start_backend_local.ps1

# 启动前端（另开终端）
.\start_frontend_local.ps1
```

---

## 4. Linux 服务器部署

适用于 Ubuntu 22.04 / CentOS 8+ 等发行版。

### 4.1 系统准备

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm nginx git

# CentOS/RHEL
sudo dnf install -y python3.11 nodejs npm nginx git
```

### 4.2 部署代码

```bash
# 创建应用目录
sudo mkdir -p /opt/execl_mix
sudo chown $USER:$USER /opt/execl_mix

# 克隆或上传代码
git clone <repo-url> /opt/execl_mix
cd /opt/execl_mix

# 复制并编辑环境变量
cp .env.example .env
nano .env   # 填写生产配置
```

### 4.3 后端部署

```bash
cd /opt/execl_mix

# 创建虚拟环境
python3.11 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r backend/requirements.txt

# 创建数据目录（如使用 SQLite）
mkdir -p data/uploads data/samples data/templates data/outputs

# 执行数据库迁移
python -m alembic -c backend/alembic.ini upgrade head

# 测试启动
python backend/run.py
```

### 4.4 前端构建

```bash
cd /opt/execl_mix/frontend

# 确保 VITE_API_BASE_URL 在 .env 中已设置为生产地址
# 例如：VITE_API_BASE_URL=https://your-domain.com/api/v1

npm install
npm run build
# 构建产物在 frontend/dist/
```

### 4.5 配置 systemd 服务（后端）

```bash
sudo nano /etc/systemd/system/execl-mix-backend.service
```

```ini
[Unit]
Description=社保表格聚合工具 - Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/execl_mix
EnvironmentFile=/opt/execl_mix/.env
ExecStart=/opt/execl_mix/.venv/bin/python backend/run.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable execl-mix-backend
sudo systemctl start execl-mix-backend
sudo systemctl status execl-mix-backend

# 查看日志
sudo journalctl -u execl-mix-backend -f
```

### 4.6 修改后端监听地址

如果需要后端监听所有网卡（配合 Nginx 使用），编辑 `backend/run.py`：

```python
# 将 host="127.0.0.1" 改为 host="0.0.0.0"（仅内网时使用）
# 如果使用 Nginx 反代，保持 127.0.0.1 更安全
uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, ...)
```

---

## 5. Docker 部署

### 5.1 目录结构准备

在项目根创建以下 Docker 文件：

**`Dockerfile.backend`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY .env .env

# 创建数据目录
RUN mkdir -p data/uploads data/samples data/templates data/outputs

EXPOSE 8000

CMD ["python", "backend/run.py"]
```

**`Dockerfile.frontend`**

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
ARG VITE_API_BASE_URL
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

**`docker-compose.yml`**

```yaml
version: "3.9"

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data            # 持久化数据目录
      - ./templates:/app/templates  # 导出模板文件
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
      args:
        VITE_API_BASE_URL: ${VITE_API_BASE_URL}
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

### 5.2 启动

```bash
# 构建并启动
docker compose up -d --build

# 初次运行迁移（仅首次）
docker compose exec backend python -m alembic -c backend/alembic.ini upgrade head

# 查看日志
docker compose logs -f backend

# 停止
docker compose down
```

### 5.3 模板文件挂载

导出模板需要挂载到容器内，在 `docker-compose.yml` 的 volumes 中添加：

```yaml
volumes:
  - /host/path/to/templates:/app/data/templates
```

并在 `.env` 中设置：

```env
SALARY_TEMPLATE_PATH=/app/data/templates/薪酬模板.xlsx
FINAL_TOOL_TEMPLATE_PATH=/app/data/templates/工具表最终版模板.xlsx
```

---

## 6. Nginx 反向代理

### 6.1 HTTP 配置

```bash
sudo nano /etc/nginx/sites-available/execl-mix
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    root /opt/execl_mix/frontend/dist;
    index index.html;

    # 前端路由（SPA 回退）
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 文件上传超时（大文件）
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
        client_max_body_size 100M;
    }

    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/execl-mix /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6.2 HTTPS 配置（Let's Encrypt）

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
sudo systemctl reload nginx
```

Certbot 会自动修改 nginx 配置添加 HTTPS。

---

## 7. 数据库：SQLite vs PostgreSQL

### SQLite（默认，适合单机/小团队）

```env
DATABASE_URL=sqlite:///./data/app.db
```

- 无需额外安装
- 文件位于 `data/app.db`，注意定期备份
- 不支持高并发写入

### PostgreSQL（推荐生产环境）

```bash
# 安装 PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# 创建数据库和用户
sudo -u postgres psql
```

```sql
CREATE DATABASE social_security_db;
CREATE USER ssapp WITH ENCRYPTED PASSWORD 'your-strong-password';
GRANT ALL PRIVILEGES ON DATABASE social_security_db TO ssapp;
\q
```

```env
DATABASE_URL=postgresql://ssapp:your-strong-password@localhost:5432/social_security_db
```

```bash
# 重新执行迁移
python -m alembic -c backend/alembic.ini upgrade head
```

### 数据库备份

```bash
# SQLite 备份
cp data/app.db data/app.db.$(date +%Y%m%d)

# PostgreSQL 备份
pg_dump -U ssapp social_security_db > backup_$(date +%Y%m%d).sql
```

---

## 8. 认证配置

系统使用 HMAC-SHA256 自定义 Token，支持两个内置角色：

| 角色 | 环境变量 | 默认密码 | 权限 |
|------|----------|----------|------|
| admin | `ADMIN_PASSWORD` | admin123 | 全部功能 |
| hr | `HR_PASSWORD` | hr123 | 导入、查看、员工自助 |

**生产环境必须修改的配置：**

```env
ADMIN_PASSWORD=强密码至少12位含大小写数字符号
HR_PASSWORD=强密码至少12位含大小写数字符号
AUTH_SECRET_KEY=$(openssl rand -hex 32)
AUTH_TOKEN_TTL_MINUTES=480    # Token 有效期（分钟）
AUTH_ENABLED=true
```

**关闭认证（仅限开发调试）：**

```env
AUTH_ENABLED=false
```

---

## 9. 模板文件配置

系统必须能访问两份 Excel 导出模板，否则导出功能将失败。

```env
SALARY_TEMPLATE_PATH=/absolute/path/to/2026年02月社保公积金_模板（薪酬）.xlsx
FINAL_TOOL_TEMPLATE_PATH=/absolute/path/to/2026年02月社保公积金工具表_模板（最终版）.xlsx
```

**注意事项：**
- 路径必须是绝对路径，或相对于后端启动目录的相对路径
- 服务器上文件名中的中文字符需确保文件系统编码为 UTF-8
- 两份模板缺一不可，任意一份不可访问则导出阻塞

**建议将模板文件放到项目目录内统一管理：**

```bash
mkdir -p /opt/execl_mix/data/templates
cp 薪酬模板.xlsx /opt/execl_mix/data/templates/
cp 工具表最终版模板.xlsx /opt/execl_mix/data/templates/
```

```env
SALARY_TEMPLATE_PATH=./data/templates/薪酬模板.xlsx
FINAL_TOOL_TEMPLATE_PATH=./data/templates/工具表最终版模板.xlsx
```

---

## 10. 验证与回归测试

### 健康检查

```bash
curl http://localhost:8000/health
# 期望返回：{"status": "ok", ...}
```

### 后端回归测试

```bash
source .venv/bin/activate

# 全量测试
python -m pytest backend/tests -p no:cacheprovider -v

# 地区样例解析回归
python -m pytest backend/tests/test_region_sample_regression.py -v

# 双模板导出回归
python -m pytest backend/tests/test_template_exporter_regression.py -v

# DeepSeek 降级行为验证
python -m pytest backend/tests/test_llm_mapping_service.py -v
```

### 前端构建验证

```bash
cd frontend
npm run lint    # 代码检查
npm run build   # 生产构建
```

### 端到端操作验证清单

- [ ] 健康检查接口返回正常
- [ ] 能以 admin 身份登录
- [ ] 能上传广州格式 Excel 并解析
- [ ] 能上传深圳格式 Excel 并解析
- [ ] 非明细行（合计/小计）未出现在标准化结果中
- [ ] 字段映射页可以修正低置信度字段
- [ ] 数据校验通过后能触发工号匹配
- [ ] 导出后能在 `OUTPUTS_DIR` 中找到两份模板文件

---

## 11. 已知限制

| 限制 | 说明 |
|------|------|
| 员工主数据管理 | 目前支持导入和查询，不支持单条编辑/删除 |
| DeepSeek 回归 | 自动化测试中未包含真实 LLM 调用（网络依赖不稳定） |
| 并发写入 | SQLite 不适合多用户同时写入；高并发场景请切换 PostgreSQL |
| 模板路径 | 模板文件路径变更后需重启后端服务 |
| 员工匹配 | 匹配前必须已导入员工主数据，否则匹配步骤阻塞 |
