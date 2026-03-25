#!/usr/bin/env python3
import subprocess
import sys
import os

SERVER = "10.0.0.60"
USER = "root"
PASSWORD = "gQJwgfG9obG57p"
PORT = "22"
PROJECT_DIR = "/opt/execl_mix"

def run_ssh(command):
    """Run SSH command with password"""
    ssh_cmd = f'sshpass -p "{PASSWORD}" ssh -o StrictHostKeyChecking=no -p {PORT} {USER}@{SERVER} "{command}"'
    result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode

def run_rsync():
    """Transfer files"""
    rsync_cmd = f'''sshpass -p "{PASSWORD}" rsync -avz --progress \
        --exclude 'data/' --exclude 'node_modules/' --exclude '__pycache__/' \
        --exclude '.venv/' --exclude '.git/' --exclude '*.pyc' \
        --exclude '.idea/' --exclude 'dist/' --exclude 'build/' \
        --exclude '.claude/' --exclude 'everything-claude-code/' \
        -e "ssh -p {PORT} -o StrictHostKeyChecking=no" \
        ./ {USER}@{SERVER}:{PROJECT_DIR}/'''
    return subprocess.run(rsync_cmd, shell=True).returncode

print("=== Installing sshpass ===")
subprocess.run("pip install sshpass 2>/dev/null || echo 'Using system sshpass'", shell=True)

print("\n=== Step 1: Transferring files ===")
if run_rsync() != 0:
    print("Error: File transfer failed")
    sys.exit(1)

print("\n=== Step 2: Setting up backend ===")
run_ssh("cd /opt/execl_mix && python3 -m venv .venv")
