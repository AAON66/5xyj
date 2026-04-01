#!/bin/bash
# 自动部署脚本 - 在服务器上执行

set -e

echo "=== 开始修复部署 ==="

# 1. 停止旧服务
echo "1. 停止旧的后端服务..."
pkill -f uvicorn || true
sleep 2

# 2. 清理端口
echo "2. 检查并清理 8000 端口..."
if command -v lsof &> /dev/null; then
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
fi

# 3. 检查目录
echo "3. 检查项目目录..."
cd /opt/execl_mix
ls -la

# 4. 启动后端
echo "4. 启动后端服务（监听所有网卡）..."
cd /opt/execl_mix/backend
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /opt/execl_mix/backend.log 2>&1 &

sleep 3

# 5. 验证服务
echo "5. 验证后端服务..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ 后端服务启动成功"
    ps aux | grep uvicorn | grep -v grep
else
    echo "✗ 后端服务启动失败，查看日志："
    tail -30 /opt/execl_mix/backend.log
    exit 1
fi

# 6. 检查端口监听
echo "6. 检查端口监听状态..."
if command -v netstat &> /dev/null; then
    netstat -tlnp | grep 8000
elif command -v ss &> /dev/null; then
    ss -tlnp | grep 8000
fi

echo ""
echo "=== 修复完成 ==="
echo "后端服务已启动在 0.0.0.0:8000"
echo "日志文件: /opt/execl_mix/backend.log"
echo ""
echo "请访问: http://139.199.192.190/login"
