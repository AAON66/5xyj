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

print("=== 清理并重建 ===")
commands = [
    "cd /opt/execl_mix && rm -rf .venv",
    "find /opt/execl_mix -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true",
    "cd /opt/execl_mix && python3.11 -m venv .venv",
]

for cmd in commands:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    stdout.channel.recv_exit_status()

print("完成\n")

print("=== 安装依赖 ===")
stdin, stdout, stderr = ssh.exec_command("cd /opt/execl_mix && .venv/bin/pip install -q fastapi uvicorn[standard] python-multipart sqlalchemy pydantic pydantic-settings httpx pandas openpyxl python-dotenv loguru alembic")
stdout.channel.recv_exit_status()
print("完成\n")

print("=== 修复类型注解 ===")
stdin, stdout, stderr = ssh.exec_command("cd /opt/execl_mix/backend/app/models && sed -i 's/dict\\[str, object\\] | None/Optional[dict[str, object]]/g' employee_master_audit.py normalized_record.py")
stdout.channel.recv_exit_status()
print("完成\n")

print("=== 启动服务 ===")
stdin, stdout, stderr = ssh.exec_command("pkill -f uvicorn; cd /opt/execl_mix && nohup .venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > /tmp/execl-mix.log 2>&1 &")
stdout.channel.recv_exit_status()
time.sleep(8)

print("=== 测试 ===")
for i in range(3):
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/api/v1/system/health")
    stdout.channel.recv_exit_status()
    result = stdout.read().decode()
    if result and "{" in result:
        print(result)
        print(f"\n✓ 部署成功!")
        print(f"\n访问地址:")
        print(f"  后端API: http://{SERVER}:8000")
        print(f"  API文档: http://{SERVER}:8000/docs")
        break
    time.sleep(3)
else:
    stdin, stdout, stderr = ssh.exec_command("tail -30 /tmp/execl-mix.log")
    stdout.channel.recv_exit_status()
    print(stdout.read().decode())

ssh.close()
