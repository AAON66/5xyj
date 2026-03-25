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

print("=== Creating startup script ===")
stdin, stdout, stderr = ssh.exec_command("""cat > /opt/execl_mix/start.sh << 'EOF'
#!/bin/bash
cd /opt/execl_mix
source .venv/bin/activate
nohup uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > /tmp/execl-mix.log 2>&1 &
echo $! > /tmp/execl-mix.pid
echo "Started with PID $(cat /tmp/execl-mix.pid)"
EOF
chmod +x /opt/execl_mix/start.sh""")
stdout.channel.recv_exit_status()

print("\n=== Stopping old process ===")
stdin, stdout, stderr = ssh.exec_command("pkill -f 'uvicorn backend.app.main' || true")
stdout.channel.recv_exit_status()
time.sleep(2)

print("\n=== Starting service ===")
stdin, stdout, stderr = ssh.exec_command("/opt/execl_mix/start.sh")
stdout.channel.recv_exit_status()
print(stdout.read().decode())
time.sleep(5)

print("\n=== Testing API ===")
for i in range(3):
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/api/v1/system/health")
    stdout.channel.recv_exit_status()
    result = stdout.read().decode()
    if result:
        print(result)
        if "{" in result:
            print(f"\n✓ 部署成功!")
            print(f"\n访问地址:")
            print(f"  后端API: http://{SERVER}:8000")
            print(f"  API文档: http://{SERVER}:8000/docs")
            print(f"\n管理命令:")
            print(f"  启动: ssh {USER}@{SERVER} '/opt/execl_mix/start.sh'")
            print(f"  停止: ssh {USER}@{SERVER} 'pkill -f uvicorn'")
            print(f"  日志: ssh {USER}@{SERVER} 'tail -f /tmp/execl-mix.log'")
            break
    time.sleep(2)
else:
    print("\n=== 查看日志 ===")
    stdin, stdout, stderr = ssh.exec_command("tail -50 /tmp/execl-mix.log")
    stdout.channel.recv_exit_status()
    print(stdout.read().decode())

ssh.close()
