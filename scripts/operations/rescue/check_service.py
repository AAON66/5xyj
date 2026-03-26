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

print("=== Checking uvicorn ===")
exec_cmd(ssh, "/opt/execl_mix/.venv/bin/uvicorn --version")

print("\n=== Checking logs ===")
exec_cmd(ssh, "journalctl -u execl-mix -n 50 --no-pager")

print("\n=== Testing manual start ===")
exec_cmd(ssh, "cd /opt/execl_mix && /opt/execl_mix/.venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &")

ssh.close()
