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

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, port=PORT, username=USER, password=PASSWORD, timeout=10)

print("=== Fixing type annotations ===")
# Fix config.py
stdin, stdout, stderr = ssh.exec_command("""cd /opt/execl_mix/backend/app/core && sed -i 's/: str | None/: Optional[str]/g' config.py && sed -i '7a from typing import Optional' config.py""")
stdout.channel.recv_exit_status()

# Fix all Python files with | None syntax
stdin, stdout, stderr = ssh.exec_command("""cd /opt/execl_mix/backend && find . -name '*.py' -exec sed -i 's/\\(: [A-Za-z_][A-Za-z0-9_]*\\) | None/\\1, None]/g; s/\\]: /]: Optional[/g' {} \\;""")
stdout.channel.recv_exit_status()

print("\n=== Starting service ===")
stdin, stdout, stderr = ssh.exec_command("cd /opt/execl_mix && nohup .venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > /tmp/execl-mix.log 2>&1 & sleep 3")
stdout.channel.recv_exit_status()

print("\n=== Testing ===")
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/api/v1/system/health")
stdout.channel.recv_exit_status()
print(stdout.read().decode())

ssh.close()
