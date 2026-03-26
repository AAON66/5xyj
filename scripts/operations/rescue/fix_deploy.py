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

print("=== Connecting ===")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, port=PORT, username=USER, password=PASSWORD, timeout=10)
print("[OK] Connected")

print("\n=== Checking Python ===")
exec_cmd(ssh, "python3 --version")

print("\n=== Installing Node.js ===")
exec_cmd(ssh, "curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -")
exec_cmd(ssh, "yum install -y nodejs")
exec_cmd(ssh, "node --version && npm --version")

print("\n=== Updating requirements.txt ===")
exec_cmd(ssh, """cat > /opt/execl_mix/backend/requirements.txt << 'EOF'
fastapi==0.68.0
uvicorn[standard]==0.15.0
python-multipart==0.0.5
sqlalchemy==1.4.23
alembic==1.7.1
pydantic==1.8.2
httpx==0.19.0
pandas==1.3.3
openpyxl==3.0.9
python-dotenv==0.19.0
loguru==0.5.3
pytest==6.2.5
EOF""")

print("\n=== Installing Python packages ===")
exec_cmd(ssh, "cd /opt/execl_mix && .venv/bin/pip install --upgrade pip setuptools")
exec_cmd(ssh, "cd /opt/execl_mix && .venv/bin/pip install -r backend/requirements.txt")

print("\n=== Installing frontend ===")
exec_cmd(ssh, "cd /opt/execl_mix/frontend && npm install")
exec_cmd(ssh, "cd /opt/execl_mix/frontend && npm run build")

print("\n=== Restarting service ===")
exec_cmd(ssh, "systemctl restart execl-mix")
exec_cmd(ssh, "sleep 3 && systemctl status execl-mix --no-pager")

print("\n=== Complete ===")
print(f"Backend: http://{SERVER}:8000")

ssh.close()
