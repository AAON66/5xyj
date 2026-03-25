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

print("=== 清理所有缓存 ===")
stdin, stdout, stderr = ssh.exec_command("cd /opt/execl_mix && find . -type f -name '*.pyc' -delete && find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true")
stdout.channel.recv_exit_status()

print("=== 重新上传所有backend文件 ===")
sftp = ssh.open_sftp()
import os
count = 0
for root, dirs, files in os.walk("backend/app"):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for file in files:
        if file.endswith('.py'):
            local = os.path.join(root, file)
            remote = f"/opt/execl_mix/{local}".replace('\\', '/')
            sftp.put(local, remote)
            count += 1
sftp.close()
print(f"上传了 {count} 个文件")

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
    print(f"\n✓ 部署成功!")
    print(f"后端: http://{SERVER}:8000")
else:
    stdin, stdout, stderr = ssh.exec_command("tail -15 /tmp/execl-mix.log")
    stdout.channel.recv_exit_status()
    print(stdout.read().decode())

ssh.close()
