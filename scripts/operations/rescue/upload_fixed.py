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

print("=== Uploading fixed models ===")
sftp = ssh.open_sftp()
sftp.put("backend/app/models/employee_master_audit.py", "/opt/execl_mix/backend/app/models/employee_master_audit.py")
sftp.put("backend/app/models/normalized_record.py", "/opt/execl_mix/backend/app/models/normalized_record.py")
sftp.close()

print("\n=== Restarting ===")
stdin, stdout, stderr = ssh.exec_command("pkill -f uvicorn && sleep 2 && /opt/execl_mix/start.sh")
stdout.channel.recv_exit_status()
print(stdout.read().decode())
time.sleep(5)

print("\n=== Testing ===")
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/api/v1/system/health")
stdout.channel.recv_exit_status()
result = stdout.read().decode()
print(result)

if result and "{" in result:
    print(f"\n✓ 部署成功!")
    print(f"后端: http://{SERVER}:8000")
    print(f"文档: http://{SERVER}:8000/docs")
else:
    stdin, stdout, stderr = ssh.exec_command("tail -30 /tmp/execl-mix.log")
    stdout.channel.recv_exit_status()
    print("\n" + stdout.read().decode())

ssh.close()
