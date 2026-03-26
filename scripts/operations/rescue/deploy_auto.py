#!/usr/bin/env python3
"""
Automated deployment script for execl_mix project
"""
import paramiko
import os
import sys
from pathlib import Path

SERVER = "10.0.0.60"
USER = "root"
PASSWORD = "gQJwgfG9obG57p"
PORT = 22
PROJECT_DIR = "/opt/execl_mix"

def ssh_exec(ssh, command, description=""):
    if description:
        print(f"\n>>> {description}")
    print(f"$ {command}")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()

    output = stdout.read().decode()
    error = stderr.read().decode()

    if output:
        print(output)
    if error:
        print(error, file=sys.stderr)

    return exit_status == 0

def main():
    print("=== Connecting to server ===")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER, port=PORT, username=USER, password=PASSWORD)
        print(f"✓ Connected to {SERVER}")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        sys.exit(1)

    # Step 1: Create project directory
    ssh_exec(ssh, f"mkdir -p {PROJECT_DIR}", "Creating project directory")

    print("\n=== Step 2: Transferring files ===")
    print("Please run manually:")
    print(f"rsync -avz --exclude 'data/' --exclude 'node_modules/' --exclude '.venv/' \\")
    print(f"  -e 'ssh -p {PORT}' ./ {USER}@{SERVER}:{PROJECT_DIR}/")
    input("\nPress Enter after rsync completes...")
