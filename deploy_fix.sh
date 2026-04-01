#!/bin/bash
# 快速修复部署脚本

echo "=== 1. 停止旧服务 ==="
pkill -f uvicorn
sleep 2

echo "=== 2. 检查端口 ==="
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "端口 8000 仍被占用，强制释放..."
    lsof -ti:8000 | xargs kill -9
fi

echo "=== 3. 启动后端服务 ==="
cd /opt/execl_mix/backend
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /opt/execl_mix/backend.log 2>&1 &

sleep 3

echo "=== 4. 检查服务状态 ==="
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✓ 后端服务启动成功"
else
    echo "✗ 后端服务启动失败，查看日志："
    tail -20 /opt/execl_mix/backend.log
    exit 1
fi
