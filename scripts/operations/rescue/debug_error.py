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

print("=== Checking error logs ===")
stdin, stdout, stderr = ssh.exec_command("journalctl -u execl-mix -n 100 --no-pager | grep -A 10 'Traceback\\|Error\\|Failed'")
stdout.channel.recv_exit_status()
print(stdout.read().decode())

print("\n=== Testing manual start ===")
stdin, stdout, stderr = ssh.exec_command("cd /opt/execl_mix && /opt/execl_mix/.venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 2>&1 | head -20")
stdout.channel.recv_exit_status()
print(stdout.read().decode())

ssh.close()
