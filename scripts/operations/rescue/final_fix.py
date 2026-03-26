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

print("=== 直接修复服务器上的类型注解 ===")
stdin, stdout, stderr = ssh.exec_command(r"""cd /opt/execl_mix/backend/app/models && sed -i 's/dict\[str, object\] | None/Optional[dict[str, object]]/g' *.py""")
stdout.channel.recv_exit_status()

print("\n=== 验证Python 3.11虚拟环境 ===")
stdin, stdout, stderr = ssh.exec_command("cd /opt/execl_mix && .venv/bin/python --version")
stdout.channel.recv_exit_status()
print(stdout.read().decode())

print("\n=== 启动 ===")
stdin, stdout, stderr = ssh.exec_command("pkill -f uvicorn; cd /opt/execl_mix && nohup .venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > /tmp/execl-mix.log 2>&1 & sleep 6")
stdout.channel.recv_exit_status()

print("\n=== 测试 ===")
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/api/v1/system/health")
stdout.channel.recv_exit_status()
result = stdout.read().decode()

if result and "{" in result:
    print(result)
    print(f"\n✓ 成功! 后端: http://{SERVER}:8000")
else:
    stdin, stdout, stderr = ssh.exec_command("tail -20 /tmp/execl-mix.log")
    stdout.channel.recv_exit_status()
    print(stdout.read().decode())

ssh.close()
