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

print("=== 检查实际Python版本 ===")
stdin, stdout, stderr = ssh.exec_command("/opt/execl_mix/.venv/bin/python -c 'import sys; print(sys.version); print(sys.path)'")
stdout.channel.recv_exit_status()
print(stdout.read().decode()[:300])

print("\n=== 检查site-packages实际位置 ===")
stdin, stdout, stderr = ssh.exec_command("find /opt/execl_mix/.venv -name 'sqlalchemy' -type d 2>/dev/null")
stdout.channel.recv_exit_status()
result = stdout.read().decode()
print(result if result else "未找到sqlalchemy")

ssh.close()
