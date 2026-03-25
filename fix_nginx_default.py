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

print("=== 检查Nginx配置 ===")
stdin, stdout, stderr = ssh.exec_command("grep -n 'default_server' /etc/nginx/nginx.conf")
stdout.channel.recv_exit_status()
print(stdout.read().decode())

print("\n=== 修改主配置 ===")
stdin, stdout, stderr = ssh.exec_command("sed -i 's/listen.*80 default_server/listen 80/g' /etc/nginx/nginx.conf")
stdout.channel.recv_exit_status()

print("\n=== 重启Nginx ===")
stdin, stdout, stderr = ssh.exec_command("systemctl restart nginx && sleep 2")
stdout.channel.recv_exit_status()

print("\n=== 测试 ===")
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost/ | grep -i 'social\\|execl\\|<!DOCTYPE' | head -3")
stdout.channel.recv_exit_status()
result = stdout.read().decode()
print(result)

if 'DOCTYPE' in result and 'nginx' not in result.lower():
    print(f"\n✓ 成功! http://{SERVER}/")
else:
    print("\n查看配置:")
    stdin, stdout, stderr = ssh.exec_command("cat /etc/nginx/conf.d/execl-mix.conf")
    stdout.channel.recv_exit_status()
    print(stdout.read().decode())

ssh.close()
