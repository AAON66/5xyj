#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import sys
import time

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

SERVER = "10.0.0.60"
USER = "root"
PASSWORD = "gQJwgfG9obG57p"
PORT = 22

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, port=PORT, username=USER, password=PASSWORD, timeout=10)

print("=== 检查Python版本 ===")
stdin, stdout, stderr = ssh.exec_command("python3.11 --version || echo 'Python 3.11 not found'")
stdout.channel.recv_exit_status()
print(stdout.read().decode())

print("\n=== 完全清理旧环境 ===")
stdin, stdout, stderr = ssh.exec_command("cd /opt/execl_mix && rm -rf .venv __pycache__ backend/app/__pycache__ backend/app/*/__pycache__")
stdout.channel.recv_exit_status()

print("\n=== 创建Python 3.11虚拟环境 ===")
stdin, stdout, stderr = ssh.exec_command("cd /opt/execl_mix && /usr/bin/python3.11 -m venv .venv")
stdout.channel.recv_exit_status()

print("\n=== 安装依赖 ===")
stdin, stdout, stderr = ssh.exec_command("cd /opt/execl_mix && .venv/bin/pip install -q fastapi uvicorn[standard] python-multipart sqlalchemy pydantic pydantic-settings httpx pandas openpyxl python-dotenv loguru alembic")
stdout.channel.recv_exit_status()
print("完成")

print("\n=== 启动服务 ===")
stdin, stdout, stderr = ssh.exec_command("pkill -f uvicorn; sleep 2; cd /opt/execl_mix && nohup .venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > /tmp/execl-mix.log 2>&1 &")
stdout.channel.recv_exit_status()
time.sleep(6)

print("\n=== 测试 ===")
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/api/v1/system/health")
stdout.channel.recv_exit_status()
result = stdout.read().decode()

if result and "{" in result:
    print(result)
    print(f"\n✓ 部署成功!")
    print(f"后端: http://{SERVER}:8000")
else:
    stdin, stdout, stderr = ssh.exec_command("tail -25 /tmp/execl-mix.log")
    stdout.channel.recv_exit_status()
    print(stdout.read().decode())

ssh.close()
