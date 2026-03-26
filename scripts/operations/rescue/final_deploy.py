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

print("=== Adding future annotations ===")
stdin, stdout, stderr = ssh.exec_command("""cd /opt/execl_mix/backend/app/core && sed -i '1i from __future__ import annotations' config.py""")
stdout.channel.recv_exit_status()

print("\n=== Starting service ===")
stdin, stdout, stderr = ssh.exec_command("cd /opt/execl_mix && nohup .venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > /tmp/execl-mix.log 2>&1 &")
stdout.channel.recv_exit_status()
time.sleep(4)

print("\n=== Testing API ===")
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/api/v1/system/health")
stdout.channel.recv_exit_status()
result = stdout.read().decode()
print(result)

if result:
    print(f"\n[SUCCESS] 部署完成!")
    print(f"后端地址: http://{SERVER}:8000")
    print(f"健康检查: http://{SERVER}:8000/api/v1/system/health")
else:
    print("\n=== 检查日志 ===")
    stdin, stdout, stderr = ssh.exec_command("tail -30 /tmp/execl-mix.log")
    stdout.channel.recv_exit_status()
    print(stdout.read().decode())

ssh.close()
