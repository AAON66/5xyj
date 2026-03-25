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

print("=== 彻底删除虚拟环境 ===")
stdin, stdout, stderr = ssh.exec_command("rm -rf /opt/execl_mix/.venv")
stdout.channel.recv_exit_status()

print("=== 用Python 3.11重建 ===")
stdin, stdout, stderr = ssh.exec_command("/usr/bin/python3.11 -m venv /opt/execl_mix/.venv")
stdout.channel.recv_exit_status()

print("=== 检查lib目录 ===")
stdin, stdout, stderr = ssh.exec_command("ls -la /opt/execl_mix/.venv/lib*/")
stdout.channel.recv_exit_status()
print(stdout.read().decode()[:500])

print("\n=== 安装依赖 ===")
stdin, stdout, stderr = ssh.exec_command("/opt/execl_mix/.venv/bin/pip install -q fastapi uvicorn[standard] python-multipart sqlalchemy pydantic pydantic-settings httpx pandas openpyxl python-dotenv loguru alembic")
stdout.channel.recv_exit_status()

print("\n=== 启动 ===")
stdin, stdout, stderr = ssh.exec_command("pkill -f uvicorn; cd /opt/execl_mix && nohup .venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > /tmp/execl-mix.log 2>&1 &")
stdout.channel.recv_exit_status()
time.sleep(8)

print("\n=== 测试 ===")
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/api/v1/system/health")
stdout.channel.recv_exit_status()
result = stdout.read().decode()

if result and "{" in result:
    print(result)
    print(f"\n✓ 成功! http://{SERVER}:8000")
else:
    stdin, stdout, stderr = ssh.exec_command("head -30 /tmp/execl-mix.log")
    stdout.channel.recv_exit_status()
    print(stdout.read().decode())

ssh.close()
