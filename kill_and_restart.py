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

print("=== 杀掉所有相关进程 ===")
stdin, stdout, stderr = ssh.exec_command("pkill -9 -f uvicorn; pkill -9 -f 'python.*backend'")
stdout.channel.recv_exit_status()
time.sleep(2)

print("\n=== 清理日志 ===")
stdin, stdout, stderr = ssh.exec_command("rm -f /tmp/execl-mix.log")
stdout.channel.recv_exit_status()

print("\n=== 启动服务 ===")
stdin, stdout, stderr = ssh.exec_command("cd /opt/execl_mix && nohup .venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > /tmp/execl-mix.log 2>&1 &")
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
    print(f"文档: http://{SERVER}:8000/docs")
else:
    stdin, stdout, stderr = ssh.exec_command("cat /tmp/execl-mix.log")
    stdout.channel.recv_exit_status()
    log = stdout.read().decode()
    print(log[-1000:] if len(log) > 1000 else log)

ssh.close()
