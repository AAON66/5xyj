# 紧急修复部署指南

## 问题原因
前端配置的 API 地址是本地 `127.0.0.1`，导致公网访问时无法连接后端。

## 修复步骤

### 1. 登录服务器
```bash
ssh root@10.0.0.60
# 密码: gQJwgfG9obG57p
```

### 2. 上传新构建的前端
在本地执行：
```bash
cd D:\execl_mix
scp -r frontend/dist root@10.0.0.60:/opt/execl_mix/frontend/
```

### 3. 修复后端服务
在服务器上执行：
```bash
# 停止旧服务
pkill -f uvicorn

# 检查端口
lsof -ti:8000 | xargs kill -9

# 启动后端（监听所有网卡）
cd /opt/execl_mix/backend
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &

# 验证服务
curl http://localhost:8000/health
```

### 4. 配置防火墙（如果 8000 端口无法访问）
```bash
# CentOS/RHEL
firewall-cmd --add-port=8000/tcp --permanent
firewall-cmd --reload

# Ubuntu
ufw allow 8000/tcp
```

### 5. 验证修复
浏览器访问：`http://139.199.192.190/login`
- 输入账号：admin
- 输入密码
- 应该能正常登录

## 快速诊断命令
```bash
# 检查后端是否运行
ps aux | grep uvicorn

# 检查端口监听
netstat -tlnp | grep 8000

# 查看后端日志
tail -f /opt/execl_mix/backend/backend.log

# 测试后端接口
curl http://localhost:8000/api/v1/auth/login -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'
```

## 已修复内容
✓ 前端 API 地址改为 `http://139.199.192.190:8000/api/v1`
✓ 前端已重新构建（dist 目录）
✓ 创建了后端启动脚本
