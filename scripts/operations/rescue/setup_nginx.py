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

print("=== 安装Nginx ===")
stdin, stdout, stderr = ssh.exec_command("yum install -y nginx")
stdout.channel.recv_exit_status()

print("\n=== 配置Nginx ===")
nginx_conf = """server {
    listen 80;
    server_name _;

    location / {
        root /opt/execl_mix/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}"""

stdin, stdout, stderr = ssh.exec_command(f"cat > /etc/nginx/conf.d/execl-mix.conf << 'EOF'\n{nginx_conf}\nEOF")
stdout.channel.recv_exit_status()

print("\n=== 启动Nginx ===")
stdin, stdout, stderr = ssh.exec_command("systemctl enable nginx && systemctl restart nginx")
stdout.channel.recv_exit_status()

print("\n=== 测试 ===")
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost/ | head -5")
stdout.channel.recv_exit_status()
print(stdout.read().decode())

print(f"\n✓ 前端已配置!")
print(f"访问: http://{SERVER}/")

ssh.close()
