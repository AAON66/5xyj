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

print("=== 检查前端构建 ===")
stdin, stdout, stderr = ssh.exec_command("ls -la /opt/execl_mix/frontend/dist/")
stdout.channel.recv_exit_status()
print(stdout.read().decode())

print("\n=== 删除默认配置 ===")
stdin, stdout, stderr = ssh.exec_command("rm -f /etc/nginx/nginx.conf.default /etc/nginx/conf.d/default.conf")
stdout.channel.recv_exit_status()

print("\n=== 重新配置Nginx ===")
stdin, stdout, stderr = ssh.exec_command("""cat > /etc/nginx/conf.d/execl-mix.conf << 'EOF'
server {
    listen 80 default_server;
    server_name _;

    location / {
        root /opt/execl_mix/frontend/dist;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF""")
stdout.channel.recv_exit_status()

print("\n=== 重启Nginx ===")
stdin, stdout, stderr = ssh.exec_command("nginx -t && systemctl restart nginx")
stdout.channel.recv_exit_status()
print(stdout.read().decode())

print(f"\n✓ 完成! 访问: http://{SERVER}/")

ssh.close()
