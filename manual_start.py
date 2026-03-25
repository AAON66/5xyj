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

print("=== Checking error ===")
stdin, stdout, stderr = ssh.exec_command("journalctl -u execl-mix -n 30 --no-pager | grep -E 'Error|Traceback|File.*line' | tail -20")
stdout.channel.recv_exit_status()
print(stdout.read().decode())

print("\n=== Starting manually in background ===")
stdin, stdout, stderr = ssh.exec_command("cd /opt/execl_mix && nohup .venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > /tmp/execl-mix.log 2>&1 &")
stdout.channel.recv_exit_status()
time.sleep(3)

print("\n=== Checking if running ===")
stdin, stdout, stderr = ssh.exec_command("ps aux | grep uvicorn | grep -v grep")
stdout.channel.recv_exit_status()
print(stdout.read().decode())

print("\n=== Testing API ===")
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/api/v1/system/health")
stdout.channel.recv_exit_status()
result = stdout.read().decode()
print(result)

if "healthy" in result or "ok" in result.lower():
    print("\n[SUCCESS] Service is running!")
    print(f"Backend: http://{SERVER}:8000")
else:
    print("\n=== Checking logs ===")
    stdin, stdout, stderr = ssh.exec_command("tail -50 /tmp/execl-mix.log")
    stdout.channel.recv_exit_status()
    print(stdout.read().decode())

ssh.close()
