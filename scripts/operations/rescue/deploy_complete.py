#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import os
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

SERVER = "10.0.0.60"
USER = "root"
PASSWORD = "gQJwgfG9obG57p"
PORT = 22
PROJECT_DIR = "/opt/execl_mix"

def exec_cmd(ssh, cmd, desc=""):
    if desc:
        print(f"\n>>> {desc}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out:
        print(out)
    if err and exit_code != 0:
        print(f"ERROR: {err}", file=sys.stderr)
    return exit_code == 0

def upload_file(sftp, local, remote):
    try:
        sftp.put(local, remote)
        return True
    except Exception as e:
        print(f"Upload failed: {e}")
        return False

def upload_dir(sftp, local_dir, remote_dir, exclude=[]):
    for root, dirs, files in os.walk(local_dir):
        # Skip excluded dirs
        dirs[:] = [d for d in dirs if d not in exclude]

        rel_path = os.path.relpath(root, local_dir)
        remote_path = os.path.join(remote_dir, rel_path).replace('\\', '/')

        try:
            sftp.stat(remote_path)
        except:
            sftp.mkdir(remote_path)

        for file in files:
            if any(file.endswith(ext) for ext in ['.pyc', '.pyo']):
                continue
            local_file = os.path.join(root, file)
            remote_file = os.path.join(remote_path, file).replace('\\', '/')
            print(f"  {local_file} -> {remote_file}")
            upload_file(sftp, local_file, remote_file)

print("=== Connecting to server ===")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(SERVER, port=PORT, username=USER, password=PASSWORD, timeout=10)
    print(f"[OK] Connected to {SERVER}")
except Exception as e:
    print(f"[ERROR] Failed: {e}")
    sys.exit(1)

sftp = ssh.open_sftp()

# Step 1: Create directories
print("\n=== Step 1: Creating directories ===")
exec_cmd(ssh, f"mkdir -p {PROJECT_DIR}/backend {PROJECT_DIR}/frontend {PROJECT_DIR}/data/uploads {PROJECT_DIR}/data/outputs {PROJECT_DIR}/data/templates")

# Step 2: Upload backend
print("\n=== Step 2: Uploading backend ===")
upload_dir(sftp, "backend", f"{PROJECT_DIR}/backend", exclude=['__pycache__', '.venv', 'tests'])

# Step 3: Upload frontend
print("\n=== Step 3: Uploading frontend ===")
upload_dir(sftp, "frontend", f"{PROJECT_DIR}/frontend", exclude=['node_modules', 'dist', 'build'])

# Step 4: Setup backend
print("\n=== Step 4: Setting up backend ===")
exec_cmd(ssh, f"cd {PROJECT_DIR} && python3 -m venv .venv", "Creating virtual environment")
exec_cmd(ssh, f"cd {PROJECT_DIR} && .venv/bin/pip install --upgrade pip", "Upgrading pip")
exec_cmd(ssh, f"cd {PROJECT_DIR} && .venv/bin/pip install -r backend/requirements.txt", "Installing dependencies")

# Step 5: Setup frontend
print("\n=== Step 5: Setting up frontend ===")
exec_cmd(ssh, f"cd {PROJECT_DIR}/frontend && npm install", "Installing npm packages")
exec_cmd(ssh, f"cd {PROJECT_DIR}/frontend && npm run build", "Building frontend")

# Step 6: Create systemd service
print("\n=== Step 6: Creating systemd service ===")
service_content = f"""[Unit]
Description=Excel Mix Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={PROJECT_DIR}
Environment="PATH={PROJECT_DIR}/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart={PROJECT_DIR}/.venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
"""
exec_cmd(ssh, f"cat > /etc/systemd/system/execl-mix.service << 'EOF'\n{service_content}\nEOF")
exec_cmd(ssh, "systemctl daemon-reload")
exec_cmd(ssh, "systemctl enable execl-mix")
exec_cmd(ssh, "systemctl restart execl-mix")
exec_cmd(ssh, "sleep 2 && systemctl status execl-mix --no-pager")

print("\n=== Deployment Complete ===")
print(f"Backend: http://{SERVER}:8000")
print(f"Check logs: ssh {USER}@{SERVER} 'journalctl -u execl-mix -f'")

sftp.close()
ssh.close()
