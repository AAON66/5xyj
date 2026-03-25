#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import sys

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

SERVER = "10.0.0.60"
USER = "root"
PASSWORD = "gQJwgfG9obG57p"
PORT = 22

def exec_cmd(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)
    return exit_code == 0

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, port=PORT, username=USER, password=PASSWORD, timeout=10)

print("=== Installing Python 3.9 ===")
exec_cmd(ssh, "yum install -y python39 python39-pip")

print("\n=== Recreating venv with Python 3.9 ===")
exec_cmd(ssh, "cd /opt/execl_mix && rm -rf .venv && python3.9 -m venv .venv")

print("\n=== Installing dependencies ===")
exec_cmd(ssh, "cd /opt/execl_mix && .venv/bin/pip install --upgrade pip")
exec_cmd(ssh, "cd /opt/execl_mix && .venv/bin/pip install fastapi uvicorn[standard] python-multipart sqlalchemy pydantic httpx pandas openpyxl python-dotenv loguru alembic")

print("\n=== Restarting service ===")
exec_cmd(ssh, "systemctl restart execl-mix")
exec_cmd(ssh, "sleep 3 && systemctl status execl-mix --no-pager")

print("\n=== Testing API ===")
exec_cmd(ssh, "sleep 2 && curl -s http://localhost:8000/api/v1/system/health")

ssh.close()
