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

print("=== 创建启动脚本（清理环境变量） ===")
stdin, stdout, stderr = ssh.exec_command("""cat > /opt/execl_mix/start_clean.sh << 'EOF'
#!/bin/bash
cd /opt/execl_mix
export PYTHONPATH=""
export PYTHONHOME=""
.venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
EOF
chmod +x /opt/execl_mix/start_clean.sh""")
stdout.channel.recv_exit_status()

print("\n=== 启动 ===")
stdin, stdout, stderr = ssh.exec_command("pkill -f uvicorn; nohup /opt/execl_mix/start_clean.sh > /tmp/execl-mix.log 2>&1 &")
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
else:
    stdin, stdout, stderr = ssh.exec_command("tail -15 /tmp/execl-mix.log")
    stdout.channel.recv_exit_status()
    print(stdout.read().decode())

ssh.close()
